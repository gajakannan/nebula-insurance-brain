# F0006 Architect Implementation Review

- Run: `2026-11-02-5a00b0ff`
- NEBULA_PRODUCT_ROOT: `/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain`
- Reviewer: Codex / Architect (`/root/g0_architect`)
- Review date: 2026-11-03T23:06:54+00:00
- Verdict: PASS
- Open findings: critical=0; high=0; medium=0; low=0. A-IMPL-01 (High) and SEC-04/A-IMPL-02 (Medium) were repaired and independently re-reviewed.
- Scope: as-built conformance and independent second review of the production contract/domain/admission/persistence/current-consumer changes.

## Independence and Sources

I authored the G0 plan-validation report and independent QE expectations/tests,
but did not author the production assertion contracts, domain carriers or their
runtime implementation. This is an implementation review separate from the G0
assembly-readiness judgment and from the parallel Code Reviewer and Security
Reviewer reports.

The approved feature assembly plan governs, including the correction-basis and
v2 correction-persistence rework approved in planning run
`2026-11-01-512e9303`. Raw ADR-0075, the authored candidate/result/admission
schemas, the current fact/review API contract, SOLUTION-PATTERNS and the G0
constraints were compared with source. Tier-2 lookup supplied routing; the
planned graph state does not override the implementation or raw requirements.

[Architect static checks](artifacts/test-results/architect-conformance-checks.json)
record the reviewed production inventory, SHA-256 values, schema comparisons,
legacy preservation and observed JUnit totals. The review covers all 20 Python
production files in the source-fingerprinted changed-line inventory, including
the additive migration and the existing authorization/temporal/API/worker
adapters. Package metadata and fixture limitations are assessed through the
existing QE and DevOps evidence rather than asserted from source coverage alone.

## Conformance Judgments

| Boundary | Source judgment and observed proof |
|---|---|
| Strict decoding and schema ownership | `brain_contracts.assertions` rejects duplicate object keys at every level, non-finite numbers, ill-formed UTF-8/Unicode and non-JSON values. JSON Schema is checked before and after adapter construction; extra fields are forbidden. Its local registry refuses remote retrieval. All three packaged schemas are byte-identical to the approved authored schemas. The 16 authored contract cases and explicit-version rejection cases pass in the final engine XML. |
| Explicit version dispatch | Missing version uses the original strict v1 schema/DTO; only exact integer `2` reaches v2. Explicit null/bool/string/float/other integers fail, and a failed reader has no permissive retry. `DocumentResultImporter` invokes `parse_legacy_result`, rejecting v2 before effects. Original `result.py` and authored v1 schema bytes match HEAD; the packaged v1 schema matches the authored source. |
| Domain and truth boundaries | Frozen I/O-free domain carriers preserve kind, mode, origin, basis, confidence, full source qualifiers and evidence as independent dimensions. Typed records require predicate/release; open statements require source wording, null predicate/release and EXPLICIT basis. Local references/name claims do not create canonical entities, facts, aliases or ontology validation. |
| Structural grounding | `f0006-grounding-v1` retains NFC/casefold/whitespace/hyphen/currency normalization with original ranges. The admission service ignores model offsets, grounds only in the trusted claimed block and preserves native selectors. Repeated/partial/noncontiguous matches retain honest coarse or unresolved precision. Quote presence never establishes value truth; competing five-million/ten-million source claims and a misread value remain independently retainable. |
| References, outcomes and missingness | Only references used by accepted claims are persisted. Introducing names, object names and scoped time-reference words are checked; an undeclared object becomes the supplied name literal with OBJECT_UNDECLARED. Per-item rejection preserves all applicable outcomes; truncated/uninterpreted output marks partial handling without claiming complete runs or NOT_FOUND. The default time resolver refuses until the future owning feature supplies one. |
| Atomic admission and replay | INTERPRET authority precedes source text. The repository verifies current-transaction audit/owner/run/artifact/document identity, locks the document, and uses per-item savepoints for name contention. Unique scoped name claims backstop races; infra/auth/audit failures escape and roll back the mutation. Admission hashes include context, source hashes and delivery identity while excluding server time. Exact replay preserves actor/time; changed identity or content refuses overwrite. |
| Correction basis and lineage | v2 corrections retain basis, kind/mode, subject/object identity, predicate/release, source wording, qualifiers/mood and time snapshots; children remain v2/HUMAN_REVIEW with inherited subject type and their own extension, evidence UUIDs and hashes. Changed evidence is re-grounded against the authorized source. Unsupported semantic changes fail before retained effects. v1 correction remains the explicitly approved version-1 EXPLICIT compatibility branch. |
| Mandatory current-consumer guard | `CanonicalCommitService` invokes the required repository guard after slot/current-range checks and before register/close/outbox effects. Resolution walks evidence, review and correction ancestry, rejects mixed unknown/corrupt v2 lineage and requires current in-memory same-session/transaction source proof plus READ audit rows. Copied and previous-transaction proofs fail. The legacy unregistered pilot UUID boundary remains explicit and cannot clear attributable v2 restrictions. |
| Conjunctive eligibility and HTTP | Open/mood restrictions dominate; only verified resolved STATED/OCR/TRANSCRIBED support clears described-only status. Described/unqualified/unresolved evidence retains review restrictions. Source READ and primary mutation decisions use one authorization unit of work with failure auditing and rechecks. A denied source remains 404 ahead of authorized stable-code 422, without protected excerpts. The existing fact/review routes and request schemas remain the transport boundary. |
| Migration and rollback | `0011` follows `0010` and adds discriminator/default plus the three planned tables, composite owner keys, enum/shape/mirror/hash checks and deferred carrier/extension integrity. Append-only guards preserve original source/evidence while allowing only the existing one-step assertion version increment. Occupied downgrade refuses rather than erasing evidence. The page/bbox INSERT-integrity omission below was repaired and its positive/negative PostgreSQL proof passes. |

## Finding A-IMPL-01 — High — Resolved

The initial deferred evidence check in migration `0011` compared identity,
artifact, block, precision, character range, ownership and document identity,
but omitted `assertion_evidence.page` and `bbox` against the retained
`verified_evidence.selector`. This violated the approved mirrored-field
invariant for newly inserted evidence. The repaired guard now compares nullable
page exactly and uses null-normalized JSON bbox equality. Real coordinates
remain exact; SQL NULL and JSON null represent the same absent bbox. This
restores the approved requirement without changing schema semantics.

Independent source re-review and
[17 passing PostgreSQL migration cases](artifacts/test-results/g3-evidence-tamper-final.xml)
close the finding: four INSERT-tamper cases reject changed/absent page or bbox
with zero effects, and three positive cases retain honest PDF and regionless
TRANSCRIBED CSV evidence with SQL NULL/JSON-null bbox. All existing migration,
immutability, correction-contract and downgrade cases also pass in that run.

The [red run](artifacts/test-results/g3-evidence-tamper-red.xml) exposed all four
expected missing-rejection failures plus two initial positive-fixture failures.
The [intermediate run](artifacts/test-results/g3-evidence-tamper-green.xml)
proved the four guard rejections but retained the fixture errors: the supposed
regionless fixture still had PDF source-location metadata. The corrected
regionless CSV/TRANSCRIBED fixture passes in the final run. Neither failed
attempt is represented as passing. The clean full replacement below verifies
the repaired source together with existing consumers.

[Runtime migration refresh](artifacts/runtime/migration-carrier-refresh.json)
records the guard deployed on the dedicated runtime database after confirming
the v2 surface was empty, with legacy row hashes unchanged.

## Runtime Evidence and Limits

[The QE AC map](test-plan.md) maps all 35 ACs; the
[execution report](test-execution-report.md) records the final 306 engine cases,
15 importer cases, ten SQLite/PostgreSQL recovery cases across separate runs,
and five existing actual-OCR PostgreSQL worker cases. Earlier focused engine
suites, including the 157-case feature subset and focused 17 migration/25 discovery-consumer cases,
overlap the 306 and are not summed. The clean replacement is
[g3-sec04-regression.xml](artifacts/test-results/g3-sec04-regression.xml),
with zero failures, errors or skips. Neuron/importer/recovery artifacts are
unchanged compatibility evidence; those lanes were not rerun for this SQL-only repair. The original recovery attempt's five
PG skips are replaced by the separate clean PG run. Initial cache/setup errors,
termination 143 and missing-env skips remain documented history.

[Changed-code coverage](artifacts/coverage/changed-code-summary.json) is
1,170/1,266 executable changed lines (92.4171%), with no instrumentation gaps
across the 20 files, from clean engine/importer inputs. This establishes the
contract floor without waiver; it does not establish insurance truth or model
accuracy. Native-format admission fixtures are independently authored synthetic
retained-source snapshots, including original non-PDF assets and PDF renditions;
they prove storage/selector handling, not new conversion or frozen-model
qualification. The framework's separate parser/security-staging regressions
are not product-test counts.

## Ownership and Publication Boundary

This report supplies an independent second Architect review of the contracts
and their semantics for the touched `capability:semantic-interpretation-run`
hotspot (current recorded rank 4). The Code Reviewer workflow separately
requires primary-owner acknowledgement on a PR when `bus_factor_flag: true`.
The recorded owner is `gajapathi.kannan@live.com`; this report supplies no such
acknowledgement. No PR/merge approval is fabricated. Attach this review to the
eventual PR and obtain the owner's acknowledgement before PR approval/merge.

The graph still has planning bindings for the new untracked source. G7 owns
as-built `kg-source/bindings/**` and node-shard reconciliation, compiled
projection/symbol/decision regeneration and drift validation. G8 owns the
archive move and path-sensitive coverage refresh. Those future publication
steps have not been represented as completed here. ADR-0065/0075 remain at their
recorded status pending the prescribed acceptance process. F0016 durable
outcomes/time/run adoption, F0018 full canonical orchestration, F0022 display,
F0066 open extraction/alignment and production activation remain outside this
feature review.

No source, schema, graph, manifest, STATUS or gate was changed by this review.

## Finding A-IMPL-02 / SEC-04 — Medium — Resolved

Security review confirmed that pre-READ source discovery called the full
`resolve_lineage` ORM loader, materializing assertion values, semantic records,
verified evidence/quotes and review-item evidence before source READ authority.
Although the decision logic needed only metadata and no returned-content
exploit was observed, this conflicts with the approved metadata-only discovery
boundary in the assembly plan's Authorization facade integration and ADR-0075
§4. A guarded commit must also validate source proof/READ authority before its
full semantic load, including direct application callers.

The implemented repair conforms to that boundary. Frozen `SourceDiscovery`
and `discover_sources` use selected identity/discriminator/correction-link
columns; they do not select ORM entities or populate claim/evidence payloads in
the identity map. Assertion read, review and commit callbacks use the same
minimal projection. Direct `require_commit_sources` validates current
same-session/transaction source proof and successful READ audit before invoking
the full semantic resolver. Missing links, cycles and chains exceeding 256
fail closed; the full resolver still enforces v2 scope, completeness,
correction/review compatibility and eligibility after authorization.

[Focused PostgreSQL proof](artifacts/test-results/g3-sec04-focused.xml) passes
all 25 cases, including nine new tests observing actual SELECT projections for
read/commit/review/review-decision discovery, unauthorized internal read,
unproved direct commit and missing/cyclic/overlong lineage. It prohibits
protected assertion values, semantic records and review evidence in those
pre-READ queries. The clean
[306-case full replacement](artifacts/test-results/g3-sec04-regression.xml)
also passes without failures, errors or skips; focused suites overlap that
execution. The current 20-source inventory matches the reviewed code; only the
two persistence implementation files changed for this repair.

The explicit all-legacy pilot behavior retains its existing source-READ
exemption for commit/review callbacks and returns without protected payload
loading. Internal assertion reads still require source READ. No supported
migration-valid owner regression was found: migration 0006
`CHAINS` (lines 69–77) and composite FK creation (lines 183–190) constrain
assertion/evidence/artifact/review owner links that the prior full resolver
defensively checked. Internally consistent foreign legacy references against a
different fact-slot scope were already within the explicit pilot boundary;
F0006 does not redefine that boundary as complete source orchestration.

This resolves the Medium finding without a policy, schema or acceptance-rule
change. A-IMPL-01 and the interpretation-basis decision remain intact.

## Interpretation-Basis Decision — 2026-11-03T14:39:22+00:00

**Decision:** Under the approved F0006 contract, INFERRED or AMBIGUOUS basis
alone does not impose a mandatory human-review gate. Its basis remains visible
and independent of confidence. A qualified typed source with no other
restriction can have `review_required=False`; that flag records the absence
of F0006's mandatory review reasons, not canonical approval or a new automatic
acceptance policy.

The controlling sources are explicit:

- [Master blueprint §11](../../../../architecture/master-blueprint.md), line 843:
  “governance policy decides whether review is required before canonicalization.”
  The preceding definition at lines 784–800 makes basis an epistemic dimension.
- [Accepted ADR-0035, Decision](../../../../architecture/decisions/ADR-0035-interpretation-basis-is-first-class.md),
  lines 20–24: preserve EXPLICIT/INFERRED/AMBIGUOUS independently of fact mode.
  This decision defines no basis-only mandatory-review rule.
- [Approved assembly plan](../../../../features/F0006-assertion-plane-origin-and-interpretation-basis/feature-assembly-plan.md),
  line 272 assigns provenance hooks and existing confidence handling; the
  eligibility row at line 283 leaves qualified STATED/OCR/TRANSCRIBED claims to
  existing policy and commit checks, with no new auto-acceptance. Line 286
  retains INFERRED/AMBIGUOUS without automatic acceptance. Lines 288–290 retain
  the bounded guarded pilot commit and defer full orchestration.
- [S0001 AC4](../../../../features/F0006-assertion-plane-origin-and-interpretation-basis/F0006-S0001-preserve-typed-source-claims.md),
  line 25 requires independent confidence/basis retention and forbids silent
  conversion to EXPLICIT or automatic acceptance. Its entry contract at line 34
  explicitly grants assertion submission no canonical approval.
- [PRD](../../../../features/F0006-assertion-plane-origin-and-interpretation-basis/PRD.md),
  line 20 requires zero canonical effects from assertion admission alone;
  lines 41–43 exclude full commit orchestration, automated deciders and new
  grants. Line 71 preserves basis independently of supplied confidence.
- [Proposed ADR-0065](../../../../architecture/decisions/ADR-0065-assertion-admission-text-origin-and-mood.md),
  lines 71–84 specifies described-only and mood restrictions, not basis-only
  mandatory review. [ADR-0075 §3–4](../../../../architecture/decisions/ADR-0075-versioned-assertion-semantics-and-admission.md),
  lines 62–72 composes those restrictions, preserves correction basis and
  requires separate current COMMIT/source READ authority in one unit of work.

Accordingly, neither confidence 0.99 nor a false `review_required` flag may
cause canonical acceptance during admission or grant an automatic producer.
An explicit later commit proposal must independently satisfy fact-slot COMMIT,
current source READ, scope/proof/lineage and all kind/mood/evidence restrictions.
Such an authorized commit is a distinct governed mutation under the existing
pilot boundary; it is not evidence that admission auto-accepted the claim or
that a human reviewed it. The full policy/orchestration obligations remain
with their approved future owners. New consumers must not interpret this flag
as authority to auto-accept.

The implementation preserves this distinction: the admission/writer path has
zero canonical mutation calls; eligibility derives the specified mandatory
restrictions, while current commit runs separately through authorization and
the repository guard. No basis-only rule is added by this review. This is a
consistent reading of plan and story, so no plan-story reconciliation or
`workstate.py decision --topic plan-story-reconcile` entry is warranted.
The parent is recording a focused behavior probe separately; this clarification
does not claim an unobserved probe result.
