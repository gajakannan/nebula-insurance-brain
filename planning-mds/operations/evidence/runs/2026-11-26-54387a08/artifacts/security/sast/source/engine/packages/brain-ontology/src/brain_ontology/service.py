"""Authorized ontology release commands (F0012-S0002 AC6, S0004 AC6/AC7, S0006; ADR-0081 D5/D8).

Every command authorizes `ResourceKey(ontology_release, knowledge_base_id)` (G0-5)
through `AuthorizationExecution`, so its effects and the decision audit commit
or roll back together. Each command also appends one `ontology_release_<command>`
audit event carrying the release reference and the typed outcome: inside the
transaction on success, and after the durable denial or failure otherwise (G0-9).
No command parses a document, calls a model or writes a canonical fact.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, TypeVar
from uuid import UUID

from brain_domain.authx import Action, AuthorizationDecision, ResourceKey, ResourceType
from brain_domain.ontology import OntologyReason, OntologyRefused, report_digest
from brain_domain.principal import Principal
from brain_persistence.ontology_releases import (
    InstalledRelease,
    InstallResult,
    OntologyReleaseStore,
    Selection,
    StoredReport,
)
from brain_security.execution import AuthorizationDenied, AuthorizationExecution
from sqlalchemy.exc import IntegrityError

from brain_ontology.impact import ReleaseSnapshot, analyze, assemble

T = TypeVar("T")
Scope = tuple[UUID, UUID]


class ScopeMismatch(Exception):
    """The requested tenant does not own the knowledge base: treated as a denial."""


@dataclass(frozen=True, slots=True)
class CommandOutcome:
    command: str
    outcome: str
    payload: Mapping[str, Any]


def scope_key(scope: Scope) -> ResourceKey:
    return ResourceKey(ResourceType.ONTOLOGY_RELEASE, scope[1])


class OntologyReleaseService:
    def __init__(
        self,
        execution: AuthorizationExecution,
        store: OntologyReleaseStore,
        *,
        commit: Callable[[], Awaitable[None]],
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._execution = execution
        self._store = store
        self._commit = commit
        self._clock = clock or (lambda: datetime.now(UTC))

    # --- shared ---------------------------------------------------------------------

    async def _run(
        self,
        principal: Principal,
        scope: Scope,
        action: Action,
        command: str,
        payload: Mapping[str, Any],
        work: Callable[[AuthorizationDecision], Awaitable[tuple[T, str, Mapping[str, Any]]]],
        trace_id: str,
    ) -> T:
        seen: list[AuthorizationDecision] = []

        async def operation(decisions: Sequence[AuthorizationDecision]) -> T:
            decision = decisions[0]
            seen.append(decision)
            if (
                decision.scope is None
                or (decision.scope.tenant_id, decision.scope.knowledge_base_id) != scope
            ):
                raise ScopeMismatch(str(scope[1]))
            result, outcome, extra = await work(decision)
            await self._store.audit(
                decision,
                command=command,
                outcome=outcome,
                payload={**payload, **extra},
                at=self._clock(),
            )
            return result

        try:
            return await self._execution.mutate(
                principal, [scope_key(scope)], action, trace_id=trace_id, operation=operation
            )
        except AuthorizationDenied as denied:
            await self._after(denied.decision, command, "denied", payload)
            raise
        except ScopeMismatch:
            await self._after(seen[0], command, "denied", payload)
            raise
        except OntologyRefused as refused:
            if seen:
                await self._after(
                    seen[0], command, refused.reason.value, {**payload, "detail": refused.detail}
                )
            raise
        except IntegrityError as conflict:
            # The database backstop (unique selection sequence, guard trigger).
            if seen:
                await self._after(
                    seen[0], command, OntologyReason.SELECTION_CONFLICT.value, payload
                )
            raise OntologyRefused(OntologyReason.SELECTION_CONFLICT, "database guard") from conflict

    async def _after(
        self,
        decision: AuthorizationDecision,
        command: str,
        outcome: str,
        payload: Mapping[str, Any],
    ) -> None:
        """Audit a refused command after the durable decision is committed."""
        await self._store.audit(
            decision, command=command, outcome=outcome, payload=payload, at=self._clock()
        )
        await self._commit()

    # --- install (S0004) ------------------------------------------------------------

    async def install(
        self,
        principal: Principal,
        scope: Scope,
        manifest: Mapping[str, Any],
        normalized: Mapping[str, Any],
        *,
        trace_id: str,
    ) -> InstallResult:
        payload = {
            "release_ref": str(manifest.get("release_ref")),
            "manifest_digest": str(manifest.get("manifest_digest")),
        }

        async def work(
            decision: AuthorizationDecision,
        ) -> tuple[InstallResult, str, Mapping[str, Any]]:
            result = await self._store.install(
                scope, manifest, normalized, actor_id=decision.actor_principal_id, at=self._clock()
            )
            return (
                result,
                result.status,
                {"release_id": str(result.release_id), "terms": result.terms},
            )

        return await self._run(principal, scope, Action.INSTALL, "install", payload, work, trace_id)

    async def install_extension(
        self, principal: Principal, scope: Scope, module: str, *, trace_id: str
    ) -> None:
        """S0002 AC6: tenant extensions have no install path. Authorized or not, the
        request is refused, audited and writes no row."""
        payload = {"module": module, "reason": OntologyReason.TENANT_EXTENSION_UNSUPPORTED.value}

        async def work(decision: AuthorizationDecision) -> tuple[None, str, Mapping[str, Any]]:
            raise OntologyRefused(OntologyReason.TENANT_EXTENSION_UNSUPPORTED, module)

        try:
            await self._run(
                principal, scope, Action.INSTALL, "install-extension", payload, work, trace_id
            )
        except (AuthorizationDenied, ScopeMismatch) as exc:
            raise OntologyRefused(OntologyReason.TENANT_EXTENSION_UNSUPPORTED, module) from exc

    # --- report and review (S0006 AC1-AC4) ---------------------------------------------

    async def _snapshot(self, release: InstalledRelease) -> ReleaseSnapshot:
        return ReleaseSnapshot(
            release_ref=release.release_ref,
            manifest_digest=release.manifest_digest,
            terms=await self._store.terms(release.id),
            constraints=await self._store.constraints(release.id),
            change_records=release.manifest.get("change_records", []),
        )

    async def report(
        self, principal: Principal, scope: Scope, candidate_ref: str, *, trace_id: str
    ) -> StoredReport:
        payload = {"release_ref": candidate_ref}

        async def work(
            decision: AuthorizationDecision,
        ) -> tuple[StoredReport, str, Mapping[str, Any]]:
            candidate = await self._store.release_by_ref(scope, candidate_ref)
            if candidate is None:
                raise OntologyRefused(OntologyReason.RELEASE_NOT_INSTALLED, candidate_ref)
            head = await self._store.head(scope)
            predecessor = await self._store.release_by_id(scope, head.release_id) if head else None
            pred_snapshot = await self._snapshot(predecessor) if predecessor else None
            cand_snapshot = await self._snapshot(candidate)
            analysis = analyze(pred_snapshot, cand_snapshot)
            reach = await self._store.reach(scope, sorted(analysis.predicate_keys))
            report = assemble(scope, pred_snapshot, cand_snapshot, analysis, reach)
            stored = await self._store.save_report(
                scope,
                report,
                candidate_id=candidate.id,
                predecessor_id=predecessor.id if predecessor else None,
                actor_id=decision.actor_principal_id,
                at=self._clock(),
            )
            return stored, "recorded", {"report_id": str(stored.id), "status": stored.status}

        return await self._run(principal, scope, Action.REVIEW, "report", payload, work, trace_id)

    async def review(
        self,
        principal: Principal,
        scope: Scope,
        report_id: UUID,
        decision_value: str,
        rationale: str,
        *,
        trace_id: str,
    ) -> UUID:
        if decision_value not in {"approve", "reject"} or not rationale.strip():
            raise ValueError("a review is approve or reject with a rationale")
        payload = {"report_id": str(report_id), "decision": decision_value}

        async def work(decision: AuthorizationDecision) -> tuple[UUID, str, Mapping[str, Any]]:
            report = await self._store.report(scope, report_id)
            if report is None:
                raise OntologyRefused(OntologyReason.REPORT_NOT_FOUND, str(report_id))
            review_id = await self._store.save_review(
                scope,
                report_id=report_id,
                decision=decision_value,
                rationale=rationale,
                reviewer_id=decision.actor_principal_id,
                decision_id=decision.decision_id,
                at=self._clock(),
            )
            return (
                review_id,
                "recorded",
                {
                    "review_id": str(review_id),
                    "report_digest": report.report_digest,
                    "candidate": report.report["candidate"],
                    "predecessor": report.report["predecessor"],
                },
            )

        return await self._run(principal, scope, Action.REVIEW, "review", payload, work, trace_id)

    # --- activation and rollback (S0006 AC5-AC7) -----------------------------------------

    async def activate(
        self,
        principal: Principal,
        scope: Scope,
        release_ref: str,
        review_id: UUID,
        *,
        trace_id: str,
    ) -> Selection:
        payload = {"release_ref": release_ref, "review_id": str(review_id)}

        async def work(decision: AuthorizationDecision) -> tuple[Selection, str, Mapping[str, Any]]:
            candidate = await self._store.release_by_ref(scope, release_ref)
            if candidate is None:
                raise OntologyRefused(OntologyReason.RELEASE_NOT_INSTALLED, release_ref)
            head = await self._store.head(scope, for_update=True)
            if head is not None and head.release_id == candidate.id:
                raise OntologyRefused(
                    OntologyReason.SELECTION_CONFLICT, "already the selected release"
                )
            review = await self._store.review(scope, review_id)
            report = await self._store.report(scope, review.report_id) if review else None
            if review is None or report is None:
                raise OntologyRefused(OntologyReason.ACTIVATION_REPORT_REQUIRED, str(review_id))
            body = report.report
            predecessor = await self._store.release_by_id(scope, head.release_id) if head else None
            if (
                report_digest(body) != report.report_digest
                or report.candidate_release_id != candidate.id
                or body["candidate"]["manifest_digest"] != candidate.manifest_digest
            ):
                raise OntologyRefused(OntologyReason.REPORT_DIGEST_MISMATCH, "candidate")
            if report.status != "complete" or body["unresolved"]:
                raise OntologyRefused(OntologyReason.REPORT_INCOMPLETE, str(report.id))
            if review.decision != "approve":
                raise OntologyRefused(OntologyReason.REVIEW_REJECTED, str(review.id))
            expected = predecessor.id if predecessor else None
            if report.predecessor_release_id != expected:
                raise OntologyRefused(
                    OntologyReason.PREDECESSOR_MISMATCH, "the selected release changed"
                )
            if (
                predecessor is not None
                and body["predecessor"]["manifest_digest"] != predecessor.manifest_digest
            ):
                raise OntologyRefused(OntologyReason.REPORT_DIGEST_MISMATCH, "predecessor")
            return await self._select(scope, head, "activate", candidate, review.id, decision)

        return await self._run(
            principal, scope, Action.ACTIVATE, "activate", payload, work, trace_id
        )

    async def rollback(
        self, principal: Principal, scope: Scope, release_ref: str, *, trace_id: str
    ) -> Selection:
        payload = {"release_ref": release_ref}

        async def work(decision: AuthorizationDecision) -> tuple[Selection, str, Mapping[str, Any]]:
            target = await self._store.release_by_ref(scope, release_ref)
            if target is None:
                raise OntologyRefused(OntologyReason.RELEASE_NOT_INSTALLED, release_ref)
            head = await self._store.head(scope, for_update=True)
            if not await self._store.was_activated(scope, target.id):
                raise OntologyRefused(OntologyReason.ROLLBACK_TARGET_NEVER_ACTIVE, release_ref)
            if head is not None and head.release_id == target.id:
                raise OntologyRefused(
                    OntologyReason.SELECTION_CONFLICT, "already the selected release"
                )
            return await self._select(scope, head, "rollback", target, None, decision)

        return await self._run(
            principal, scope, Action.ACTIVATE, "rollback", payload, work, trace_id
        )

    async def _select(
        self,
        scope: Scope,
        head: Selection | None,
        action: str,
        release: InstalledRelease,
        review_id: UUID | None,
        decision: AuthorizationDecision,
    ) -> tuple[Selection, str, Mapping[str, Any]]:
        at = self._clock()
        sequence = (head.sequence if head else 0) + 1
        await self._store.append_selection(
            scope,
            sequence=sequence,
            action=action,
            release_id=release.id,
            review_id=review_id,
            actor_id=decision.actor_principal_id,
            decision_id=decision.decision_id,
            at=at,
        )
        selection = Selection(
            sequence,
            action,
            release.release_ref,
            release.id,
            review_id,
            decision.actor_principal_id,
            at,
        )
        return (
            selection,
            "selected",
            {"sequence": sequence, "manifest_digest": release.manifest_digest},
        )

    # --- history ------------------------------------------------------------------------------

    async def history(
        self, principal: Principal, scope: Scope, *, trace_id: str
    ) -> list[Selection]:
        async def load(decision: AuthorizationDecision) -> list[Selection]:
            if (
                decision.scope is None
                or (decision.scope.tenant_id, decision.scope.knowledge_base_id) != scope
            ):
                raise ScopeMismatch(str(scope[1]))
            return await self._store.history(scope)

        return await self._execution.read(
            principal, scope_key(scope), Action.READ, trace_id=trace_id, load=load
        )
