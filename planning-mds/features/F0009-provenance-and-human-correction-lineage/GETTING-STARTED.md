# F0009 — Getting Started

Phase B design guide — no F0009 runtime implementation exists yet.

## Planning resume

Canonical `NEBULA_PRODUCT_ROOT`: `/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain` (environment selection normalized at setup).
Run `2026-11-24-bfdbbf04`, action plan, phase A+B, feature mode new. Keep this run ID across sessions.

From `/home/gajap/uSandbox/repos/nebula/nebula-agents`:

```bash
python3 agents/scripts/resume-brief.py --product-root /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain --run-id 2026-11-24-bfdbbf04
python3 agents/scripts/project_context.py --product-root /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain --action plan
```

Read [PRD](PRD.md), [STATUS](STATUS.md), all six stories and the run's [gate decisions](../../operations/evidence/runs/2026-11-24-bfdbbf04/gate-decisions.md). G3 is complete with the exact operator token `approve-phase-a`. Read the [assembly plan](feature-assembly-plan.md), proposed [ADR-0080](../../architecture/decisions/ADR-0080-bounded-provenance-and-correction-reservations.md) and [contract inventory](contract-inventory.yaml). G4 and the G5 pre-approval checks passed. Phase B approved 2026-11-24 by operator token `approve-phase-b`; the run journal/manifest records the final G5 refresh and publication. Run the independent plan-review action before implementation.

## Carry-ins and gotchas

- F0006 v2 corrections remain v2; source READ happens before claim materialization. Preserve legacy qualification rather than inventing metadata.
- ADR-0044's old limitation paragraph assigns orchestration to F0002; current BLUEPRINT §4.10 and F0018 ownership supersede that sequencing shorthand. Review submission still never writes canonical versions.
- F0008 `split_of_version_id` is same-slot (migration 0015). `ending_refs` is inside the version evidence JSON. Remainders retain predecessor evidence/timestamps and version rows are close-only.
- F0008 second remediation requires current READ of predecessor attestation sources even for commit responses. Apply the same source boundary to a lineage result.
- F0010 owns the unresolved reason-aware retraction amendment; this feature leaves the current PRESENT guard intact.
- Use the delivered F0011 offline contract pipeline. The Architect inventories consumers and designs the reserved-reference contract; no F0041 learning producer is assumed.
- The current application database role has elevated privileges; future F0018 RLS cannot substitute for application authorization tests.

## Runtime setup / verification

The [assembly plan](feature-assembly-plan.md) supplies exact proposed package/test paths, migration order, schema consumer inventory, SQL/semantic guards and verification commands. Use the existing integration PostgreSQL fixture/Compose configuration; no new secret or environment variable is required. Implementers verify invocation syntax and record observed commands/results in the later feature action. Planning examples validate structurally only.

## Existing entry points bound by the approved assembly plan

`engine/packages/brain-review/src/brain_review/decisions.py`, `engine/packages/brain-persistence/src/brain_persistence/repositories.py`, `engine/packages/brain-persistence/src/brain_persistence/assertions.py`, and the shipped temporal reader/commit and schema bundle. These are existing source references, not a proposed F0009 package layout.


## Migration and concurrency gotchas

- Proposed 0016 follows the current 0015 head; rebase the identifier at feature G0 if another migration lands.
- The server stamps correction_lineage_contract=1 only on new review_decision inserts. Historical NULL markers stay untouched, and cannot acquire fabricated reservations. A deferred constraint requires a reservation for every new effective CORRECT by commit.
- Explicitly persist decided_at=decision.decided_at on new rows so reservation actor/time matches the actual stored decision. Do not rely on a second server clock.
- Preflight and lock the whole batch before any correction. A typed refusal result commits only protected attempt/audit rows before the route returns its existing 422; raising early would lose the attempt record.
- Refused attempts are history, never a replay key. Only ReviewDecision rows produce duplicate outcomes. Attempts are get-or-create on (item, event, outcome), and each refused request writes its own refusal audit (PR-H1).
- Provenance edges read `<source> <kind> <target>` and follow only the assembly plan's Edge Semantics table. The schema enforces the pairs; the domain enforces uniqueness, endpoint presence and root connectivity (PR-H2).
- Metadata discovery/final fingerprint must use the same unit of work and locked current authority. Never call execution.read inside execution.mutate.
- Once a reservation or refusal row exists, downgrade refuses under table locks. Keep compatible schema/data and forward-repair; do not delete lineage for rollback.
