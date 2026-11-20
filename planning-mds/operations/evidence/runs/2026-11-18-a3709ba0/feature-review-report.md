# Feature Review Report — F0008 Bitemporal canonical facts (review run 2026-11-18-a3709ba0)

- **Action:** feature-review, mode `closeout-audit` (read-only)
- **Feature:** F0008 `bitemporal-canonical-facts` (archived at `planning-mds/features/archive/F0008-bitemporal-canonical-facts/`)
- **Audited feature run:** `2026-11-17-1a4ae2f0`. `latest-run.json` points to this run with `status: approved`.
- **Target:** PR #55 (MERGED, squash `339c920`). DIFF_RANGE `2badb9a..339c920`, 135 paths. The PR head `4da9f4e` tree is identical to the merge tree.
- **Reviewer:** Claude (Opus 5.5), with six role lanes (PM, Architect, QE, Code Reviewer, Security, DevOps). This was a fresh session, separate from the implementing session.
- **Date:** 2026-11-18

## Decision

**TRULY DONE.**

- Required evidence validation passes. `validate-feature-evidence.py --stage closeout` exits 0, and the four other FR2 validators also exit 0.
- There are no critical or high findings.
- `gate_policy.py --profile review-family --variant feature` returns `TRULY DONE`; see `artifacts/test-results/fr4-gate-policy.txt`.

The review independently re-ran the evidence:

- The exact CI step from `.github/workflows/ci-gates.yml` ran on PostgreSQL 18 against the merged code. 234 passed, and `brain_temporal` coverage is 97.99%.
- This matches PR #55's own CI run `44445935719`: 234 passed, 97.99%.
- The post-merge `main` CI run `44449326859` concluded `success`.

The open items are one Medium and four Low findings plus informational notes. They are tracker and evidence-hygiene repairs and defense-in-depth suggestions. None of them blocks completion, and each is routed back to its owner below. ADR-0078 formal acceptance remains an operator decision (FR-ARCH-I1).

## Findings By Severity

Counts: **Critical 0 · High 0 · Medium 1 · Low 4 · Info 5**

### Critical

None.

### High

None.

### Medium

- **FR-PM-M1: deferred obligations are not recorded on the receiving side (Requirements / Tracker Sync; owner Product Manager).**
  - **What is deferred:** F0008 hands two obligations to later features.
    - SEC-F8-02: the application must connect as a non-superuser role. Today it connects as superuser `brain`, which can set `session_replication_role = replica` and so skip the D5 triggers.
    - Durable per-refusal reason-code persistence (ADR-0078 D8 G0 note).
  - **Where the deferrals are recorded:**
    - `planning-mds/operations/evidence/runs/2026-11-17-1a4ae2f0/pm-closeout.md` (Deferred Follow-ups);
    - `security-review-report.md:73,85`;
    - `ADR-0078…md:186`.
  - **Where they are missing:**
    - `planning-mds/features/F0018-canonical-commit-service-and-action-authorization/README.md` lists F0008 only as a dependency (line 17). It mentions no application role, superuser, RLS or refusal reasons.
    - `planning-mds/kg-source/features/F0018.yaml` has the same gap.
    - ADR-0078 Consequences (`:231`) gives F0018 the RLS inventory but not the non-superuser application-role requirement.
  - **Story text:** `F0008-S0005-…md:40` (Data Requirements) still reads "Refusal reason codes in the audit". The story is marked Done, and nothing at story level says this was deferred.
  - **Risk:** when F0018 Phase A starts from its own folder and shard, both obligations can be lost.
  - **Mitigation / route:** this is targeted PM tracker rework, not a feature reopen.
    1. Add the two inherited obligations to the F0018 shard or README.
    2. Optionally add an F0018 line to ADR-0078 Consequences.
    3. Annotate the S0005 Data Requirements line as deferred to F0018.
  - **Target:** before F0018 Phase A starts.

### Low

- **FR-PM-L1: evidence drift between manifest `changed_paths[]` and the merged diff (Signoff and Closeout; owner Product Manager).**
  - **Raw diff:** this run's `artifacts/diffs/changed-files.txt` (135 paths) compared with `evidence-manifest.json` `changed_paths[]` (133 paths).
  - **Missing from the manifest:**
    - `planning-mds/knowledge-graph/coverage-report.yaml`
    - `planning-mds/operations/evidence/features/F0008-bitemporal-canonical-facts/latest-run.json`
    - `runs/2026-11-17-1a4ae2f0/token-usage.json`
  - **Listed but not committed:**
    - `runs/2026-11-17-1a4ae2f0/artifacts/security/sast/sast-semgrep-20261117-052012.sarif` does not exist on disk or in the tree. It belongs to the first SAST attempt: `commands.log` shows exit 2 at 05:20:17, and the `.log` file is 0 bytes.
  - **Impact:** the closeout validator does not cross-check `changed_paths` against SCM. The raw diff wins.
  - **Route:** feature-action owner. Refresh `changed_paths` on any later manifest patch, or record it as a known drift.
- **FR-PM-L2: STATUS header stale (Tracker Sync; owner Product Manager).** `archive/F0008-…/STATUS.md:4` reads `**Last Updated:** 2026-11-17`. Line 3 and the Closeout Summary record Done/Archived on 2026-11-18.
- **FR-SEC-L1: the scan summary disagrees with the raw SARIF (Security; owner Security Reviewer).**
  - `evidence-manifest.json:316-318` records `security_scans.sast.result: "clean"`.
  - The raw `artifacts/security/sast/sast-semgrep-20261117-052326.sarif` contains 7 results, all `avoid-sqlalchemy-text` in `0014_f0008_bitemporal_contract.py`.
  - `security-review-report.md:52` triages them as false positives.
  - This review re-read migration 0014. Every `text()`/`op.execute` interpolates module constants only, so **the triage is correct**. Only the manifest label is wrong: it should be "triaged", not "clean".
- **FR-ARCH-L1: the database backstop does not tie split lineage to the same slot (Architecture; owner Architect).**
  - `engine/migrations/versions/0014_f0008_bitemporal_contract.py:332` constrains `split_of_version_id` only by `(id, tenant_id, knowledge_base_id)`.
  - The insert guard (`:175-177`) checks only that the predecessor exists and that its contract is legacy or v1. It never checks `v.slot_id = NEW.slot_id`.
  - **Exposure:** a privileged direct insert could record cross-slot lineage within one tenant/KB. The service never does this, because `commit.py:273,616,636` takes the predecessor from `current_versions(slot)`.
  - **Tests:** `test_temporal_immutability.py::test_s0004_ac6_*` covers cross-tenant/KB lineage only.
  - **Who relies on it:** F0009 reads `split_of_version_id` for provenance lineage (ADR-0078 Consequences).
  - **Route:** decide during F0009 or ADR-0078 acceptance whether to add `predecessor.slot_id = NEW.slot_id` to the guard or a composite FK.

### Info

- **FR-ARCH-I1:** ADR-0078 is still **Proposed**. `ADR-0078…md:13` records that the six proof gates are met and that acceptance is an operator decision. This review confirms the proof-gate evidence by re-running the suites. It follows the ADR-0077/F0007 precedent of accepting after merge. **Operator action:** accept ADR-0078 or record otherwise.
- **FR-CR-I1:** the code review's informational items CR-I1, CR-I2 and CR-I3 were re-verified as accurate and are tracked with owners in `pm-closeout.md`.
  - CR-I3 means a refusal that only the database makes (tzdata divergence, PostgreSQL 2025b vs Python 2026e) surfaces as 409 `concurrent_commit` via `routes/facts.py:264`, not as a 422 reason code.
  - That fails closed, so no new finding is raised.
- **FR-CR-I2 (nit):** production `assert`s narrow types on request paths, for example `routes/facts.py:130` `assert slot is not None`. They are unreachable in practice, but under `python -O` they would turn into an AttributeError instead. Not blocking.
- **FR-QE-I1, reviewer independence:**
  - All 35 signoff rows (`signoff-ledger.md`) came from one agent identity in the implementing session, and the operator decided only at G4.
  - The contract allows this. This independent audit and the CI re-run partly offset it.
- **FR-X-I1, cross-cutting framework observation (out of F0008 scope):**
  - `run-gate.py` writes `"cwd":"{NEBULA_PRODUCT_ROOT}"` unrendered into `commands.log` for product-cwd operations (this run's `commands.log`, the FR2 `kg/validate.py` rows).
  - It also records no FR0/FR1 rows for zero-op stages.
  - Report this to nebula-agents.

## Completion Checks

### Product Manager — Requirements Satisfaction, Signoff and Closeout, Tracker Sync

| Check | Result | Raw evidence |
|---|---|---|
| Every in-scope story has an explicit disposition | PASS: 7/7 Done | `archive/F0008-…/STATUS.md` Story Checklist; story files `Status: Done` |
| ACs map to implementation and tests | PASS: 46/46 ticked | `acceptance-criteria-checklist.md`; `test-plan.md` AC→test table; test names were checked against the raw JUnit (see QE) |
| Deferred items explicit, owned, non-build-critical | PASS with FR-PM-M1 | `pm-closeout.md` Deferred Follow-ups: owners present; receiving side missing |
| Required signoffs (5 roles × 7 stories) | PASS: 35 rows, reviewer, date and evidence path | `signoff-ledger.md`, `STATUS.md` provenance |
| WITH RECOMMENDATIONS acceptance (§15) | PASS: SEC-F8-02 Low, owner, operator-accepted at G4 | `gate-decisions.md` G4 Approval Record; `pm-closeout.md` Recommendation Acceptances |
| Status, archive, registry, roadmap, story index, mappings agree | PASS: `validate-trackers.py` exits 0; story-index currency diff empty | `artifacts/test-results/fr2-validate-trackers.txt`, `artifacts/diffs/fr2-story-index-currency.diff` (0 lines) |
| latest-run.json = FEATURE_RUN_ID | PASS | `features/F0008-…/latest-run.json` → `2026-11-17-1a4ae2f0`, approved |

### Architect — Architecture and KG Alignment

| Check | Result | Raw evidence |
|---|---|---|
| Implementation matches the assembly plan and ADR-0078 D1–D10 | PASS | D1: `commit.py` `commit()` branches on `slot_identity_version`, and the insert guard binds the contract. D2: `bounds.py` plus the trigger's `date_trunc`. D3/D4: `attestation.py`. D5: `CLOSE_ONLY`/`REFUSE` triggers. D6: `routes/facts.py` 23P01→409. D7: envelope CHECK and guard. D8: `commit.py` `_guard`. D9: `reader.py`. G0 deviations are reconciled in the archived assembly plan and in ADR-0078 `:186` (operator-accepted at G4). |
| API contract matches delivered behaviour | PASS | `brain-api.yaml` adds the commit `temporal` block, the `FactValidityUnknown` 200 variant (`:218-226`, `:698-701`), `temporal_conflict` (`:425`) and the additive FactVersion fields; `schemas/facts.py` matches. No route was added (`test_s0007_ac6_no_route_is_added`). |
| Data model / migration | PASS with FR-ARCH-L1 | `0014_…py`: additive nullable columns, CHECKs, triggers, downgrade guard |
| KG bindings and code-index cover new source | PASS | `code-index.yaml` and `kg-source` contain `reader.py`, `bounds.py`, `attestation.py`, `temporal.py`, `0014_…py`, `commit.py`, `routes/facts.py`. `kg/validate.py --check-symbols` and `--check-drift` exit 0. |
| ADR state | Info (FR-ARCH-I1) | ADR-0078 is Proposed and awaits the operator |

### Quality Engineer — Test Evidence and Coverage

| Check | Result | Raw evidence |
|---|---|---|
| Raw JUnit agrees with the report counts | PASS | Parsed `g1-baseline-regression.xml` 74/74, `g2-full-engine-regression.xml` 1076/1076 and `g3-full-engine-regression.xml` 1081/1081 (0 fail, 0 error, 0 skip) |
| Cited AC tests exist in the raw results | PASS | Spot-checked 12 test IDs from `test-plan.md` in the G3 JUnit, including the post-G3 fixes `test_structurally_malformed_bounds_…` (4) and `test_other_integrity_errors_do_not_echo_database_text` (1), which are absent at G2 as expected |
| Tested code = merged code | PASS (independent re-run) | `artifacts/test-results/fr1-unit-spot-check.xml`: 107/107; per-module counts equal G3 (bounds 56, contract_examples 39, temporal_service 12). `artifacts/test-results/fr1-ci-step-rerun.{xml,txt}`: 234 passed, `brain_temporal` 97.99% (≥ 80% floor). |
| Tests ran in the required runtime and CI | PASS | `brain-postgres` PG 18.6. PR CI run `44445935719` step "Prove F0008…" gave 234 passed and 97.99% (`artifacts/test-results/fr1-pr55-ci-f0008-step-excerpt.txt`). Post-merge main CI `44449326859` succeeded. |
| Coverage ≥ 80% | PASS | Changed-line coverage 98.0% (`coverage-report.md`, `artifacts/coverage/changed-code-summary.txt`); re-run `brain_temporal` 97.99% |
| Skipped layers justified | PASS | Frontend, UX and AI are omitted with reasons in the manifest `omissions[]`; no E2E is needed for engine-only scope (`test-plan.md` Approach) |
| Failure/retry history | PASS | `commands.log` shows the G1 baseline exit 1 before the disposable DB migrated, then exit 0. SAST attempt 1 exited 2, attempt 3 exited 0. These are runtime failures, not code defects. |

### Code Reviewer — Code Quality and merge-readiness

| Check | Result | Raw evidence |
|---|---|---|
| Changed code limited to F0008 scope | PASS | 29 engine/CI paths, all in the temporal, facts, persistence or migration area. The F0007 test edits (`test_factslot_migration.py`, `test_factslot_ownership.py`, 4 lines each) are reconciled at G0/G4. |
| Vertical slice end to end | PASS | migration → models/repository → domain → service → reader → API route/schema → tests → CI step |
| Prior review findings fixed or justified | PASS | CR-L1 and CR-L2/SEC-F8-01 were verified fixed in code (`bounds.py` `InvalidRangeError` paths; `routes/facts.py:264` `ConcurrentCommitApiError(None)`) and tested in G3 |
| No hidden TODO, debug code or dead paths | PASS | `git diff 2badb9a 339c920 -- engine` has no TODO/FIXME/print/breakpoint additions. One migration head (`0014`). |
| Merge readiness | PASS: merged; post-merge CI green | `gh run view 44449326859` → success |

### Security — Security

| Check | Result | Raw evidence |
|---|---|---|
| Server-side authorization for new and changed actions | PASS | `routes/facts.py` keeps `execution.read`/`execution.mutate`. Attesting documents join the same-UoW READ checks on both GET (`scope_reads`) and POST (`source_keys`), covering D4/T-08. Temporal refusals are raised only after `require_commit_sources` (`commit.py` `pending`). `_ending_refs` uses the same `UUID(str())` parse as `parse_commit_temporal`, so no well-formed ref escapes the READ check. |
| Input validation | PASS | `bounds.py` uses an IANA allow-list (`available_timezones`) and a 64-character cap. The `extra="forbid"` schemas take exactly one of `valid_from`/`temporal`. The database re-checks zones and truncation. |
| Audit and immutability | PASS (SEC-F8-02 accepted Low) | Close-only, DELETE and TRUNCATE triggers. The refusal is audited as an F0002 failed outcome. |
| Secrets, config and leakage | PASS | The raw gitleaks SARIF has 0 results. The 409 detail is no longer echoed. Raw pip-audit: 35 deps, 0 vulns. Raw ZAP: Informational alerts only. |
| Scan labels vs raw | Low (FR-SEC-L1) | The SAST label says "clean"; the raw SARIF holds 7 triaged false positives |

### DevOps — Deployability (RUN_DEVOPS = yes)

| Check | Result | Raw evidence |
|---|---|---|
| Migration up/down/up | PASS | `g2-migration-cycle.txt`: 0014 → 0013 → 0014 (head). `test_temporal_migration.py` re-ran green in this review. |
| Rollback documented | PASS | `deployability-check.md` Rollback: the downgrade refuses once v1 rows exist (roll forward) |
| CI wiring | PASS | New `ci-gates.yml` step (+16 lines). It executed in PR CI and passed. |
| No new env vars, services, ports or secrets | PASS | `uv.lock` and `pyproject.toml` are not in the diff. The only env var is test-only (`BRAIN_MIGRATION_ADMIN_URL`). |
| Operational follow-ups | Info | The shared dev DB `brain` is at 0010 and is tracked in `pm-closeout.md`. tzdata pinning (CR-I3) is owned by DevOps. |

## Validation Evidence

| Command | Exit | Summary | Artifact |
|---|---|---|---|
| `validate-feature-evidence.py --product-root P --feature F0008 --stage closeout` | 0 | "Feature evidence validation passed", validated=1 | `artifacts/test-results/fr2-validate-feature-evidence-closeout.txt`; `lifecycle-gates.log` FR2 |
| `validate-trackers.py` (`--product-root P`) | 0 | result: PASS | `artifacts/test-results/fr2-validate-trackers.txt` |
| `scripts/kg/validate.py --check-symbols` | 0 | PASS | `lifecycle-gates.log` FR2 |
| `scripts/kg/validate.py --check-drift` | 0 | PASS | `lifecycle-gates.log` FR2 |
| `validate_templates.py` | 0 | PASS | `lifecycle-gates.log` FR2 |
| `generate-story-index.py` (currency check, on a scratch copy) | 0 | 0-line diff, so current | `artifacts/diffs/fr2-story-index-currency.diff` |
| pytest pure unit spot check | 0 | 107 passed | `artifacts/test-results/fr1-unit-spot-check.xml` |
| pytest CI F0008 step re-run (PG 18) | 0 | 234 passed, `brain_temporal` 97.99% | `artifacts/test-results/fr1-ci-step-rerun.{xml,txt}` |
| `gate_policy.py --profile review-family --variant feature` (all domains 0/0) | 0 | TRULY DONE | `artifacts/test-results/fr4-gate-policy.txt` |

## Artifact Trace

See `artifact-trace.md` for the full list. In short:

- **Read:**
  - feature-run manifest and role reports: `gate-decisions`, `signoff-ledger`, `pm-closeout`, `test-plan`, `code-review-report`, `security-review-report`, `deployability-check`, `commands.log`;
  - raw JUnit, SARIF, ZAP and pip-audit artifacts;
  - the archived feature folder (STATUS, AC checklist, S0005);
  - ADR-0078, `brain-api.yaml`, F0018 README and shard;
  - every changed engine source file at `339c920`.
- **Written (this run folder only):** `action-context.md`, `feature-review-report.md`, `README.md`, `gate-decisions.md`, `artifact-trace.md`, `commands.log`, `lifecycle-gates.log`, `gate-state.json`, and `artifacts/{diffs,test-results}/fr*`.
- **Not written:** the feature run folder, feature docs, trackers, the KG, and code.
