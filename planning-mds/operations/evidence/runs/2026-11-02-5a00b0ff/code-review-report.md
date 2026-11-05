# Code Review Report — F0006 assertion plane, origin and interpretation basis

- Run: `2026-11-02-5a00b0ff`
- NEBULA_PRODUCT_ROOT: `/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain`
- Reviewer: Codex / independent Code Reviewer (`/root/g3_code_review`)
- Review date: 2026-11-03T23:05:25.994357+00:00
- Review boundary: local feature G3; tracked and untracked implementation plus current-run evidence.
- Open findings: critical=0; high=0; medium=0; low=0.
- Resolved findings: high=1 (`A-IMPL-01`) and medium=1 (`SEC-04` / `A-IMPL-02`), independently re-reviewed here after repair.

## Reviewed Files

The review used the actual working tree, not only `git diff`. Canonical delta artifacts are
[tracked.patch](artifacts/diffs/tracked.patch) and [added-files.patch](artifacts/diffs/added-files.patch);
the source-fingerprinted inventory is
[changed-production-lines.json](artifacts/coverage/changed-production-lines.json).
All 20 production hashes matched the final reviewed files. The broader changed engine and Neuron snapshot also includes packaging, locks, tests and fixtures.

- `engine/apps/api/src/brain_api/errors.py`
- `engine/apps/api/src/brain_api/routes/facts.py`
- `engine/apps/api/src/brain_api/routes/reviews.py`
- `engine/apps/worker/src/brain_worker/document_delivery.py`
- `engine/migrations/versions/0011_f0006_assertion_semantics.py`
- `engine/packages/brain-assertions/src/brain_assertions/__init__.py`
- `engine/packages/brain-assertions/src/brain_assertions/admission.py`
- `engine/packages/brain-assertions/src/brain_assertions/eligibility.py`
- `engine/packages/brain-assertions/src/brain_assertions/normalization.py`
- `engine/packages/brain-assertions/src/brain_assertions/ports.py`
- `engine/packages/brain-assertions/src/brain_assertions/service.py`
- `engine/packages/brain-contracts/src/brain_contracts/assertions.py`
- `engine/packages/brain-contracts/src/brain_contracts/dispatch.py`
- `engine/packages/brain-domain/src/brain_domain/assertions.py`
- `engine/packages/brain-persistence/src/brain_persistence/assertion_models.py`
- `engine/packages/brain-persistence/src/brain_persistence/assertions.py`
- `engine/packages/brain-persistence/src/brain_persistence/models.py`
- `engine/packages/brain-persistence/src/brain_persistence/repositories.py`
- `engine/packages/brain-security/src/brain_security/execution.py`
- `engine/packages/brain-temporal/src/brain_temporal/commit.py`

I also reviewed the modified package/workspace metadata and lockfile changes,
the three packaged new schemas and preserved v1 contract, the new admission,
contract, normalization and eligibility unit tests, the PostgreSQL assertion
integration modules, including the new authority-projection tests, the independent retained-source fixture harness, and the
changed authorization tests/temporal fake repository. Existing review, fact,
persistence and Neuron worker/recovery regressions are represented by their
observed execution artifacts; this is not a claim to have manually re-reviewed
every unchanged file in those suites.

Requirements were read from all five story files, the approved assembly plan
including correction-basis/persistence rework, raw schema contracts,
ADR-0075 and SOLUTION-PATTERNS. The changed feature STATUS remains In Progress;
this report does not mark stories Done or grant final signoff.

## Validation Artifacts

| Artifact | Observation relied on |
|---|---|
| [g3-sec04-regression.xml](artifacts/test-results/g3-sec04-regression.xml) | Final replacement engine run: 306 tests, zero failures/errors/skips. |
| [g3-sec04-focused.xml](artifacts/test-results/g3-sec04-focused.xml) | 25 PostgreSQL projection/current-consumer cases pass; includes nine new projection/denial/corrupt-chain cases and overlaps the 306. |
| [g3-basis-boundary.xml](artifacts/test-results/g3-basis-boundary.xml) | Two explicit basis-boundary cases pass; zero canonical effects after admission and one only after a separately authorized commit. |
| [g3-evidence-tamper-final.xml](artifacts/test-results/g3-evidence-tamper-final.xml) | 17 PostgreSQL migration cases pass; overlaps the 306. |
| [g2-neuron-importer-isolated.xml](artifacts/test-results/g2-neuron-importer-isolated.xml) | 15 current importer cases pass. |
| [g2-neuron-recovery.xml](artifacts/test-results/g2-neuron-recovery.xml) and [g2-neuron-postgres-second.xml](artifacts/test-results/g2-neuron-postgres-second.xml) | Five SQLite crash points pass; initial five PostgreSQL skips are replaced by five passing PostgreSQL cases. |
| [g2-existing-content-worker-postgres.xml](artifacts/test-results/g2-existing-content-worker-postgres.xml) | Five existing content-worker PostgreSQL cases pass. |
| [g2-lint-complete.log](artifacts/test-results/command-output/g2-lint-complete.log) and [g3-carrier-fix-lint.log](artifacts/test-results/command-output/g3-carrier-fix-lint.log) | Container lint checks passed before and after the integrity repair. |
| [coverage-report.md](coverage-report.md), [changed-code-summary.json](artifacts/coverage/changed-code-summary.json) | 1,170/1,266 changed executable lines, 92.4171%, no instrumentation gaps. |
| [architect-implementation-review.md](architect-implementation-review.md) | Independent second implementation review; repaired findings and source hashes recorded. |
| [test-plan.md](test-plan.md) and [test-execution-report.md](test-execution-report.md) | All 35 ACs mapped to concrete assertions, with synthetic/native-format limitations and failed historical attempts retained. |

I independently parsed the final XML totals, checked the 20 source fingerprints,
compared the packaged/authored schemas, confirmed the v1 DTO/schema remain
byte-identical to HEAD, and independently recomputed the changed-line coverage
union from raw engine coverage and existing importer JSON. Runtime tests and lint were executed in the
application containers by the owning roles; I relied on those artifacts and
reviewed their test bodies rather than claiming an independent full rerun.
The parent subsequently executed the optional basis probe in the existing
application container; its two passing cases and observed effects are recorded
in g3-basis-boundary.xml and its raw command log. The initial interrupted shell
attempt supplies no additional runtime evidence or outstanding permission block.
All review commands are recorded in [commands.log](commands.log).

The framework's separate generic G0 scan-staging and G2 Markdown-artifact parser
repairs have their own passing 45-test evidence. They repair evidence handling,
not product behavior, and are excluded from the 306 product-test count.

## Severity-Ranked Findings

No unresolved production finding was confirmed in this review.

### A-IMPL-01 — high — resolved

Location: `engine/migrations/versions/0011_f0006_assertion_semantics.py:252`
(the deferred verified-evidence comparison).

The original guard omitted page/bbox equality between inserted
`assertion_evidence` rows and retained server selectors, allowing a direct INSERT
to retain conflicting display coordinates despite the UPDATE immutability guard.
The approved mirror/correction invariants require those fields to agree.

The repaired SQL uses null-safe page equality and JSON bbox equality that treats
SQL NULL and JSON null as the same absent coordinate. I reviewed the repaired
predicate and the independent test bodies: four changed/absent page/bbox cases
must raise PostgreSQL CheckViolation with unchanged authoritative row counts;
three honest/regionless SQL-null/JSON-null cases must commit successfully.
The final 17-case migration XML and 306-case replacement regression XML pass
without skips. Earlier red/intermediate runs remain historical evidence rather
than being relabeled as success. This closes the finding.

### SEC-04 / A-IMPL-02 — medium — resolved

Original locations: `brain_persistence/assertions.py:492`,
`brain_persistence/repositories.py:189` and the canonical guard's full-lineage call.

The initial source-key callbacks called full ORM lineage resolution before the
source READ decision. This materialized assertion values, semantic records and
review evidence in the session even though returned-payload authorization was
enforced. That violated the approved metadata-only discovery boundary.

The repaired `SourceDiscovery` / `discover_sources`
(`brain_persistence/assertions.py:578` / `:583`) select only assertion/evidence/
review linkage IDs, ancestry and contract discriminator. All three read/commit/
review source callbacks use these column projections. The direct canonical
guard validates its current session/transaction proof and staged READ audit
before loading full lineage, then verifies its source set matches discovery.
Missing/cyclic/overlong assertion ancestry fails closed.

I reviewed both changed production files and all nine new PostgreSQL test
cases in `test_assertion_authority_projection.py`. Captured SQL must exclude
assertion values, the semantic table, review evidence and corrected payloads
during four discovery paths, denied internal read and direct commit without
proof. Three corrupt-chain cases also retain zero effects. The focused 25-case
XML and full 306-case regression XML pass with zero failures/errors/skips,
and final source hashes/coverage cover this repair. SEC-04 is closed, with no
deferred implementation waiver.

The metadata-only all-legacy return preserves the documented pilot boundary.
Internally consistent foreign legacy references were already in that boundary;
owner-inconsistent child/parent rows are prevented by migration 0006's composite
foreign keys. Missing/cyclic/overlong linkage still refuses. No supported,
migration-valid legacy regression was identified.

## Non-Blocking Recommendations With Owner/Follow-up

None arising from unresolved Code Reviewer implementation defects. The
separate [Security Review](security-review-report.md) owns its residual scan/
dependency recommendations; this verdict supplies no acceptance of them. The existing G7 graph
publication and future PR ownership requirements below remain workflow
obligations; they are not represented as completed work or accepted waivers.

## Vertical-Slice Completeness

The delivered slice is the approved internal path: strict candidate/result
contracts → authorized immutable-source admission → scoped append-only
claim/reference/name/evidence/review persistence → existing review/correction
and canonical-commit guards → PostgreSQL/HTTP/legacy regression evidence.
The automatic result importer remains v1-only. There is no new UI, HTTP assertion
route, grant, model call, live open producer, alignment execution, writer-default
change or conversion/OCR path in admission.

Admission preserves claims and outcomes; it creates no canonical facts.
Grounding a quote does not validate the business value. F0016 owns durable
drop/time/run adoption, F0018 full provenance/commit orchestration, F0022 display
and F0066 open extraction/alignment. These are explicit delivery boundaries,
not missing parts of this feature's approved slice.

## AC / Test Adequacy

The concrete per-AC mapping is [test-plan.md](test-plan.md). I traced each of
its 35 rows to the relevant implementation and examined the new behavioral
tests, including negative effects, fresh-session reload, current consumer entry
points, real PostgreSQL constraints and independent fixture expectations.

| Story | ACs | Code-review verdict | Main assessed behavior |
|---|---:|---|---|
| F0006-S0001 | 7 | PASS | Lossless typed dimensions, independent competing claims/confidence, current authority and scoped ownership, additive correction/immutable evidence. |
| F0006-S0002 | 7 | PASS | Open/typed shapes and local references, strict explicit version dispatch, unchanged v1 behavior, no open canonical use. |
| F0006-S0003 | 8 | PASS | Versioned deterministic normalization/original ranges, all reason/outcome families, name ownership, time checks, honest native/coarse evidence and zero rejected effects. |
| F0006-S0004 | 6 | PASS | Independent mood/open/described restrictions, qualified actual origins, operative-policy versus embedded-condition boundary, source authorization before protected errors. |
| F0006-S0005 | 7 | PASS | Legacy import/recovery and corrections, mandatory current canonical guard, mixed/unknown/correction lineage, atomic retry and guard-preserving migration/rollback. |

The tests assert observable retained records, canonical-effect counts and stable
errors, rather than just reproducing helper internals. PostgreSQL test databases
are owned throwaways; the fixture overrides the historical shared-DB cleanup.
Source snapshots/native locators are independently authored synthetic
development evidence; they do not qualify conversion/OCR/model accuracy or a
frozen release evaluation. The supplied time-reference port is scoped test
support, not a delivered F0016 resolver.

A potential basis-only review concern was resolved against the governing source:
master-blueprint §11 (`master-blueprint.md:843`) says governance policy decides
whether INFERRED/AMBIGUOUS needs review before canonicalization. The approved
assembly plan's review hook and eligibility table (`feature-assembly-plan.md:272`
and `:283`) retain existing confidence/provenance handling and existing commit
policy; they add no basis-only mandatory-review rule. Admission writes no
canonical fact. A separately requested, currently authorized COMMIT with source
READ/proof is the existing governed mutation, not automatic acceptance by
admission or confidence. Basis is retained through storage and v2 correction.
The independent Architect records the same source interpretation; no new
acceptance policy was introduced. The observed two-case probe confirms that
admission creates zero canonical effects for high-confidence INFERRED/AMBIGUOUS
claims; a separate authorized COMMIT creates one.

## Architecture Compliance

| Review dimension | Assessment |
|---|---|
| Correctness and logic | Strict input/output validation, source-derived evidence, explicit partial outcomes, atomic item savepoints and transaction-wide infrastructure failure propagation are consistent with the approved contract. |
| Clean architecture | I/O-free domain carriers; source/repository ports in application packages; SQL/content adapters in persistence; existing API/worker composition. No application import of the Neuron runtime or new transport boundary. |
| SOLID | Admission, normalization, eligibility, authorization and persistence have distinct roles. The larger persistence adapter groups the related infrastructure seams without moving policy evaluation into the API. |
| Test quality and coverage | The AC map and final PostgreSQL/current-consumer proofs support the changed behavior; source-bound coverage exceeds the 80% floor. |
| Error handling | Authorization/infra failures propagate and retain failure audits; ordinary model-item rejects remain typed outcomes. Unauthorized sources produce non-disclosing 404 before stable authorized 422 eligibility errors. |
| Performance | Pure admission caches verified blocks per batch; document locks/name keys bound contention. Lineage is cycle-checked and limited to 256 ancestors. No new latency SLO is claimed. Full-bundle source verification remains an infrastructure cost to assess with future producer scale. |
| Readability and naming | Names and docstrings explain the source/truth distinction and non-obvious normalization, same-UoW and rollback decisions. No blocking naming/style issue found. |
| Acceptance mapping | All five stories and 35 ACs traced; no unimplemented required UI or producer activation inferred. |
| Over/under-engineering | Additive tables/envelope and required guard are justified by immutable v1 compatibility. No speculative orchestration/runtime framework added. |

The mandatory guard is called by CanonicalCommitService before register/end/fact/
outbox effects. It resolves full evidence/review/correction ancestry and rejects
incomplete mixed v2 lineage. Its source proof is a current-session/current-
transaction object backed by staged READ audit rows, not a request boolean.
The authorization facade obtains source READ and mutation decisions in the same
unit of work and rechecks authority; it does not nest a committing read facade.

v2 corrections preserve basis, kind/mode, subject/object identity, property/
release, source phrase, qualifiers/mood and time snapshots. Children receive
fresh identities/evidence and reviewer metadata; changed locators are grounded
again. v1 correction's existing EXPLICIT basis behavior remains the specifically
approved legacy boundary. The guarded occupied downgrade preserves v2 evidence.

### Graph, tracker and publication boundary

KG lookup/hint was used for routing before code-body reads. `diff-impact.py HEAD`
reported affected nodes:

- `capability:bitemporal-canonical-commit`
- `capability:durable-authorization-decisions`
- `capability:parse-once-content-artifact`
- `capability:runtime-roots-and-toolchain`
- `entity:content-artifact`

That tracked-diff command omits new untracked files; the explicit 20-file
inventory and added-files patch supplied that scope. New-service `--defines`
lookups and the FactCommitRepository `--implementers` lookup lacked current
symbol edges, so raw source was checked: the production repository and temporal
test fake implement the mandatory guard.

Risk scores were recorded for those five nodes, semantic-interpretation-run,
all three F0006 capabilities and four assertion entities. Scores range 0–6;
none reaches the high/critical bands. The recorded parse-once hotspot is rank 1
(score 6); semantic-interpretation-run is rank 4 (score 4). The independent
Architect review covers the changed production implementation and supplies
second-review evidence. Raw test artifacts resolve the graph's planning-only
test-gap counts; current importer/recovery regressions cover its co-change
partners without enabling them.

The primary owner `gajapathi.kannan@live.com` has not acknowledged a PR.
SKILL's bus-factor and hotspot clauses explicitly concern the PR. No PR exists
at this local G3 boundary. Attach independent review evidence and obtain the
separate owner acknowledgement before PR approval/merge. This report does not
fabricate it or substitute the Architect review for it.

G7 still owns authored as-built bindings, symbol/decision regeneration and
validation; no KG file was edited by this reviewer. The feature remains active/
In Progress with five stories and no archive transition. Final tracker
reconciliation, story provenance, closeout and archive/path-sensitive checks
belong to their later gates and have not been claimed here. ADR-0065/0075 status
is not promoted by this code review.

## Coverage Verification

Independently recomputing the intersection of the final changed-line inventory
with the union of raw executed/missing lines produced **1,170/1,266 =
92.4171%**, matching the refreshed machine summary. The QE-owned coverage-report.md
records the same final denominator when its prose refresh is complete. All 20 source
fingerprints matched; missing instrumentation is empty. This exceeds the active
80% threshold without waiver.

The earlier whole assertion-surface measurement of 906/1,000 (90.6%) is
historical evidence with a different denominator; it is not the refreshed
SEC-04 changed-code result. The final 96 missed changed statements remain
listed per file; line coverage is not branch
coverage, model accuracy or proof of every possible failure path.

## Result

APPROVED

This is the independent Code Reviewer's local G3 verdict. It supplies no PM
acceptance, user approval, PR approval, final story signoff or deployment/
production qualification.
