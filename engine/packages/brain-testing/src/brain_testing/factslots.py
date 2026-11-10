"""F0007 test composition: the `test` predicate namespace and slot fixtures.

The `test` namespace is wired only here. Production composition registers only
`sys` (`brain_factslots.predicates.production_registry`). Synthetic development
data, kept outside any frozen evaluation holdout.
"""

from __future__ import annotations

from collections.abc import Iterable
from uuid import UUID, uuid4

from brain_domain.fact_slots import Cardinality, PredicateContract, PredicateKey, QualifierSpec
from brain_domain.fact_values import ValueType
from brain_factslots.predicates import SYSTEM_PREDICATES, StaticPredicateRegistry
from brain_persistence.tenancy import associate_entity, resolve_entity
from sqlalchemy.orm import Session

from brain_testing.fixtures import SYNTHETIC_OPERATOR, seed_scope, utc_now

TEST_RELEASE = "f0007-fixtures/1"
TEST_RELEASE_ALT = "f0007-fixtures/2"


def _key(local: str) -> PredicateKey:
    return PredicateKey("test", local, 1)


LIMIT_AMOUNT = PredicateContract(
    key=_key("hasLimitAmount"),
    release_ref=TEST_RELEASE,
    cardinality=Cardinality.SINGLE,
    value_type=ValueType.MONEY,
    qualifiers=(
        QualifierSpec("basis", ValueType.CODE, required=True),
        QualifierSpec("currency", ValueType.CODE),
        QualifierSpec("threshold", ValueType.DECIMAL),
        QualifierSpec("attachment", ValueType.MONEY),
        QualifierSpec("label", ValueType.TEXT),
        QualifierSpec("location", ValueType.ENTITY_REF),
    ),
    basis_required=True,
)
# Same predicate key, later release, different cardinality: resolving an existing
# slot through it is CARDINALITY_CONFLICT.
LIMIT_AMOUNT_AS_MULTI = PredicateContract(
    key=_key("hasLimitAmount"),
    release_ref=TEST_RELEASE_ALT,
    cardinality=Cardinality.MULTI,
    value_type=ValueType.MONEY,
    qualifiers=LIMIT_AMOUNT.qualifiers,
    member_key_source="value",
    basis_required=True,
)
ADDITIONAL_INSURED = PredicateContract(
    key=_key("hasAdditionalInsured"),
    release_ref=TEST_RELEASE,
    cardinality=Cardinality.MULTI,
    value_type=ValueType.ENTITY_REF,
    member_key_source="entity",
)
POLICY_NUMBER = PredicateContract(
    key=_key("hasPolicyNumber"),
    release_ref=TEST_RELEASE,
    cardinality=Cardinality.MULTI,
    value_type=ValueType.IDENTIFIER,
    member_key_source="value",
)
TAX_ID = PredicateContract(
    key=_key("hasTaxId"),
    release_ref=TEST_RELEASE,
    cardinality=Cardinality.SINGLE,
    value_type=ValueType.IDENTIFIER,
)
RELATED_TO = PredicateContract(
    key=_key("relatedTo"),
    release_ref=TEST_RELEASE,
    cardinality=Cardinality.RELATIONSHIP,
    value_type=ValueType.DECIMAL,
    qualifiers=(QualifierSpec("role", ValueType.CODE),),
)
AGGREGATE_LIMIT = PredicateContract(
    key=_key("hasAggregateLimit"),
    release_ref=TEST_RELEASE,
    cardinality=Cardinality.SINGLE,
    value_type=ValueType.MONEY,
)
EFFECTIVE_DATE = PredicateContract(
    key=_key("hasEffectiveDate"),
    release_ref=TEST_RELEASE,
    cardinality=Cardinality.SINGLE,
    value_type=ValueType.DATE,
)
BAD_CARDINALITY = PredicateContract(
    key=_key("hasBadCardinality"),
    release_ref=TEST_RELEASE,
    cardinality="PAIR",
    value_type=ValueType.TEXT,
)

TEST_PREDICATES: tuple[PredicateContract, ...] = (
    LIMIT_AMOUNT,
    LIMIT_AMOUNT_AS_MULTI,
    ADDITIONAL_INSURED,
    POLICY_NUMBER,
    TAX_ID,
    RELATED_TO,
    AGGREGATE_LIMIT,
    EFFECTIVE_DATE,
    BAD_CARDINALITY,
)


def test_registry(extra: Iterable[PredicateContract] = ()) -> StaticPredicateRegistry:
    """System predicates plus the `test` namespace (test composition only)."""
    return StaticPredicateRegistry((*SYSTEM_PREDICATES, *TEST_PREDICATES, *extra))


test_registry.__test__ = False  # type: ignore[attr-defined]  # not a pytest test


def seed_subject(
    session: Session,
    tenant_id: UUID,
    knowledge_base_ids: Iterable[UUID],
    *,
    external_key: str | None = None,
) -> UUID:
    """A tenant entity associated with each named KB (F0002 trusted services)."""
    entity_id: UUID | None = None
    for knowledge_base_id in knowledge_base_ids:
        seed_scope(session, tenant_id, knowledge_base_id)
        if entity_id is None:
            entity_id = resolve_entity(
                session,
                tenant_id,
                namespace="synthetic-f0007",
                external_key=external_key or uuid4().hex,
                actor_id=SYNTHETIC_OPERATOR,
                at=utc_now(),
            )
        associate_entity(
            session,
            entity_id,
            tenant_id,
            knowledge_base_id,
            actor_id=SYNTHETIC_OPERATOR,
            at=utc_now(),
        )
    if entity_id is None:
        raise ValueError("a subject needs at least one knowledge base")
    return entity_id


def slot_key(
    knowledge_base_id: UUID,
    subject_entity_id: UUID,
    predicate: PredicateContract,
    *,
    qualifiers: dict | None = None,
    **extra: object,
) -> dict:
    """A `fact-slot-key-v1` payload for `predicate`."""
    return {
        "schema_version": 1,
        "knowledge_base_id": str(knowledge_base_id),
        "subject_entity_id": str(subject_entity_id),
        "predicate_key": str(predicate.key),
        "predicate_release_ref": predicate.release_ref,
        "qualifiers": qualifiers or {},
        **extra,
    }
