# F0007 — Getting started

**State:** Done and archived 2026-11-09. Phase A and Phase B were approved in plan run `2026-11-09-60865e32`; feature run `2026-11-09-b94cfa12` implemented, reviewed and closed all six stories.

Read these in order:

1. [PRD.md](PRD.md)
2. [personas.md](personas.md)
3. the six story files
4. [acceptance-criteria-checklist.md](acceptance-criteria-checklist.md)
5. [STATUS.md](STATUS.md)
6. the [assembly plan](feature-assembly-plan.md)
7. [ADR-0077](../../../architecture/decisions/ADR-0077-factslot-identity-and-typed-answer-carriers.md)
8. the [worked examples](worked-examples.md)

The bound product root is `/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain`. Framework commands run from `nebula-agents` and always receive that absolute root.

## Key files (as built)

| Concern | Path |
|---|---|
| Identity, predicate keys, qualifiers, fingerprint | `engine/packages/brain-domain/src/brain_domain/fact_slots.py` |
| Typed values: decimal, money, identifiers, names, JCS | `engine/packages/brain-domain/src/brain_domain/fact_values.py`, `data/iso4217-2026-01.txt` |
| `fact-answer/v1` carrier and reasons | `engine/packages/brain-domain/src/brain_domain/fact_answers.py` |
| Resolver, answer policy, name hook, registry, authorized facade | `engine/packages/brain-factslots/src/brain_factslots/` |
| PostgreSQL store and qualifier mapping | `engine/packages/brain-persistence/src/brain_persistence/fact_slots.py`, `fact_slot_models.py` |
| Migration | `engine/migrations/versions/0012_f0007_factslot_identity.py` |
| Commit hook and API wiring | `brain_temporal/commit.py` (`CommitAnswerPolicy`), `brain_api/routes/facts.py`, `errors.py`, `deps.py` (`get_predicate_registry`) |
| Test composition (`test` namespace, seed helpers) | `engine/packages/brain-testing/src/brain_testing/factslots.py` |
| PostgreSQL harness and pilot fixtures | `engine/tests/fixtures/factslots/` |

Release references: system predicates are pinned at `f0007-system-predicates/1`; the test namespace at `f0007-fixtures/1`.

## Verify locally

```bash
# product root; needs the Compose PostgreSQL and an admin URL for owned test databases
export BRAIN_MIGRATION_ADMIN_URL=postgresql://brain:brain@localhost:5432/brain
engine/.venv/bin/python -m pytest engine/packages/brain-factslots/tests \
  engine/tests/integration/test_factslot_{migration,resolution,ownership,answers,names}.py \
  --cov=brain_factslots --cov-fail-under=80
```

Each integration test creates and drops its own database. The shared development database is never migrated or truncated by these suites. To regenerate the pilot snapshot after an intentional seed change, run the migration test once with `F0007_WRITE_PILOT_SNAPSHOT=1`.

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
- **Entity references that leave the KB.** An entity reference in a qualifier, a MULTI member or an answer value that is not associated with the slot's KB is rejected with `RELATIONSHIP_OBJECT_OUT_OF_SCOPE`, the same reason as an out-of-KB relationship object.
- **The name hook authorizes per slot.** `AuthorizedFactSlots.current_names` runs `fact_slot:read` on each candidate slot. A slot the reader cannot read is absent, exactly like a missing one.
- **The backup inventory hashes present columns only.** `scripts/ops/verify_content.py` reads the columns that exist at the database's revision, so backups of databases older than 0012 still work.

## RLS inventory handed to F0018

`fact_slot` and `fact_slot_qualifier`, both owned by `(tenant_id, knowledge_base_id)`. F0007 enables no RLS policy and adds no `BYPASSRLS`, superuser or `SECURITY DEFINER` path. F0026 proves isolation.
