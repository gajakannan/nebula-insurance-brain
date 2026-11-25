# Security Review Report — F0009-provenance-and-human-correction-lineage run 2026-11-24-08701e37

Reviewer: Claude (Opus 5.5) / Security Reviewer
Date: 2026-11-24

## Scope

This review covers the internal provenance reader and its metadata-first discovery, the opt-in `prepare_reads` facade change, the review-boundary refusal attribution and learning reservation, migration 0016's guards, and the contract bundle additions. It does not cover F0018 row-level security or role remediation (a pre-existing handoff), or a public provenance API (none exists; F0020 owns it).

## Reviewed Surfaces

`brain_security/execution.py`, `brain_persistence/provenance.py`, `brain_provenance/service.py`, `brain_persistence/repositories.py`, `brain_review/decisions.py`, `brain_api/routes/reviews.py`, `brain_api/schemas/review.py`, `migrations/versions/0016_f0009_provenance_hooks.py`, the four new schemas, and the F0009 test suites.

## Threat Boundary

The reader runs in-process and is not routed. Its threats are an authorized caller using it to:

- read protected source content without current READ on that source;
- infer the existence or topology of another tenant's or KB's lineage;
- obtain a partial graph after a denial.

The review route's threats are reviewer spoofing, audit loss on refusal, and fabricated reservations.

## Auth / Authz

- **READ before materialization.** The anchor is decided first. Then discovery (column-only selects, so no protected payload enters the identity map) produces every content-artifact, review-task and fact-slot requirement. All of them are decided and locked in the same unit of work before `materialize`. One denial refuses the whole result.
  - Proven: a denied source means zero loads (`test_denied_prepared_source_means_zero_protected_loads`, `test_denied_source_means_zero_materialize_calls`).
  - Proven: a revoked grant refuses old history (`test_revoked_grant…`, `test_current_grant_governs_a_historical_coordinate`).
  - Proven: one denied ending/attestation source refuses exactly the dependent lineages (`test_ex_prov_004…`).
- **Expiry during load is rechecked** even without `additional_reads` (`test_expiry_during_the_load_is_rechecked_without_additional_reads`).
- **Root association is proven structurally.** A fact version needs its own slot anchor; an assertion needs a review-task or artifact anchor on its own chain. Arbitrary, foreign or wrong-kind anchors give the same non-disclosing outcome as an unknown root (`test_unknown_inaccessible_and_mismatched_anchors_are_indistinguishable`, `test_cross_kb_anchor…`). CR-L1 now proves the association before any closure expansion.
- **The review route** keeps `review_task:annotate` plus source READ. The reviewer comes from the verified principal only; a submitted `reviewer_principal_id` gives 422. The service principal cannot annotate (404, zero effects).

## Validation

- **Query shape:** `ProvenanceQuery` is parsed for shape only and validated against the installed portable schema before any read.
- **Results:** validated against `provenance-result-v1` (native profile) inside `load`, after authorization and before the audit commit. A failure gives `LineageUnavailable`, with no partial graph.
- **Reservations and attempts:** validated against their installed schemas before staging.
- **Database guards:** they re-verify every link (decision, item, original, child, reviewer, UTC instant, matching annotate authorization). Direct-SQL challenges are refused even under the elevated test role (`test_f0009_migration.py`).

## Audit / Logging

- **Durable audit.** Every read, denial and failure is a durable authorization decision under the existing F0002 facade. Each refused request adds one `review_submission_refused` event whose payload holds only the attempt id and outcome.
- **No leakage.** The refusal 422 body and the denial exception text contain no submitted values. Logs captured during denied reads contain no protected values (`test_revoked_grant…`, `test_ex_prov_004…`, `test_competing_correction…`).
- **No silent rollback.** The reservation-failure and source-drift paths persist a `failed` authorization audit.

## Secrets / Config

There are no new secrets, environment variables or credentials. Evidence artifacts redact the local development database credentials. gitleaks found 0 leaks in the 107 changed files.

## Scan Disposition

| Class | Result | Disposition |
|---|---|---|
| dependency | clean (engine 75, neuron 171, experience 0 advisories) | none |
| secrets | clean | Framework follow-up: the filesystem mode of `check-secrets.sh` needs `--no-git` for gitleaks ≥ 8.19 (README) |
| sast | 4 × `avoid-sqlalchemy-text` in migration 0016 (lines 297/320/332/334) | **False positive.** The interpolated values are module-level constant table, constraint and trigger names, with no external input. This is the same pattern as shipped 0014/0015. Accepted as informational by Security. |
| dast | 0 fail / 0 warn / 119 pass | none; the HTTP surface is unchanged |

## OWASP Top 10 Coverage

- **A01 Broken Access Control:** addressed. Conjunctive current-authority checks on every linked resource; non-disclosing refusal; structural anchors.
- **A03 Injection:** all queries are parameterized SQLAlchemy. Migration identifiers are constants.
- **A04 Insecure Design:** append-only lineage. A refused attempt never becomes a replay key (PR-H1). The deferred constraint prevents an unreserved effective correction.
- **A05 Misconfiguration:** SECURITY INVOKER functions with a fixed `search_path`.
- **A08 Integrity:** owner FKs, immutability triggers, and a marker that historical rows cannot acquire.
- **A09 Logging:** durable audit on every path.
- **A10 SSRF:** none, because v1 evidence locators are never fetched.

A02, A06 and A07 are unchanged by this feature (dependency scan clean).

## Findings

- Critical: none.
- High: none.
- Medium: none.
- Low: none open. CR-L1 was closed during code review.

Known pre-existing boundary (not a new finding): the application connects with an elevated database role, and row-level security is F0018's. The F0009 guards do not depend on it, as proven by tests running under the elevated role.

## Recommendation Disposition

No open recommendation needs PM acceptance. The two operations notes are recorded in deployability-check.md and README.md and are not findings: data-only restores need `--disable-triggers`, and the framework gitleaks flag.

## Result

Result: PASS
