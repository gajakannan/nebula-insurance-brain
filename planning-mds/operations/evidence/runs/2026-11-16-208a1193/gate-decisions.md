# Gate Decisions — F0008-bitemporal-canonical-facts run 2026-11-16-208a1193

NEBULA_PRODUCT_ROOT: /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain

## Gate Decisions

| Gate | Decision | Decider | Timestamp | Rationale | Blocking | Follow-up |
|---|---|---|---|---|---|---|
| G1 | PASS | Product Manager (Claude) | 2026-11-16T06:00:08-05:00 | Four open requirement questions answered by the operator; remaining design choices assigned to Phase B | No | G2 tracker validation |
| G2 | PASS | Product Manager (Claude) | 2026-11-16T06:00:08-05:00 | Seven stories pass story validation with no warnings; STORY-INDEX regenerated (54 stories); trackers 0 errors/0 warnings; Brain plan-readiness exit 0; dependency audit recorded in artifact-trace.md | No | G3 operator review |
| G3 | PASS | Operator token; Product Manager attestation | 2026-11-16T06:41:45-05:00 | Explicit approve-phase-a recorded; checkpoint attested and approve-plan.py Phase A operation run | No | Phase B; A+B manifest remains draft |
| G4 | PASS | Architect (Claude) | 2026-11-16T08:35:10-05:00 | Feature, node and planning-binding shards authored; compile and drift check exited 0 through the gate driver; seven stories mapped; coverage exclusion removed. The first G4 attempt failed at kg-compile on a YAML plain-scalar colon in a capability note; the note was re-emitted quoted and G4 re-run | No | G5 exit validation and architecture review |
| G5 | PASS | Operator token; Architect attestation | 2026-11-17T00:02:22-05:00 | Explicit approve-phase-b recorded (includes the ADR-0078 D8 end-revision clarification); pre-checkpoint exit operations exited 0; checkpoint attested and post-approval operations run through the gate driver | No | plan-review; ADR-0078 stays Proposed until F0008 proof gates |

## Clarification Judgment (G1)

The sources leave four business rules open. The operator answered them on 2026-11-16, choosing the recommended option each time:

1. **Start basis and the succession guard (ADR-0064 §7).** Time-mention grades come from F0016, which is not built. **Decision:** each version stores how its start was obtained (`TEMPLATE_FIELD`, `HUMAN`, `MENTION_A/B/C`). A template field or a human-entered date counts as grade `A`. Grade `C` cannot close or split a predecessor (`SUCCESSION_START_UNANCHORED`). Routing the refusal to review is F0018's work.
2. **Information-state supersession (ADR-0039, 2026-11-08 amendment).** **Decision:** a `PRESENT` value can be closed only by `PRESENT` or `EXPLICIT_NEGATIVE`. Every other state against a `PRESENT` predecessor is refused (`STATE_SUPERSESSION_REFUSED`). Removing a value is an F0010 correction or retraction. A non-`PRESENT` predecessor can be closed by any answer.
3. **Unknown start with undated evidence (ADR-0064 §5).** **Decision:** refuse with `START_UNATTESTED`. A start is never widened to minus infinity, and upload, receipt or acceptance time is never used as a substitute.
4. **Time zone of date-granular bounds.** **Decision:** the caller supplies an IANA zone per bound. F0008 validates truncation in that zone and stores it. Document conventions stay with the caller: the template route now, F0016 later.

The PRD records four PM assumptions, labelled for G3 review:

- **A1:** identity-v1 slots require the new temporal fields. Legacy pilot slots keep the pilot shape, with no fabricated values.
- **A2:** every slot is `STATE` until F0012/F0013 declare `temporal_kind`. The row design must still hold `EVENT` and `ETERNAL` without DDL.
- **A3:** a commit writes a full version, and changing only an end closes and replaces.
- **A4:** an unknown start with dated evidence is floored at `attested_from`. It is marked as such and, like grade `C`, cannot close a predecessor.

A4 is derived from EX-SEM-004 together with ADR-0064 §7.

**Phase B owns:**

- the unknown-end representation inside the exclusion constraint;
- the immutability trigger, with the §109.2 close-only rule confirmed against the event-derived alternative;
- the envelope backstop;
- the commit and read contract additions;
- reconciling §78 `canonical_relationship_version` with F0007 RELATIONSHIP slots;
- the migration and rollback.

No business rule beyond the cited sources was invented. One correction was made while drafting: the EX-SEM-003 "standard time" fixture uses `Etc/GMT+6`, because `America/Chicago` in July would mean CDT.

## Approval Checkpoints

The initial instruction to execute plan is not a review approval. A manual checkpoint is attested only after the operator explicitly approves the corresponding reviewable artifacts.

## G3 Review Package

Phase A is ready for operator review:

- seven stories with 46 ACs;
- four existing personas;
- no new UI, route or grant.

Review the feature PRD, personas, stories, acceptance checklist and STATUS skeleton. The gate driver is paused at `approve-phase-a`, and no approval operation has run. Proposed explicit operator token: `approve-phase-a`.

Validation is recorded in `artifacts/test-results/phase-a-*.log` and commands.log:

- story validation PASS: seven stories, no warnings, after one wording pass that made the authorization, audit and negative paths explicit;
- story index regenerated: 54 repository stories;
- tracker validation PASS: 0 errors and 0 warnings, with feature evidence intentionally skipped;
- Brain plan-readiness for F0008: exit 0.

G3 had no PASS decision until the operator approved (see Explicit Phase A Approval). The plan manifest stays draft. After G3 approval, Phase B completes the KG mapping, removes the reserved coverage exclusion, compiles the projections, and runs the ontology and exit checks.

## Explicit Phase A Approval

- **Token:** `approve-phase-a`
- **Source:** the operator's reply in the plan session. It came after the G3 review package was presented: the PRD, personas, seven stories with 46 ACs, the checklist, STATUS, the four G1 decisions and PM assumptions A1–A4.
- **Timestamp:** 2026-11-16T06:41:45-05:00
- **Scope:** Phase A requirements as drafted. Assumptions A1–A4 are accepted with the package. The roadmap lane stays Now.

## Phase B Operator Decisions (2026-11-16)

Two conflicts between the approved Phase A text and the sources came up during Phase B. Per the plan contract (PRD vs architecture: resolve in Phase B, never silently), the operator was asked and answered:

1. **Reads before an attestation floor.**
   - The conflict: S0002 AC4 said "returns no version", which S0006 AC2 would surface as `NOT_PROCESSED`. EX-PC-014-B expects `UNKNOWN`.
   - **Decision:** validity-unknown.
   - Edited: S0002 AC4 and S0006 AC3, both marked *Amended at Phase B*, and PRD scope item 7.
2. **HTTP exposure of states.**
   - The conflict: F0007 left the GET unchanged and assigned HTTP information states to F0020, while S0006 AC2/AC3 named `NOT_PROCESSED` and validity-unknown results.
   - **Decision:** the internal `TemporalFactReader` returns `NOT_PROCESSED` and validity-unknown. The GET adds a `temporal` block and an additive `FactValidityUnknown` 200 variant for identity-v1 slots, and a coordinate with no version keeps the pilot 404.
   - Edited: S0006 AC2, marked *Clarified at Phase B*, and the PRD.

## Phase B Design Decisions and G5 Review Package

The Architect authored these Phase B artifacts:

- the feature assembly plan, Proposed ADR-0078, and the new design schema `fact-temporal-v1`;
- an additive `temporal` block, with `oneOf` legacy/v1, in `canonical-commit-request`;
- `brain-api.yaml` 0.5.0: `FactVersion.temporal`, the `FactValidityUnknown` variant, ten 422 reason codes and 409 `temporal_conflict`;
- 20 positive and negative contract cases;
- GETTING-STARTED, and the feature ER and component diagrams in the README;
- the required role matrix (QE, Code Review, Security, DevOps, Architect);
- updates to the data model, the glossary (four terms, plus the canonical-relationship-version note), BLUEPRINT §4.7 and §4.15, the umbrella assembly index and the examples coverage map;
- KG feature, node and binding shards.

No implementation file or feature evidence package was created.

**Review points (ADR-0078):**

1. **D1 versioned contract.** `temporal_contract` is NULL (legacy) or 1. Identity-v1 slots require the `temporal` block. Legacy rows are never backfilled. A remainder of a legacy row stays legacy (`split_of_version_id`).
2. **D2 precision and zone.** Granularity and IANA zone are stored per bound. Truncation is checked in Python and authoritatively in a PostgreSQL trigger (`date_trunc(field, ts, zone)`), and the run records both tzdata versions.
3. **D3 unknown end.** The ADR-0064 option is adopted: the integrity range closes at the exclusive end of the `attested_to` period, and reads in `[validity_unknown_from, upper)` are validity-unknown. The exclusion DDL is unchanged.
4. **D4 attestation.** It is derived from current F0004 date selections on the evidence and ending evidence, never from clocks. An unknown start is floored at `attested_from` (`ATTESTATION_FLOOR`) or refused. The attesting documents join the GET `additional_reads`, so whole-read denial applies (T-08).
5. **D5 close-only immutability.** Triggers allow a single close of an open recorded interval and refuse every other UPDATE, DELETE and TRUNCATE. `canonical_fact_change` is append-only. Remainders carry their predecessor's payload, evidence and timestamps (the pilot defect is fixed), and change rows link to remainders. The event-derived alternative is rejected.
6. **D6 concurrency and relationships.** The existing slot lock plus the exclusion apply; `23P01` maps to 409 `temporal_conflict` with no rows written. RELATIONSHIP slots version in the same table; the §78 `canonical_relationship_version` table is not created.
7. **D7 envelope backstop.** A CHECK and an insert trigger enforce the state/value predicate. The preflight refuses malformed existing rows.
8. **D8 guards**, enforced by the service:
   - the start-basis guard: grade C or an attestation floor closes nothing;
   - the state guard: a PRESENT value closes only to PRESENT or EXPLICIT_NEGATIVE.
   - **Proposed clarification needing explicit approval:** an *end revision* (same answer, start bound, basis and `attested_from`, with only the end changed) is not a succession and is not blocked by the start-basis guard. Without it, the approved S0005 AC3 would refuse EX-PC-014's `OPEN` → `UNKNOWN` on a floored fact. S0005 AC3 carries the note.
9. **D9 reads**, as decided above. **D10:** `temporal_kind` is reserved; F0008 writes STATE only.
10. **Migration 0014.** Additive, with a guarded downgrade. The revision number is coordinated with the parallel F0011 lane.

**Known trade-offs:**

- The guards are service-enforced and are not a database invariant.
- The tzdata versions can drift between PostgreSQL and Python; the database is authoritative.
- Legacy versions on identity-v1 slots carry no temporal fields until superseded.
- Most v0.1 documents are undated, so unknown-start commits are mostly refused until F0022/F0016.

**Additional checks.** All exited 0; the logs are in `artifacts/test-results/phase-b-*.log`.

- the offline check of the 20 contract cases against the schemas (`artifacts/validation/validate-contract-examples.py`), 20/20;
- Brain plan-readiness for F0008;
- story re-validation after the amendments, 7/7 clean;
- semantic-example validation;
- relative-link resolution across edited documents;
- `git diff --check`.

**G5 process:**

1. G5 runs its pre-checkpoint exit operations in declared order, then pauses at `approve-phase-b`. Reaching that pause is not a G5 PASS or A+B approval.
2. Proposed explicit operator token: `approve-phase-b`. That token also approves the D8 end-revision clarification.
3. After receiving it:
   - make the approval-status edits;
   - record the token;
   - attest with gate-decisions.md;
   - re-run G5's post-approval operations.
4. No planning edits follow the final refresh.

## Explicit Phase B Approval

- **Token:** `approve-phase-b`
- **Source:** the operator's reply in the plan session, after the G5 review package above was presented (assembly plan, Proposed ADR-0078 D1–D10, `fact-temporal-v1`, the `canonical-commit-request` and `brain-api.yaml` 0.5.0 changes, 20 contract cases, GETTING-STARTED, the role matrix and KG shards).
- **Timestamp:** 2026-11-17T00:02:22-05:00
- **Scope:** the Phase B design as drafted, including the ADR-0078 D8 end-revision clarification on S0005 AC3. ADR-0078 stays Proposed; formal acceptance needs its PostgreSQL proof gates in the feature action.
- **Post-approval edits (status only):** STATUS, README, PRD and assembly-plan status lines; the ADR-0078 design-review line; the S0005 AC3 approval marker; BLUEPRINT §3.3 and §4.15 headings; KG notes for the feature, capability and schema. No requirement or design content changed.
