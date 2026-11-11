# F0007 Feature Review — 2026-11-10-86ee5ef7

## Decision

**CONDITIONALLY DONE** (`gate_policy.py --profile review-family --variant feature`: 0 Critical, 1 High). The remediated source is correct, and its tests, lint and types pass. The fixes are not yet delivered: they exist only as uncommitted changes on `fix/f0007-review-remediation`.

- Mode: closeout-audit. Run audited: `2026-11-09-81798e61` (latest-run.json, approved, supersedes `2026-11-09-b94cfa12`).
- Changed-file set: `ff0a619..fa8fc1d` (PR #43), plus the working tree on `fix/f0007-review-remediation` (48 paths: the 47 in the manifest `changed_paths`, plus the `latest-run.json` pointer written at G8).
- RUN_DEVOPS: no. The only CI change is two test files added to an existing PostgreSQL step. No new services, environment variables or ports.

## Findings By Severity

### FR-H1 — High — Remediation is uncommitted; `main` still contains the defects
- **Evidence:** `git status` on the product repo shows migration `0013_f0007_identity_guard.py`, two new integration suites and `test_payload_reads.py` untracked. `answers.py`, `fact_values.py`, `execution.py`, `routes/facts.py`, ci-gates.yml, all trackers, the KG and the evidence runs are modified but not committed. `origin/main` = `fa8fc1d` (PR #43), which still has:
  - the member-value mismatch (no `MEMBER_VALUE_MISMATCH` check in `FactAnswerPolicy.canonical_value`);
  - the 128-character canonical decimal bound;
  - the NULL-permissive `ck_fact_slot_identity`.
  On `main`, the trackers already declare F0007 Done from the superseded run `b94cfa12`.
- **Impact:** "Done" is true only in one local working tree. Anyone branching from `main` (F0008, F0013 and F0017 depend on F0007) builds on the defective identity and answer contract. Losing the working tree loses the remediation. The approved run's evidence also cites a branch head that does not exist as a commit.
- **Owner / mitigation / target:** Operator + PM. Commit the remediation on `fix/f0007-review-remediation`, open a PR, and let CI run the expanded F0007 PostgreSQL step. Merge before any F0008/F0013/F0017 build starts. Proposed target: 2026-11-12, subject to owner acceptance.

### FR-L1 — Low — `FactAnswerReader.scope_read_keys` is now production-dead and encodes the removed pattern
- **Evidence:** `engine/packages/brain-factslots/src/brain_factslots/answers.py:134`. It has no production caller; only `test_factslots_unit.py:464-497` uses it. It re-selects the answer separately from the payload, which the remediation deliberately removed from both read paths.
- **Impact:** A future caller could reintroduce the scope-race that FR-M1 of review `8b8456df` reported. **Owner:** Backend. Remove it or fold it into `scope_keys_for_value`. Not blocking.

## Completion Checks

- **Requirements (PM):** six stories and 39 ACs are checked Done. README, PRD, STATUS, REGISTRY and ROADMAP agree on Done / Archived (the earlier stale "Not Started" entries are fixed). ADR-0077 is still Proposed; see plan review PR-M1.
- **Architecture/KG (Architect):** migration 0013 requires the full legacy-or-v1 shape `IS TRUE`, scans under `ACCESS EXCLUSIVE`, refuses malformed rows without repairing them, and its downgrade restores 0012 verbatim. 0012 is unchanged. KG `--check-symbols` and `--check-drift` pass, and 0013 has a KG node (`kg-source/nodes/migrations/f0007-identity-guard.yaml`).
- **Code (Code Reviewer):**
  - Member identity: `answers.py:104-110` rejects a MEMBER PRESENT value whose `member_key` under the pinned contract differs from the stored key. Unit and HTTP tests cover entity, name and identifier, including equivalent spellings that canonicalize the same.
  - Decimal: `fact_values.py:161-170` bounds the canonical length arithmetically before expansion, and input and output share the 64-character limit. Probed `0e±999999999`, `-0`, 64-digit, `10E+62` and `1E+0063`: all are correct and bounded.
  - Read authorization: `execution.read(additional_reads=…)` mirrors the existing `mutate` pattern. It derives scope keys from the exact loaded payload and decides, rechecks and audits all keys in one unit of work. Route and service both use it.
  - Ruff and mypy are clean (42 source files).
- **QE:**
  - Independent reruns: 227 unit tests (domain, factslots, security) pass.
  - All 157 tests across the CI F0007 PostgreSQL step's suites plus `test_payload_reads.py` pass against local `brain-postgres`, with no skips.
  - The new suites are wired into `ci-gates.yml`. The brain-security tests run in the existing step at `ci-gates.yml:84`.
- **Security:** scope-artifact READ is enforced server-side on both GET `/facts/{id}` and `AuthorizedFactSlots.read_answer`. Denial returns the non-disclosing 404. Name reads expose no scope or evidence. No secrets or config changes.
- **DevOps:** not run (see RUN_DEVOPS).

## Validation Evidence

FR2 via `run-gate.py --action feature-review --stage FR2`: `validate-feature-evidence --stage closeout`, `validate-trackers`, KG `--check-symbols`, KG `--check-drift` and `validate_templates` all exit 0 (lifecycle-gates.log). The story-index regeneration produced no diff. Independent test and lint commands are listed above, run on 2026-11-10 against the working tree.

## Artifact Trace

Raw sources read:
- `engine/apps/api/src/brain_api/routes/facts.py`
- `engine/packages/brain-security/src/brain_security/execution.py:350-460`
- `engine/packages/brain-factslots/src/brain_factslots/{answers,service,names}.py`
- `engine/packages/brain-domain/src/brain_domain/fact_values.py:130-175`
- `engine/migrations/versions/0012_*.py:55-110`, `0013_f0007_identity_guard.py`
- the archived F0007 folder, the ADR-0077/0039/0066 status lines, and the 81798e61 `evidence-manifest.json`

Earlier review runs `8b8456df`, `7c8e8461`, `23c712fe` and `da962864` were used only as leads. Every disposition above was re-verified against raw source and fresh test runs.
