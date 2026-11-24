from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol
from uuid import UUID, uuid4

from brain_contracts.schema_runtime import ContractRef, validate_contract
from brain_domain.assertions import SourceAccessProof
from brain_domain.facts import ChangeReason, CommitProposal, CommitResult, FactVersion
from brain_domain.temporal import (
    UNANCHORED_BASES,
    Bound,
    DocumentDate,
    EndState,
    TemporalKind,
    TemporalReason,
    TemporalRejected,
    VersionTemporal,
)

from brain_temporal.attestation import (
    Attestation,
    Placement,
    check_expected,
    derive_attestation,
    ordered_refs,
    place,
)
from brain_temporal.bounds import parse_commit_temporal
from brain_temporal.ranges import TimeRange, split_remainder


class FactSlotNotFound(Exception):
    pass


DisclosureCheck = Callable[[tuple[FactVersion, ...]], Awaitable[None]]
"""Verifies, before any effect, that the caller may read the attesting documents of
predecessors whose dates the commit response will return (SEC-F8-NEW-01). It raises
to refuse the commit."""


def returns_attestation(temporal: VersionTemporal | None) -> bool:
    return temporal is not None and any(
        (temporal.attested_from, temporal.attested_through, temporal.attested_to)
    )


class StaleVersionError(Exception):
    """`expected_current_version_id` no longer matches the slot's current
    version(s) — the optimistic half of F0001-S0005's concurrency proof."""


class LegacyTemporalUnsupported(Exception):
    """A `fact-temporal/v1` block was sent to a legacy pilot slot, which keeps
    the pilot request shape (ADR-0078 D1). The API maps this to a 400."""


class CommitAnswerPolicy(Protocol):
    """F0007 hook (ADR-0077 D5). Returns the canonical value to store for an
    identity-v1 slot, or `None` for a legacy pilot slot, whose value is used
    unchanged. Raises `brain_domain.fact_answers.FactAnswerRejected` to refuse the
    commit before any effect."""

    async def canonical_value(
        self,
        slot_id: UUID,
        value: Mapping[str, Any],
        *,
        authorized_scope: tuple[UUID, UUID],
    ) -> Mapping[str, Any] | None: ...


class FactCommitRepository(Protocol):
    async def require_commit_sources(
        self,
        *,
        evidence_refs: tuple[UUID, ...],
        review_decision_id: UUID | None,
        authorized_scope: tuple[UUID, UUID],
        closes_existing: bool,
        source_access: SourceAccessProof | None,
    ) -> None:
        """Refuse ineligible or unauthorized attributable sources before effects."""
        ...

    async def lock_slot(self, slot_id: UUID) -> tuple[UUID, UUID] | None:
        """`SELECT ... FOR UPDATE` the slot; returns `(tenant_id, knowledge_base_id)`,
        or `None` if the slot does not exist. Serializes concurrent commits on the
        same slot (F0001-S0005 logic flow step 2)."""
        ...

    async def slot_identity_version(self, slot_id: UUID) -> int | None:
        """F0007 `identity_version` of the slot: 1, or None for a legacy pilot slot.
        F0008 binds the temporal contract to it (ADR-0078 D1)."""
        ...

    async def evidence_document_dates(
        self, refs: tuple[UUID, ...], *, authorized_scope: tuple[UUID, UUID]
    ) -> Mapping[UUID, DocumentDate | None]:
        """For each evidence ref, the current F0004 date selection of its document
        version, or None when that document is undated (ADR-0078 D4)."""
        ...

    async def current_versions(self, slot_id: UUID) -> tuple[FactVersion, ...]:
        """Rows with `recorded.end IS NULL` — the currently-visible versions."""
        ...

    async def close_recorded(self, version_id: UUID, at: datetime) -> None: ...

    async def insert_version(
        self,
        *,
        version_id: UUID,
        slot_id: UUID,
        tenant_id: UUID,
        knowledge_base_id: UUID,
        value: dict,
        valid: TimeRange,
        recorded: TimeRange,
        change_reason: ChangeReason | None,
        evidence_refs: tuple[UUID, ...],
        review_decision_id: UUID | None,
        commit_id: UUID,
        source_received_at: datetime,
        artifact_created_at: datetime,
        assertion_created_at: datetime,
        canonical_accepted_at: datetime,
        temporal: VersionTemporal | None = None,
        split_of_version_id: UUID | None = None,
        ending_evidence_refs: tuple[UUID, ...] = (),
    ) -> None: ...

    async def insert_change(
        self,
        *,
        reason: ChangeReason,
        from_version_id: UUID | None,
        to_version_id: UUID,
        tenant_id: UUID,
        knowledge_base_id: UUID,
    ) -> None: ...

    async def register_commit(
        self,
        *,
        commit_id: UUID,
        tenant_id: UUID,
        knowledge_base_id: UUID,
        authorization_decision_id: UUID | None,
        at: datetime,
    ) -> None: ...

    async def write_outbox(self, commit_id: UUID, payload: dict) -> None: ...


def _range(version: FactVersion) -> TimeRange:
    return TimeRange(version.valid_start, version.valid_end)


def _state(value: Mapping[str, Any]) -> str | None:
    state = value.get("state")
    return state if isinstance(state, str) else None


def _same_answer(a: Mapping[str, Any], b: Mapping[str, Any]) -> bool:
    return dict(a) == dict(b)


@dataclass(frozen=True, slots=True)
class _Write:
    """One planned remainder row."""

    valid: TimeRange
    temporal: VersionTemporal | None


class CanonicalCommitService:
    """Master blueprint section 109.2, one transaction (F0001-S0005, F0008).

    F0002: authorization is not performed here. The caller runs `commit` as the
    operation of `AuthorizationExecution.mutate`, which has already locked current
    authority and the slot's security metadata inside the same unit of work. The
    fact rows, `canonical_fact_change`, the commit ownership row, `outbox_event`
    and the durable authorization decision then commit or roll back together.
    This service never commits the transaction itself. It still re-checks that
    the slot it locks belongs to the scope that was authorized (defense in depth).

    F0008: an identity-v1 slot takes the `fact-temporal/v1` path (ADR-0078). A
    legacy pilot slot keeps the pilot path, with the remainder fix that S0003 AC3
    requires."""

    def __init__(
        self,
        repository: FactCommitRepository,
        *,
        clock: Callable[[], datetime] | None = None,
        answer_policy: CommitAnswerPolicy | None = None,
    ) -> None:
        self._repository = repository
        self._clock = clock or (lambda: datetime.now(UTC))
        self._answer_policy = answer_policy

    async def commit(
        self,
        proposal: CommitProposal,
        *,
        authorized_scope: tuple[UUID, UUID],
        authorization_decision_id: UUID | None,
        source_access: SourceAccessProof | None = None,
        disclosure_check: DisclosureCheck | None = None,
    ) -> CommitResult:
        locked = await self._repository.lock_slot(proposal.slot_id)
        if locked is None or locked != authorized_scope:
            raise FactSlotNotFound(str(proposal.slot_id))
        identity = await self._repository.slot_identity_version(proposal.slot_id)
        if identity is None:
            return await self._commit_legacy(
                proposal,
                scope=locked,
                authorization_decision_id=authorization_decision_id,
                source_access=source_access,
            )
        return await self._commit_v1(
            proposal,
            scope=locked,
            authorization_decision_id=authorization_decision_id,
            source_access=source_access,
            disclosure_check=disclosure_check,
        )

    # --- shared helpers --------------------------------------------------

    async def _canonical_value(
        self, proposal: CommitProposal, scope: tuple[UUID, UUID]
    ) -> Mapping[str, Any]:
        # F0007: identity-v1 slots store the canonical fact-answer/v1 envelope. The
        # policy runs after the lock and before any source check or effect.
        if self._answer_policy is None:
            return proposal.value
        canonical = await self._answer_policy.canonical_value(
            proposal.slot_id, proposal.value, authorized_scope=scope
        )
        return canonical if canonical is not None else proposal.value

    async def _current(self, proposal: CommitProposal) -> tuple[FactVersion, ...]:
        current = await self._repository.current_versions(proposal.slot_id)
        expected = proposal.expected_current_version_id
        if expected is not None and expected not in {v.id for v in current}:
            raise StaleVersionError(str(expected))
        return current

    async def _remainder(
        self,
        *,
        predecessor: FactVersion,
        piece: _Write,
        proposal: CommitProposal,
        scope: tuple[UUID, UUID],
        commit_id: UUID,
        now: datetime,
        lineage: bool,
    ) -> UUID:
        """S0003 AC3: a remainder keeps its predecessor's value, evidence, review
        linkage and three source timestamps (`source_received_at`,
        `artifact_created_at`, `assertion_created_at`). Its valid cut and its
        `canonical_accepted_at`, where its recorded interval starts, are new.
        Pilot rows written before F0008 have no stored timestamps on the domain
        object, so the proposal's values are the fallback for those alone."""
        remainder_id = uuid4()
        if piece.temporal is not None:
            # Only newly constructed temporal carriers are guarded. A historical
            # legacy remainder keeps its unwrapped value and absent metadata.
            validate_contract(
                ContractRef("fact-temporal-v1", "1", "/$defs/version_temporal"),
                piece.temporal.to_json(),
                profile="native-compat/v1",
            )
        await self._repository.insert_version(
            version_id=remainder_id,
            slot_id=proposal.slot_id,
            tenant_id=scope[0],
            knowledge_base_id=scope[1],
            value=dict(predecessor.value),
            valid=piece.valid,
            recorded=TimeRange(now, None),
            change_reason=ChangeReason.SPLIT,
            evidence_refs=predecessor.evidence_refs,
            review_decision_id=predecessor.review_decision_id,
            commit_id=commit_id,
            source_received_at=predecessor.source_received_at or proposal.source_received_at,
            artifact_created_at=predecessor.artifact_created_at or proposal.artifact_created_at,
            assertion_created_at=predecessor.assertion_created_at or proposal.assertion_created_at,
            canonical_accepted_at=now,
            temporal=piece.temporal,
            split_of_version_id=predecessor.id if lineage else None,
            ending_evidence_refs=predecessor.ending_evidence_refs,
        )
        return remainder_id

    async def _finish(
        self,
        *,
        proposal: CommitProposal,
        scope: tuple[UUID, UUID],
        commit_id: UUID,
        new_version_id: UUID,
        superseded: list[UUID],
        version_ids: list[UUID],
        now: datetime,
        temporals: dict[UUID, VersionTemporal | None] | None = None,
    ) -> CommitResult:
        reason = proposal.change_reason or ChangeReason.SUPERSEDED
        sources: list[UUID | None] = list(superseded) or [None]
        for from_id in sources:
            await self._repository.insert_change(
                reason=reason,
                from_version_id=from_id,
                to_version_id=new_version_id,
                tenant_id=scope[0],
                knowledge_base_id=scope[1],
            )
        await self._repository.write_outbox(
            commit_id,
            {
                "commit_id": str(commit_id),
                "slot_id": str(proposal.slot_id),
                "fact_version_ids": [str(v) for v in version_ids],
            },
        )
        return CommitResult(
            commit_id=commit_id,
            fact_version_ids=tuple(version_ids),
            canonical_accepted_at=now,
            version_temporals=(
                tuple((v, temporals.get(v)) for v in version_ids) if temporals is not None else ()
            ),
        )

    # --- legacy pilot path ------------------------------------------------

    async def _commit_legacy(
        self,
        proposal: CommitProposal,
        *,
        scope: tuple[UUID, UUID],
        authorization_decision_id: UUID | None,
        source_access: SourceAccessProof | None,
    ) -> CommitResult:
        if proposal.temporal is not None:
            raise LegacyTemporalUnsupported(str(proposal.slot_id))
        if proposal.valid_from is None:
            raise TemporalRejected(TemporalReason.TEMPORAL_FIELDS_REQUIRED)
        # TimeRange.__post_init__ rejects an empty/inverted range (F0001-S0005 AC).
        new_valid = TimeRange(proposal.valid_from, proposal.valid_to)
        value = await self._canonical_value(proposal, scope)
        current = await self._current(proposal)
        await self._repository.require_commit_sources(
            evidence_refs=proposal.evidence_refs,
            review_decision_id=proposal.review_decision_id,
            authorized_scope=scope,
            closes_existing=any(_range(v).overlaps(new_valid) for v in current),
            source_access=source_access,
        )

        now = self._clock()
        commit_id = uuid4()
        await self._repository.register_commit(
            commit_id=commit_id,
            tenant_id=scope[0],
            knowledge_base_id=scope[1],
            authorization_decision_id=authorization_decision_id,
            at=now,
        )
        version_ids: list[UUID] = []
        superseded: list[UUID] = []
        for existing in current:
            existing_valid = _range(existing)
            if not existing_valid.overlaps(new_valid):
                continue
            await self._repository.close_recorded(existing.id, now)
            superseded.append(existing.id)
            for piece in split_remainder(existing_valid, new_valid):
                version_ids.append(
                    await self._remainder(
                        predecessor=existing,
                        piece=_Write(piece, None),
                        proposal=proposal,
                        scope=scope,
                        commit_id=commit_id,
                        now=now,
                        lineage=False,
                    )
                )

        new_version_id = uuid4()
        await self._repository.insert_version(
            version_id=new_version_id,
            slot_id=proposal.slot_id,
            tenant_id=scope[0],
            knowledge_base_id=scope[1],
            value=dict(value),
            valid=new_valid,
            recorded=TimeRange(now, None),
            change_reason=proposal.change_reason,
            evidence_refs=proposal.evidence_refs,
            review_decision_id=proposal.review_decision_id,
            commit_id=commit_id,
            source_received_at=proposal.source_received_at,
            artifact_created_at=proposal.artifact_created_at,
            assertion_created_at=proposal.assertion_created_at,
            canonical_accepted_at=now,
        )
        version_ids.append(new_version_id)
        return await self._finish(
            proposal=proposal,
            scope=scope,
            commit_id=commit_id,
            new_version_id=new_version_id,
            superseded=superseded,
            version_ids=version_ids,
            now=now,
        )

    # --- fact-temporal/v1 path (ADR-0078) -------------------------------------

    async def _commit_v1(
        self,
        proposal: CommitProposal,
        *,
        scope: tuple[UUID, UUID],
        authorization_decision_id: UUID | None,
        source_access: SourceAccessProof | None,
        disclosure_check: DisclosureCheck | None = None,
    ) -> CommitResult:
        # Step 2: contract checks. A pilot-shaped request is refused (S0007 AC3).
        if proposal.temporal is None or proposal.valid_from is not None:
            raise TemporalRejected(TemporalReason.TEMPORAL_FIELDS_REQUIRED)
        value = await self._canonical_value(proposal, scope)
        # Step 3: parse and validate bounds (S0001, S0002 AC1, S0005 AC1).
        temporal = parse_commit_temporal(proposal.temporal)

        # Steps 5-7 are computed before the source check so that `closes_existing`
        # is exact, but a refusal is raised only after it: an ineligible source is
        # reported before any temporal reason.
        refs = ordered_refs(proposal.evidence_refs, temporal.ending_evidence_refs)
        dates = await self._repository.evidence_document_dates(refs, authorized_scope=scope)
        attestation = derive_attestation(
            (dates.get(r) for r in proposal.evidence_refs),
            (dates.get(r) for r in temporal.ending_evidence_refs),
        )
        placement: Placement | None
        pending: TemporalRejected | None = None
        try:
            check_expected(temporal, attestation)
            placement = place(temporal, attestation)
        except TemporalRejected as refused:
            placement, pending = None, refused

        # Step 8: current versions and the optimistic check.
        current = await self._current(proposal)
        new_valid = (
            TimeRange(placement.start.instant, placement.end.instant if placement.end else None)
            if placement is not None
            else None
        )
        overlapping = [v for v in current if new_valid is None or _range(v).overlaps(new_valid)]
        # Step 4: the existing same-UoW source READ and eligibility check.
        await self._repository.require_commit_sources(
            evidence_refs=refs,
            review_decision_id=proposal.review_decision_id,
            authorized_scope=scope,
            closes_existing=bool(overlapping),
            source_access=source_access,
        )
        if pending is not None:
            raise pending
        assert placement is not None and new_valid is not None

        # Step 9: guards (D8). A refusal writes no row.
        end_revision = self._guard(value, placement, attestation, overlapping)

        # SEC-F8-NEW-01: a remainder repeats its predecessor's attestation dates, and
        # the response returns them. The caller must be able to read the documents
        # behind those dates; the check runs before any effect.
        if disclosure_check is not None and not end_revision:
            disclosed = tuple(
                existing
                for existing in overlapping
                if returns_attestation(existing.temporal)
                and self._remainders(existing, new_valid, placement)
            )
            if disclosed:
                await disclosure_check(disclosed)

        new_temporal = VersionTemporal(
            kind=TemporalKind.STATE,
            valid_from=placement.start,
            valid_from_basis=placement.basis,
            valid_to_state=placement.end_state,
            valid_to=placement.end,
            attested_from=attestation.attested_from,
            attested_through=attestation.attested_through,
            attested_to=attestation.attested_to
            if placement.end_state is not EndState.BOUNDED
            else None,
            validity_unknown_from=placement.validity_unknown_from,
            split_of_version_id=None,
        )
        validate_contract(
            ContractRef("fact-temporal-v1", "1", "/$defs/version_temporal"),
            new_temporal.to_json(),
            profile="native-compat/v1",
        )

        # Step 10: write.
        now = self._clock()
        commit_id = uuid4()
        await self._repository.register_commit(
            commit_id=commit_id,
            tenant_id=scope[0],
            knowledge_base_id=scope[1],
            authorization_decision_id=authorization_decision_id,
            at=now,
        )
        version_ids: list[UUID] = []
        superseded: list[UUID] = []
        remainder_links: list[tuple[UUID, UUID]] = []
        temporals: dict[UUID, VersionTemporal | None] = {}
        for existing in overlapping:
            await self._repository.close_recorded(existing.id, now)
            superseded.append(existing.id)
            # An end revision replaces its version whole: the same fact with a new
            # end leaves nothing of the old one behind (EX-PC-014).
            pieces = [] if end_revision else self._remainders(existing, new_valid, placement)
            for piece in pieces:
                remainder_id = await self._remainder(
                    predecessor=existing,
                    piece=piece,
                    proposal=proposal,
                    scope=scope,
                    commit_id=commit_id,
                    now=now,
                    lineage=True,
                )
                version_ids.append(remainder_id)
                temporals[remainder_id] = piece.temporal
                remainder_links.append((existing.id, remainder_id))

        new_version_id = uuid4()
        await self._repository.insert_version(
            version_id=new_version_id,
            slot_id=proposal.slot_id,
            tenant_id=scope[0],
            knowledge_base_id=scope[1],
            value=dict(value),
            valid=new_valid,
            recorded=TimeRange(now, None),
            change_reason=proposal.change_reason,
            evidence_refs=proposal.evidence_refs,
            review_decision_id=proposal.review_decision_id,
            commit_id=commit_id,
            source_received_at=proposal.source_received_at,
            artifact_created_at=proposal.artifact_created_at,
            assertion_created_at=proposal.assertion_created_at,
            canonical_accepted_at=now,
            temporal=new_temporal,
            ending_evidence_refs=temporal.ending_evidence_refs,
        )
        version_ids.append(new_version_id)
        temporals[new_version_id] = new_temporal
        for from_id, to_id in remainder_links:
            await self._repository.insert_change(
                reason=ChangeReason.SPLIT,
                from_version_id=from_id,
                to_version_id=to_id,
                tenant_id=scope[0],
                knowledge_base_id=scope[1],
            )
        return await self._finish(
            proposal=proposal,
            scope=scope,
            commit_id=commit_id,
            new_version_id=new_version_id,
            superseded=superseded,
            version_ids=version_ids,
            now=now,
            temporals=temporals,
        )

    @staticmethod
    def _is_end_revision(
        value: Mapping[str, Any],
        placement: Placement,
        attestation: Attestation,
        predecessor: FactVersion,
    ) -> bool:
        """ADR-0078 D8: same answer, start bound, basis and `attested_from`; only
        the end differs. A legacy predecessor has no stored start bound, so a
        proposal against it is always a succession."""
        before = predecessor.temporal
        return (
            before is not None
            and _same_answer(value, predecessor.value)
            and before.valid_from == placement.start
            and before.valid_from_basis == placement.basis
            and before.attested_from == attestation.attested_from
        )

    def _guard(
        self,
        value: Mapping[str, Any],
        placement: Placement,
        attestation: Attestation,
        overlapping: list[FactVersion],
    ) -> bool:
        """Apply the D8 guards and return whether the proposal is an end revision."""
        if not overlapping:
            return False
        end_revision = len(overlapping) == 1 and self._is_end_revision(
            value, placement, attestation, overlapping[0]
        )
        if not end_revision and placement.basis in UNANCHORED_BASES:
            raise TemporalRejected(TemporalReason.SUCCESSION_START_UNANCHORED)
        successor_state = _state(value)
        for predecessor in overlapping:
            if _state(predecessor.value) == "PRESENT" and successor_state not in {
                "PRESENT",
                "EXPLICIT_NEGATIVE",
            }:
                raise TemporalRejected(TemporalReason.STATE_SUPERSESSION_REFUSED)
        return end_revision

    @staticmethod
    def _remainders(
        predecessor: FactVersion, new_valid: TimeRange, placement: Placement
    ) -> list[_Write]:
        """ADR-0078 D5 remainders. A legacy predecessor keeps legacy remainders
        (plain ranges). A temporal-v1 predecessor's remainders copy its kind,
        basis and attestation; each cut bound comes from the successor.

        Only a BOUNDED successor leaves a remainder after it. The finite upper
        bound of an UNKNOWN successor is an integrity bound, not a stated end, so
        the predecessor does not resume after it."""
        old = _range(predecessor)
        before = predecessor.temporal
        pieces = [
            piece
            for piece in split_remainder(old, new_valid)
            if piece.start == old.start or placement.end_state is EndState.BOUNDED
        ]
        if before is None:
            return [_Write(piece, None) for piece in pieces]
        writes: list[_Write] = []
        for piece in pieces:
            if piece.start == old.start:
                # Left remainder: it ends where the successor starts.
                temporal = VersionTemporal(
                    kind=before.kind,
                    valid_from=before.valid_from,
                    valid_from_basis=before.valid_from_basis,
                    valid_to_state=EndState.BOUNDED,
                    valid_to=placement.start,
                    attested_from=before.attested_from,
                    attested_through=before.attested_through,
                    attested_to=None,
                    validity_unknown_from=None,
                    split_of_version_id=predecessor.id,
                )
            else:
                # Right remainder: it starts where a BOUNDED successor ends and
                # keeps the predecessor's end state and attestation.
                assert placement.end is not None
                start: Bound = placement.end
                unknown_from = before.validity_unknown_from
                if unknown_from is not None:
                    unknown_from = max(unknown_from, start.instant)
                temporal = VersionTemporal(
                    kind=before.kind,
                    valid_from=start,
                    valid_from_basis=before.valid_from_basis,
                    valid_to_state=before.valid_to_state,
                    valid_to=before.valid_to,
                    attested_from=before.attested_from,
                    attested_through=before.attested_through,
                    attested_to=before.attested_to,
                    validity_unknown_from=unknown_from,
                    split_of_version_id=predecessor.id,
                )
            writes.append(_Write(piece, temporal))
        return writes
