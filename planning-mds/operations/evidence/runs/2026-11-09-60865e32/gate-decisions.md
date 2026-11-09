# Gate Decisions — F0007-factslot-model run 2026-11-09-60865e32

NEBULA_PRODUCT_ROOT: /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain

## Gate Decisions

| Gate | Decision | Decider | Timestamp | Rationale | Blocking | Follow-up |
|---|---|---|---|---|---|---|
| G1 | PASS | Product Manager (Claude) | 2026-11-09T05:15:44+00:00 | Three open requirement questions answered by the operator; remaining design choices assigned to Phase B | No | G2 tracker validation |
| G2 | PASS | Product Manager (Claude) | 2026-11-09T05:15:44+00:00 | Six stories pass strict validation; STORY-INDEX regenerated (43 stories); trackers 0 errors/0 warnings; dependency audit recorded in artifact-trace.md | No | G3 operator review |
| G3 | PASS | Operator token; Product Manager attestation | 2026-11-09T16:48:30+00:00 | Explicit approve-phase-a recorded; checkpoint attested and approve-plan.py Phase A operation completed | No | Phase B; A+B manifest remains draft |
| G4 | PASS | Architect (Claude) | 2026-11-09T17:01:38+00:00 | Authored feature/node/binding shards compiled; drift check exited 0; six stories mapped with planning-only bindings; one compile doc-ref error repaired before the passing run | No | G5 architecture review |

## Clarification Judgment (G1)

The sources left three business or sequencing decisions open. The operator answered them on 2026-11-09:

1. **Row security sequencing.** The F0007 shard asked F0007 to follow the ADR-0042 RLS pattern "settled in F0018 Phase B", but F0018 depends on F0007. **Decision:** F0007 binds new rows to tenant/KB ownership (composite keys and immutability triggers, the F0002/0007 pattern) and hands an RLS table inventory to F0018. F0018 Phase B designs and enables RLS on all tenant-owned tables; F0026 proves isolation.
2. **Predicate identity before the ontology.** F0012/F0013 declare predicates after F0007. **Decision:** an opaque, namespaced predicate key with a pinned ontology-release reference, plus a minimal F0007 system-predicate set (the four ADR-0066 name predicates and test fixtures). This is the key the ADR-0038 SourceAuthorityPolicy references.
3. **Display-name precedence.** ADR-0066 gives no order across name kinds. **Decision:** F0007 provides a precedence-free display-name hook. The rule is an open decision owned by F0017/F0023.

The PRD records three PM assumptions labelled for G3 review: slots are KB-owned (derived from ADR-0061 and ADR-0066 §1a), an unread slot reads `NOT_PROCESSED`, and money is original-currency only. Phase B owns the canonical encoding, hash function, omitted-versus-null rule, member-identity representation, carrier placement on the F0008-owned version row, legacy `slot_type` handling and migration/rollback. No business rule beyond the cited sources was invented. The FEIN normalization fixture in S0004 reflects the identifier's standard nine-digit form.

## Approval Checkpoints

The initial instruction to execute plan is not a review approval. A manual checkpoint is attested only after the operator explicitly approves the corresponding reviewable artifacts.

## G3 Review Package

Phase A is ready for operator review: six stories, 39 ACs, four existing personas, no new UI, no new route or grant. Review the feature PRD, personas, stories and acceptance checklist. The gate driver is paused at `approve-phase-a`, and no approval operation has run. Proposed explicit operator token: `approve-phase-a`.

Validation: strict story validation PASS (six stories, no warnings), story index regenerated (43 repository stories), tracker validation PASS (0 errors/0 warnings, feature evidence intentionally skipped). Output is in `artifacts/test-results/phase-a-*.log` and commands.log.

G3 had no PASS decision until the operator approved (see Explicit Phase A Approval). The plan manifest stays draft. Phase B completes the KG mapping, removes the reserved coverage exclusion, compiles projections and runs the ontology and exit checks after G3 approval.

## Explicit Phase A Approval

- **Token:** `approve-phase-a`
- **Source:** operator reply in the plan session, given after the G3 review package was presented (PRD, personas, six stories / 39 ACs, checklist, STATUS, G1 decisions and the three PM assumptions)
- **Timestamp:** 2026-11-09T16:48:26+00:00
- **Scope:** Phase A requirements as drafted. The three PM assumptions (KB-owned slots, unread slot reads `NOT_PROCESSED`, original-currency money only) are accepted with the package. The roadmap lane stays Next.

## Phase B Design Decisions and G5 Review Package

The Architect authored these Phase B artifacts:

- the feature assembly plan, Proposed ADR-0077, and three versioned design schemas (`fact-slot-key-v1`, `fact-answer-v1`, `fact-slot-resolution-result-v1`);
- 26 positive and negative contract cases, worked and boundary examples, GETTING-STARTED (gotchas plus the RLS inventory), and feature ER/component diagrams;
- updates to data-model, glossary, BLUEPRINT §4.14, the umbrella assembly index and the commit-route 422 description;
- the required role matrix (QE, Code Review, Security, DevOps, Architect);
- KG feature, node and planning-binding shards.

No implementation file or feature evidence package was created.

**Review points:**

1. **Identity:** tenant, KB, subject, opaque `ns:name@vN` predicate key and normalized qualifier rows. The SHA-256/JCS fingerprint only accelerates lookup. A collision is rejected, never merged. The release reference is recorded but is not identity.
2. **Qualifier rule:** an omitted qualifier contributes nothing, and an explicit null is rejected (`QUALIFIER_NULL_REJECTED`).
3. **Members:** MULTI members are child `fact_slot` rows. The ADR-0008 exclusion then applies per member without DDL on the F0008-owned version table.
4. **Answers:** the `fact-answer/v1` envelope lives in `canonical_fact_version.value` and applies to identity-v1 slots only. The pilot GET is unchanged; an unread slot answers `NOT_PROCESSED` through the internal reader, and HTTP exposure of states is F0020.
5. **Authorization:** slot creation runs under existing `content_artifact:interpret` over the source artifacts, with derived restrictions (ADR-0042 decision 4). No new grant or action is added. The commit adds the scope artifact and name evidence to its same-UoW READ checks, so denial precedes any reason code.
6. **Legacy slots:** pilot slots stay legacy. An immutability trigger blocks fabricated identities, and no `slot_type` mapping is created.
7. **RLS inventory:** `fact_slot` and `fact_slot_qualifier` are handed to F0018.

**Known trade-offs:**

- State/value integrity is enforced by the service until F0008 adds a database backstop.
- Slot restrictions are fixed from their creating sources; F0018 owns re-derivation.
- No real predicate is usable until F0012/F0013 register one.

**Additional checks, all exit 0:**

- the offline check of the 26 contract cases against the three schemas, with local references only (`artifacts/validation/validate-contract-examples.py`);
- Brain plan-readiness;
- semantic-example teaching validation;
- relative-link resolution across edited documents;
- `git diff --check`.

One mis-logged `--help` invocation of the semantic validator remains in commands.log and was followed by the real run.

**G5 process:**

1. G5 runs its pre-checkpoint exit operations in declared order, then pauses at `approve-phase-b`. Reaching that pause is not a G5 PASS or A+B approval.
2. Proposed explicit operator token: `approve-phase-b`.
3. After receiving it: make the approval metadata edits (STATUS/README/PRD/assembly plan/ADR/BLUEPRINT/data-model/schema and ADR KG notes), record the token, attest with gate-decisions.md, and re-run G5's post-approval operations.
4. No planning edits follow the final refresh.

## Explicit Phase B Approval

- **Checkpoint:** `approve-phase-b` (G5)
- **Operator token:** `approve-phase-b`
- **Source:** the operator's reply in the plan session, after reviewing the Phase B assembly plan, ADR-0077, the three design schemas and the ontology package
- **Recorded by:** Architect (Claude)
- **Recorded at:** 2026-11-09T17:22:07+00:00
- **Precondition met:** all seven G5 pre-checkpoint exit operations completed in declared order with exit 0, and the driver paused at `approve-phase-b`.
- **Scope approved:** the six-story, 39-AC F0007 Phase B design, including the seven review points and the three known trade-offs listed above.

**Approval-status edits made before attestation:**

- feature STATUS, README, PRD, GETTING-STARTED and assembly plan;
- ADR-0077 design-review metadata;
- BLUEPRINT (§3.3 line and §4.14), data-model, umbrella assembly index and the brain-api commit description;
- KG ADR and schema node notes.

**Unchanged:**

- ADR-0077, ADR-0039 and ADR-0066 remain Proposed, pending their runtime proofs.
- All six stories remain Not Started.
- The feature shard's `validation_gate` entry criterion is unchanged.

**Next:**

- This approval evidence is frozen for attestation.
- G5 runs compile, coverage refresh, reproducibility, plain KG validation, tracker-only validation and approve-plan.py, in that order.
- No manifest status is changed manually, and no planning-source edit follows the final refresh.
