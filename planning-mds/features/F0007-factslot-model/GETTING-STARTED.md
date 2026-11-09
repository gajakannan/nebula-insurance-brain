# F0007 — Getting started

**State:** Planned. Phase A and Phase B were approved on 2026-11-09 in plan run `2026-11-09-60865e32`. Implementation has not started.

Read these in order:

1. [PRD.md](PRD.md)
2. [personas.md](personas.md)
3. the six story files
4. [acceptance-criteria-checklist.md](acceptance-criteria-checklist.md)
5. [STATUS.md](STATUS.md)
6. the [assembly plan](feature-assembly-plan.md)
7. [ADR-0077](../../architecture/decisions/ADR-0077-factslot-identity-and-typed-answer-carriers.md)
8. the [worked examples](worked-examples.md)

The bound product root is `/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain`. Framework commands run from `nebula-agents` and always receive that absolute root.

## Before implementation (feature action G0)

- Confirm the Alembic head is still `0011`. If not, renumber `0012_f0007_factslot_identity.py` and reconcile its lineage.
- Capture `engine/tests/fixtures/factslots/pilot-before.json` before running any migration. It records slot/version/evidence rows and the schema hash.
- The `test:` predicate namespace exists only in test composition. Production composition registers only `sys:` until F0012/F0013 land. An unregistered key is `PREDICATE_UNREGISTERED` by design, not a bug.

## Gotchas

- **The fingerprint is not the identity.** Always compare the stored qualifier rows on conflict. Never treat a matching hash as proof of equality, and never merge slots on a collision.
- **Release reference is not identity.** Recording a new `predicate_release_ref` on resolution of an existing slot must not create a new slot or update the old one, because identity columns are immutable by trigger.
- **Members are slots.** Commit to the member slot ID, never to the MULTI header. This keeps the ADR-0008 exclusion per member without touching `canonical_fact_version`, which F0008 owns.
- **Legacy rows stay legacy.** A NULL `identity_version` marks a pilot slot. Do not backfill predicate keys or qualifiers. Any later mapping must be explicit and reversible (F0012/F0013).
- **Authorization comes first.** Run the resolver as the `operation` of `AuthorizationExecution.mutate` over the source artifacts with `INTERPRET`. Add the scope artifact and name-evidence source to `commit_source_keys` so denial precedes any reason code.
- **Money amounts are strings.** Pydantic must not coerce a JSON number into a decimal string. Reject it (`MONEY_FLOAT_REJECTED`) before any model conversion.
- **`subject_kb_entity_id` is a generated column.** Never write it. It exists so the subject-KB foreign key ignores legacy rows (MATCH SIMPLE).

## RLS inventory handed to F0018

`fact_slot` and `fact_slot_qualifier`, both owned by `(tenant_id, knowledge_base_id)`. F0007 enables no RLS policy and adds no `BYPASSRLS`, superuser or `SECURITY DEFINER` path. F0026 proves isolation.
