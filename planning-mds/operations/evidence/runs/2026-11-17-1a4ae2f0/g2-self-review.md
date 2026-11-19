# G2 Self-Review — F0008 (run 2026-11-17-1a4ae2f0)

- Roles: Backend Developer (implementation), Quality Engineer (tests), DevOps (deployability)
- Reviewer: Claude (Opus 5.5)
- Date: 2026-11-17
- Verdict: PASS

## Scope Review

The slice stays inside F0008. It touches the engine only: migration 0014, `brain_domain.temporal`, `brain_temporal`, `brain_persistence` and the two existing `/facts` routes. It also changes test harnesses and the CI wiring. It adds no route, grant, table, UI, producer or model call.

Scope booleans reconciled against `changed_paths` (notes.scope_booleans):

| Boolean | Value | Basis |
|---|---|---|
| `runtime_bearing` | true | `engine/**` runtime and tests |
| `deployment_config_changed` | true | `engine/migrations/versions/0014_*.py` and `.github/workflows/ci-gates.yml` |
| `security_sensitive_scope` | true | Set at G0 from the Phase B risk list (attestation disclosure, triggers under application roles, non-disclosing refusals). No `auth`/`identity` path glob matches, so the flag comes from that risk call, not a path class. |
| `frontend_in_scope` | false | No `experience/**` path |

No boolean changed after G0, so G2 does not need a re-run.

## Backend self-review

- [x] **API endpoints per contract.** The two existing `/facts` routes change only additively:
  - the `temporal` request block;
  - `FactVersion.temporal` and the four optional read fields;
  - the `FactValidityUnknown` 200 variant;
  - the ten 422 codes;
  - the 409 `temporal_conflict`.

  The `brain-api.yaml` `FactVersion` lists the optional fields (G0 reconciliation 6).
- [x] **Domain logic complete and tested:**
  - `brain_domain.temporal`;
  - `brain_temporal.bounds`, `.attestation`, `.reader`;
  - the v1 path in `.commit`.
- [x] **Unit tests pass.** 124 brain-temporal unit tests, with 96.6% `brain_temporal` coverage measured without a database.
- [x] **Integration tests pass** on PostgreSQL 18 (see `test-execution-report.md`).
- [x] **SOLUTION-PATTERNS:**
  - clean layering (domain → `brain_temporal` application → `brain_persistence` → API);
  - repository protocols;
  - ProblemDetails with code-only 422s;
  - authorization stays in `AuthorizationExecution`, with the same-UoW reads extended to attesting documents.
- [x] **Migration** applies, downgrades and re-applies.

### Findings fixed during self-review

1. **End revisions:** an end revision now replaces its version whole. Without this, a right-hand remainder would re-open the old fact after an UNKNOWN end, contradicting EX-PC-014-D.
2. **Right-hand remainders:** only a `BOUNDED` successor leaves one, per the D5 wording. The finite upper bound of an UNKNOWN end is an integrity bound, not a stated end.
3. **Commit-side disclosure:** legacy evidence had no READ check. The documents whose dates can attest the version now join the commit's same-UoW READ checks, so neither `attestation_mismatch` nor `start_unattested` can reveal the date of a document the committer cannot read. S0002 asks for this.
4. **Read timestamps:** the `brain-api.yaml` `FactVersion` lacked the optional S0006 AC5 fields under `additionalProperties: false`. The fields were added.
5. **Migration SQL:** the envelope predicate builder used a string replace that would have rewritten the `'value'` key literal. It became a function before the first run. `'1 quarter'` is not a valid interval, so QUARTER maps to `3 months`.

## Implementation Risks

Interpretations recorded (no behaviour beyond the plan):

- **Current selection:** "current date selection" means the highest sequence. A current clear leaves the document undated, which matches the F0004 read (`DocumentDateView.selected_date`). ADR-0078 D4's "highest sequence that is not a clear" is read this way, not as "skip clears".
- **Ending refs:** `ending_evidence_refs` are assertion-evidence IDs, the same kind as `evidence_refs`. They travel in the version's `evidence` JSONB as `ending_refs`, so remainders and the GET's disclosure check can see them.
- **Attesting documents on GET:** for a v1 version with any attestation date, the GET's attesting documents are all of its evidence and ending-evidence artifacts. This is conservative: an unreadable one yields a whole-read 404.
- **Legacy slots:** a `temporal` block sent to a legacy pilot slot returns `400 invalid_request` (D1: the pilot shape is kept).

## Acceptance Criteria Review

| Story | ACs | Self-review result |
|---|---|---|
| S0001 | 6 | Met. Every granularity, DST, `Etc/GMT+6`; the trigger agrees with the service |
| S0002 | 7 | Met. EX-SEM-004, floor, `START_UNATTESTED`, `ATTESTATION_MISMATCH`, the response distinguishes end states |
| S0003 | 7 | Met. §115.4 retroactive change and correction, remainder lineage and timestamps, close-only, one transaction |
| S0004 | 6 | Met. Race on the grid, direct inserts, members, RELATIONSHIP, envelope, cross-scope |
| S0005 | 7 | Met. Bases, end revision, EX-OWN-003, state guard, per member |
| S0006 | 7 | Met. §87 grid, EX-PC-014 A–D, half-open bounds, read shape, coordinates, revocation |
| S0007 | 6 | Met. Byte-identical migration cycle, legacy marker, pilot shape, downgrade guard, existing suites, no grant or route |

The test-by-test traceability is in `test-plan.md`.

## Quality Engineer self-review

- [x] The test plan maps all 46 ACs and the six ADR-0078 proof gates (`test-plan.md`).
- [x] Expectations come from the ACs and the worked examples. The suites found and fixed four test-side mistakes, none of them a code defect:
  - the F0007 envelope key is `scope`, not `absence_scope`;
  - an absence scope needs `pages`;
  - a direct-insert copy has to carry the end-bound columns;
  - one unit expectation misplaced `validity_unknown_from`.
- [x] The concurrency suite passed three consecutive runs (12 racers; grid of at least 200 coordinates).
- [x] Existing suites:
  - Two F0007 tests were adjusted to approved F0008 semantics: a member change now uses `EXPLICIT_NEGATIVE` (G1 decision 2), and the F0007 migration cycle is pinned to 0013. Their intent is unchanged.
  - The F0007 harness commit helper sends the v1 block. Logged as `plan-story-reconcile` decisions in `artifacts/workstate.json`.
  - All other suites are unchanged.

## DevOps self-review

- [x] Runtime preflight re-confirmed: `brain-postgres` was healthy throughout. The only blocker was the pre-run Docker Desktop stop (G1).
- [x] Migration cycle logged; the downgrade guard and the upgrade preflight are proven.
- [x] CI wiring added; the no-database package gates were checked locally.
- [x] No environment variable, secret, container or port added.

Open items carried to G3/G4:

- **DAST** was blocked at G2: auto mode denied binding the test server. The operator approved the ZAP scan on 2026-11-18, and it ran at G3 with 0 FAIL and 0 WARN (`security-review-report.md`).
- **SAST:** 7 `avoid-sqlalchemy-text` audit findings in migration 0014. They interpolate module constants only, and G3 triages them.
- **Contract drift (follow-up):** `brain-api.yaml` describes `FactVersion.valid`/`recorded` objects, while the runtime has used `valid_start`… since F0001. This predates F0008 and is out of its scope.

## Validation Evidence

- Final full engine regression: 1081 passed, 0 failed, 0 skipped (`artifacts/test-results/g3-full-engine-regression.xml`). The G2 run had 1076 passed.
- Changed-line coverage: 98.0% (`coverage-report.md`).
- `ruff check`, `ruff format --check` and the CI `mypy` target set are clean (`commands.log`).
- Migration cycle: `artifacts/test-results/command-output/g2-migration-cycle.txt`.
- Scans:
  - dependency clean;
  - secrets clean;
  - SAST triaged;
  - DAST 0 FAIL / 0 WARN (`artifacts/security/**`).
- Reports: `test-execution-report.md`, `deployability-check.md`.
