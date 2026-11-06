"""Deterministic admission of independently decoded, source-grounded candidates.

The caller must supply trusted source ports inside its existing authorized unit
of work. Authorization and infrastructure failures propagate; they are never
misreported as ordinary rejected model items.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import asdict
from datetime import UTC, datetime
from hashlib import sha256
from typing import Any
from uuid import UUID, uuid5

from brain_contracts.assertions import (
    NORMALIZATION_VERSION,
    AdmissionBatch,
    AdmissionMetadata,
    AdmissionOutcome,
    AdmittedAssertion,
    AssertionContractError,
    EntityObjectV2,
    EntityReferenceV2,
    LiteralObjectV2,
    ServerEvidence,
    canonical_json,
    decode_json,
    parse_assertion,
    parse_entity,
    wire_value,
)
from brain_domain.assertions import EntityReference, ProducerContext, VerifiedBlock

from brain_assertions.eligibility import evaluate_eligibility
from brain_assertions.normalization import locate_quote, normalize
from brain_assertions.ports import AdmissionSources


class AssertionAdmissionService:
    def __init__(
        self,
        sources: AdmissionSources,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._sources = sources
        self._clock = clock or (lambda: datetime.now(UTC))

    async def check_items(
        self,
        context: ProducerContext,
        entities: Sequence[EntityReference],
        items: Sequence[bytes],
        *,
        truncated: bool = False,
        uninterpreted_blocks: Sequence[str] = (),
    ) -> AdmissionBatch:
        declarations: dict[UUID, tuple[int, EntityReferenceV2]] = {}
        invalid_entities: set[UUID] = set()
        outcomes: list[AdmissionOutcome] = []
        accepted: list[AdmittedAssertion] = []
        blocks: dict[str, VerifiedBlock] = {}

        def outcome(
            *,
            index: int | None,
            path: str,
            candidate_id: UUID | None,
            block_id: str | None,
            reason: str,
            raw: bytes,
            disposition: str = "REJECTED",
            excerpt: str | None = None,
        ) -> AdmissionOutcome:
            return AdmissionOutcome(
                item_index=index,
                item_path=path,
                candidate_id=candidate_id,
                block_id=block_id,
                disposition=disposition,
                reason=reason,
                raw_item_sha256=sha256(raw).hexdigest(),
                excerpt=excerpt,
                model_id=context.model_id,
                prompt_hash=context.prompt_hash,
            )

        for index, entity in enumerate(entities):
            try:
                declaration = parse_entity(entity)
                if declaration.id in declarations:
                    invalid_entities.add(declaration.id)
                    raise AssertionContractError()
                declarations[declaration.id] = (index, declaration)
            except (AssertionContractError, TypeError):
                try:
                    raw = canonical_json(entity)
                except AssertionContractError:
                    raw = b"null"
                outcomes.append(
                    outcome(
                        index=index,
                        path=f"/entities/{index}",
                        candidate_id=None,
                        block_id=None,
                        reason="MALFORMED_ITEM",
                        raw=raw,
                    )
                )

        async def block(block_id: str) -> VerifiedBlock:
            if block_id not in blocks:
                stored = await self._sources.block(context, block_id)
                # Check identities before inspecting protected source text.
                if stored.artifact_id != context.artifact_id or stored.block_id != block_id:
                    raise LookupError("source identity mismatch")
                blocks[block_id] = stored
            return blocks[block_id]

        for index, raw in enumerate(items):
            path = f"/assertions/{index}"
            try:
                candidate = parse_assertion(raw)
            except (AssertionContractError, TypeError):
                candidate_id = None
                block_id = None
                try:
                    partial = decode_json(raw)
                    candidate_id = UUID(partial["id"])
                    supplied = partial.get("evidence", [])
                    if supplied and isinstance(supplied[0].get("block_id"), str):
                        block_id = supplied[0]["block_id"] or None
                except (ValueError, TypeError, KeyError, AttributeError, IndexError):
                    pass
                outcomes.append(
                    outcome(
                        index=index,
                        path=path,
                        candidate_id=candidate_id,
                        block_id=block_id,
                        reason="MALFORMED_ITEM",
                        raw=raw,
                    )
                )
                continue

            item_outcomes: list[AdmissionOutcome] = []
            evidence: list[ServerEvidence] = []
            source_hashes: dict[str, str] = {}
            time_snapshots: list[dict[str, Any]] = []
            selected: dict[UUID, EntityReferenceV2] = {}

            def fail(
                reason: str,
                *,
                block_id: str | None = None,
                item_path: str = path,
                item_index: int = index,
                identifier: UUID = candidate.id,
                item_raw: bytes = raw,
                failures: list[AdmissionOutcome] = item_outcomes,
            ) -> None:
                entry = outcome(
                    index=item_index,
                    path=item_path,
                    candidate_id=identifier,
                    block_id=block_id,
                    reason=reason,
                    raw=item_raw,
                    excerpt=item_raw.decode("utf-8", errors="replace")[:256],
                )
                if not any(
                    (e.reason, e.item_path, e.block_id)
                    == (entry.reason, entry.item_path, entry.block_id)
                    for e in failures
                ):
                    failures.append(entry)

            if candidate.origin != context.origin:
                fail("MALFORMED_ITEM")
            required_refs = [candidate.subject_ref]
            if (
                isinstance(candidate.object, EntityObjectV2)
                and candidate.object.ref in declarations
            ):
                required_refs.append(candidate.object.ref)
            for ref in dict.fromkeys(required_refs):
                if ref not in declarations or ref in invalid_entities:
                    fail("UNKNOWN_REFERENCE")
                    continue
                entity_index, entity = declarations[ref]
                selected[ref] = entity
                entity_path = f"/entities/{entity_index}"
                for claim_index, claim in enumerate(entity.introducing_evidence):
                    location_path = f"{entity_path}/introducing_evidence/{claim_index}"
                    if not normalize(entity.label) or normalize(entity.label) not in normalize(
                        claim.quote
                    ):
                        fail("NAME_NOT_IN_QUOTE", block_id=claim.block_id, item_path=location_path)
                    if claim.artifact_id != context.artifact_id:
                        fail("UNKNOWN_REFERENCE", block_id=claim.block_id, item_path=location_path)
                        continue
                    try:
                        original = await block(claim.block_id)
                    except LookupError:
                        fail("UNKNOWN_REFERENCE", block_id=claim.block_id, item_path=location_path)
                        continue
                    if locate_quote(original.text, claim.quote, original.native_selector) is None:
                        fail(
                            "QUOTE_NOT_IN_SOURCE", block_id=claim.block_id, item_path=location_path
                        )
                    source_hashes[claim.block_id] = sha256(
                        original.text.encode("utf-8")
                    ).hexdigest()

            if isinstance(candidate.object, EntityObjectV2):
                obj = candidate.object
                if obj.ref in declarations and obj.ref not in invalid_entities:
                    declared = declarations[obj.ref][1]
                    if normalize(obj.name) != normalize(declared.label):
                        fail("NAME_NOT_IN_QUOTE", item_path=path + "/object")
                if not any(
                    normalize(obj.name) in normalize(claim.quote) for claim in candidate.evidence
                ):
                    fail("NAME_NOT_IN_QUOTE", item_path=path + "/object")
                if obj.ref not in declarations:
                    item_outcomes.append(
                        outcome(
                            index=index,
                            path=path + "/object",
                            candidate_id=candidate.id,
                            block_id=candidate.evidence[0].block_id,
                            disposition="SIGNAL",
                            reason="OBJECT_UNDECLARED",
                            raw=raw,
                            excerpt=obj.name,
                        )
                    )
                    candidate = candidate.model_copy(
                        update={"object": LiteralObjectV2(kind="LITERAL", value=obj.name)}
                    )

            for ordinal, claim in enumerate(candidate.evidence):
                evidence_path = f"{path}/evidence/{ordinal}"
                if claim.artifact_id != context.artifact_id:
                    fail("UNKNOWN_REFERENCE", block_id=claim.block_id, item_path=evidence_path)
                    continue
                try:
                    original = await block(claim.block_id)
                except LookupError:
                    fail("UNKNOWN_REFERENCE", block_id=claim.block_id, item_path=evidence_path)
                    continue
                location = locate_quote(original.text, claim.quote, original.native_selector)
                if location is None:
                    fail("QUOTE_NOT_IN_SOURCE", block_id=claim.block_id, item_path=evidence_path)
                    continue
                evidence.append(
                    ServerEvidence(
                        evidence_id=uuid5(candidate.id, str(ordinal)),
                        artifact_id=original.artifact_id,
                        block_id=original.block_id,
                        quote=claim.quote,
                        normalization_version=NORMALIZATION_VERSION,
                        precision=location.precision,
                        selector=location.selector,
                        text_origin=original.text_origin,
                        origin_qualification=original.origin_qualification,
                        producer=dict(original.producer) if original.producer is not None else None,
                        producer_confidence=original.producer_confidence,
                    )
                )
                source_hashes[claim.block_id] = sha256(original.text.encode("utf-8")).hexdigest()

            for ordinal, ref in enumerate(candidate.time_mention_refs):
                ref_path = f"{path}/time_mention_refs/{ordinal}"
                try:
                    time_ref = await self._sources.time_reference(context, ref)
                    if (
                        time_ref.id != ref
                        or time_ref.tenant_id != context.tenant_id
                        or time_ref.knowledge_base_id != context.knowledge_base_id
                        or time_ref.artifact_id != context.artifact_id
                    ):
                        raise LookupError("time reference identity mismatch")
                except LookupError:
                    fail("UNKNOWN_REFERENCE", item_path=ref_path)
                    continue
                if not normalize(time_ref.words) or not any(
                    claim.block_id == time_ref.block_id
                    and normalize(time_ref.words) in normalize(claim.quote)
                    for claim in candidate.evidence
                ):
                    fail("TIME_NOT_IN_QUOTE", block_id=time_ref.block_id, item_path=ref_path)
                time_snapshots.append(wire_value(asdict(time_ref)))

            outcomes.extend(item_outcomes)
            if any(e.disposition == "REJECTED" for e in item_outcomes):
                continue
            eligibility = evaluate_eligibility(candidate, evidence)
            accepted.append(
                AdmittedAssertion(
                    record=candidate,
                    server_evidence=tuple(evidence),
                    review_required=eligibility.review_required,
                    reasons=eligibility.reasons,
                    blocked_operations=eligibility.blocked_operations,
                    created_by=context.actor_id,
                    created_at=self._clock(),
                ).with_metadata(
                    AdmissionMetadata(
                        raw_item_sha256=sha256(raw).hexdigest(),
                        item_index=index,
                        entity_snapshots=tuple(
                            entity.model_dump(mode="json") for entity in selected.values()
                        ),
                        time_reference_snapshot=tuple(time_snapshots),
                        source_hashes=source_hashes,
                    )
                )
            )

        if truncated:
            outcomes.append(
                outcome(
                    index=None,
                    path="/output",
                    candidate_id=None,
                    block_id=None,
                    disposition="RUN_ISSUE",
                    reason="TRUNCATED_OUTPUT",
                    raw=b"",
                )
            )
        for block_id in dict.fromkeys(uninterpreted_blocks):
            outcomes.append(
                outcome(
                    index=None,
                    path="/blocks/" + block_id,
                    candidate_id=None,
                    block_id=block_id,
                    disposition="RUN_ISSUE",
                    reason="BLOCK_UNINTERPRETED",
                    raw=b"",
                )
            )
        return AdmissionBatch(
            schema_version=1,
            run_id=context.run_id,
            artifact_id=context.artifact_id,
            accepted=tuple(accepted),
            outcomes=tuple(outcomes),
            requires_partial=bool(truncated or uninterpreted_blocks),
        )
