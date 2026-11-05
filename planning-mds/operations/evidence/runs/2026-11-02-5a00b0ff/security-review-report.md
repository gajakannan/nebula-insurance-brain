# Security Review Report — F0006 assertion-plane-origin-and-interpretation-basis run 2026-11-02-5a00b0ff

## Scope

- Feature ID: F0006
- Run ID: 2026-11-02-5a00b0ff
- Date: 2026-11-03
- Reviewer: Codex / independent Security Reviewer
- Product root: /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain
- Assessment: **PASS WITH RECOMMENDATIONS** for the bounded feature G3 review. G4 operator approval and named PM acceptance of the bounded dispositions were subsequently recorded at 2026-11-04T02:37:42.390119+00:00 in [gate-decisions.md](gate-decisions.md#g4-operator-approval-recorded); this does not resolve the technical findings or grant production qualification/producer activation.
- Disposition refresh: 2026-11-04 (UTC), after reading the actual approval record and passing G4 validation output.
- SEC-05 disposition refresh: 2026-11-05 (UTC), after independent caller/source checks and the completed G7 evidence review.

Reviewed the approved five stories/35 ACs, Phase B assembly plan and correction amendments, ADR-0062/0075, authored and packaged contracts, all security-relevant changed production code, existing consumer integrations, raw scans, and current source-bound runtime evidence. The current 20 production Python hashes in artifacts/coverage/changed-production-lines.json match disk. The initial scan snapshot covered 44 source/config/test paths; final post-repair secrets/SAST and current API DAST supersede their earlier outputs. No production files, gates, manifest, STATUS, or KG projections were changed by this reviewer.

The feature adds an authorized internal v2 assertion seam and additive persistence. It adds no public assertion route, permission grant, live producer, model/conversion call, or deployment target. direct-baseline and the v1 writer remain the defaults. The external package version/source set in neuron/uv.lock is unchanged relative to HEAD; internal brain-assertions dependency edges do change. Inherited risks remain reportable despite that unchanged exposure.

## Reviewed Surfaces

- brain_assertions admission, normalization, eligibility and authorized write/read service.
- brain_contracts strict JSON/schema/version dispatch and versioned claim/outcome contracts.
- brain_persistence assertion/reference/name/semantics models, source ownership, replay, correction ancestry, current-transaction source proof, and migration 0011.
- AuthorizationExecution.mutate additional READ decisions; existing fact-commit and review-decision routes and importer.
- Existing PDF conversion/parser entry points and runtime configuration to triage dependency reachability; no new parser benchmark or exploit execution.
- Synthetic local Compose validation, JUnit/coverage, source scans and anonymous OpenAPI DAST. Production deployment, UI, live extraction, F0016 durable drops/time store, and F0018 complete provenance orchestration remain outside this feature.

## Threat Boundary

| Actor / entry | Asset / operation | Control and residual boundary |
|---|---|---|
| Granted service principal / internal admit | Immutable source blocks → candidate assertions, references, evidence and review hooks | INTERPRET facade and staged audit precede source-port loading; context/run/document ownership checked; atomic write |
| Untrusted model candidate | Quotes, selectors, names, origin, mood and eligibility | Strict candidate schema; server derives selectors/origin/restrictions; model selectors and confidence grant no authority |
| Reviewer / existing correction route | Original claim → appended correction child | ANNOTATE plus current source READ; stale/duplicate rules retained; inherited semantics and original evidence remain immutable |
| Service / existing commit route | Attributable evidence/review ancestry → canonical fact | COMMIT plus current source READ in one UoW; session/transaction-bound proof; guard before commit registration or range changes |
| Unauthorized caller | Source existence, quotes and semantic restriction reasons | Primary/source denials precede operation and remain 404; authorized eligibility refusal is sanitized 422 |
| Local converter / PDF input | Worker CPU, memory and parser process | Existing PDF signature restriction and supervised deadline reduce some exposure; SEC-01 remains |

STRIDE assessment: spoofing is controlled by existing verified principals/current grants and server context; tampering by immutable source verification, composite FKs and append-only/deferred constraints; repudiation by atomic durable authorization/review/commit audits; disclosure by source authorization and sanitized errors, with SEC-04's pre-authorization materialization repaired; denial of service by deterministic admission/replay and existing worker controls, with inherited parser memory exposure in SEC-01; elevation of privilege by independent source READ, annotation/commit separation and conjunctive eligibility guards. No new authority is accepted from model flags, client actor fields or supplied eligibility booleans.

## Auth / Authz

Internal admission uses content_artifact:interpret through AuthorizationExecution before SqlAlchemyAdmissionSources reads/verifies stored bytes. _current_audits (assertions.py:103) checks actor/action/owner/success audit in the current PostgreSQL transaction using xmin; lock_context checks the run/artifact/document owner before grounding. Cross-artifact candidate evidence is rejected before the source port.

The mutation facade (execution.py:389) authorizes/rechecks the primary action, discovers sources, authorizes deduplicated READ keys, combines audits, rechecks, and invokes the operation with one commit. There is no nested read() committing the mutation. Foreign/revoked/expired source, callback failure and audit failure tests confirm no effect. Authority locks retain ADR-0062's linearization boundary.

The commit guard (assertions.py:815; brain_temporal/commit.py:133) resolves attributable evidence, review decisions and correction ancestry; cycles, owner mismatch, mixed unknown v2 references and conflicting review/evidence ancestry refuse use. SourceAccessProof is server issued, object-identity and session-transaction bound, exact-source scoped and backed by current staged decision IDs. Copied and transaction-stale proofs fail. Direct v2 application callers without this path fail. Legacy-only unregistered UUID behavior is explicitly retained by the approved contract; it cannot qualify v2 evidence and is not claimed as complete F0018 provenance enforcement.

Open/mood restrictions dominate confidence, mode and review. DESCRIBED-only support needs review for initial use and remains unable to close/supersede; unqualified/unresolved evidence cannot clear that restriction. Qualified OCR/TRANSCRIBED evidence retains actual precision/confidence. Corrections preserve kind, identity, property/release, qualifiers/mood, basis and ancestor restrictions; changed locators are re-admitted against the same authorized source. v1 corrections retain their explicitly approved EXPLICIT compatibility behavior.

HTTP tests exercise source denial as non-disclosing 404 before authorized ASSERTION_INELIGIBLE 422, application/problem+json, no quote/mood excerpt and zero canonical effects. No new permission rows or grants were added. SEC-04 is resolved: discover_sources uses Core column projections only for all three pre-READ discovery paths; the direct guard checks current READ authority before full semantic resolution. SEC-05 records the original KG caller-map gap and its verified G7 reconciliation, with precise static-analysis limitations retained.

## Validation

decode_json rejects duplicate keys, non-finite numbers, invalid UTF-8/Unicode and non-JSON Python values. Offline packaged JSON Schema 2020-12 validation forbids unknown candidate properties and uses a registry that refuses remote retrieval. Explicit dispatch accepts absent version as legacy and exact integer 2 as v2; null/bool/string/other explicit versions fail without fallback. The existing automatic importer explicitly refuses v2 before mutation.

Typed records require predicate/release; open records require source phrase, mandatory evidence and EXPLICIT basis with null predicate/release. Scoped subject/object/time declarations, introducing names and quote presence are checked. Server normalization retains original text and conservative selectors; repeated/multiregion support cannot manufacture a unique span. Grounding intentionally does not verify the business meaning of a misread value.

Migration 0011 adds composite owner FKs, discriminator/confidence checks, record/carrier consistency, append-only evidence/extensions/references/names, correction invariants and deferred evidence completeness. Occupied downgrade refuses and retains v2 semantics. Architect finding A-IMPL-01 is **resolved**: evidence page uses null-safe exact equality and bbox compares JSON-normalized nulls to the server snapshot (migration lines 244–247). Four tampered page/bbox insertion cases now refuse while three honest/absent-region cases pass; the focused migration suite has 17 passes and the final combined engine suite has 306 passes, including the later SEC-04 regressions. UPDATE immutability alone was not treated as INSERT-integrity proof.

## Audit / Logging

Authorization allows commit with mutation effects; denial/failure rolls back effects and records a fresh failure audit. Audit failure prevents content/success release. Review decision and canonical audit/outbox behavior remains in the existing transaction. Per-item raw hash, reason, model/prompt identity and excerpts are protected outcome data; no new general log/metric of quotes or model responses was introduced. F0006 returns outcomes but does not claim F0016 durable-drop persistence or full-run completion.

## Secrets / Config

Final gitleaks reported zero results over the recorded source scope. No new production secret, token transport, identity provider or remote integration was added. Local synthetic runtime configuration is not evidence of production secret-store or TLS readiness. Existing committed non-secret defaults remain unchanged. The project-wide secrets/data-protection planning gap is SEC-02.

## Scan Disposition

All four manifest classes ran with resolvable raw artifacts; no class is waived. The reviewer interpreted existing executed container evidence rather than silently substituting a host scanner.

| Class | Ran | Result / finding summary | Artifact |
|---|---|---|---|
| dependency | Yes | Engine 0 advisories; Neuron 85 advisory records over 8 packages; SEC-01 | artifacts/security/dependency-summary.json; dependency-engine.json; dependency-neuron.json |
| secrets | Yes | 0 results; 222 gitleaks rules | artifacts/security/secrets/secrets-gitleaks-20261103-230114.sarif |
| sast | Yes | 0 results; 151 Semgrep rules over 20 changed production Python files | artifacts/security/sast/sast-semgrep-20261103-230114.sarif |
| dast | Yes | Fresh API runtime: 16 OpenAPI entries imported, 59 URLs, 112 PASS rules, 0 FAIL; one Low warning category over 2 public responses; informational client errors 43/session identification 1 | artifacts/security/dast/api-scan-sec04.json; api-scan-sec04.html |

DAST was anonymous. Protected routes mostly returned client errors; its absence of active findings does **not** prove authenticated authorization, mutation semantics or source isolation. Actual service/HTTP/PG suites supply those narrower controls, including 404-before-422 and failed-effect counts. Session identification is informational, not evidence of session theft. Final source scans follow both page/bbox and SEC-04 production repairs; final DAST follows the API runtime rebuilt after SEC-04; its actual exit 2 is the retained Low warning, not an execution failure (artifacts/test-results/command-output/sec04-dast.log).

The additional role-required strict planning audit actually ran in engine-validation and exited 1. Raw output: artifacts/test-results/command-output/g3-planning-security-audit.log. An earlier reviewer attempt hit Docker socket permissions and the approval was interrupted; it did not execute a scanner. The parent's completed existing-container audit supersedes that tooling limitation. Its failure is retained as SEC-02.

Dependency triage below counts raw records without pretending they are distinct exploit paths. certifi repeats one ID twice; Docling and docling-slim overlap upstream defects. Internal workspace packages are skipped by pip-audit because they are not PyPI packages; changed internal code has manual/SAST/test coverage, not an invented external advisory assessment.

| Package / records | Description, preconditions and scoped disposition |
|---|---|
| pypdf 6.21.2 / 7 | PDF xref/dictionary/page-tree memory amplification and encrypted page-count, labels, missing-trailer or clone loops. PdfReader and page traversal are actually called by DoclingAdapter on accepted PDF bytes. Deadline does not cap allocation. Realistic inherited High risk, SEC-01; scan lists fixes through 6.21.4. |
| pillow 12.3.0 / 39 | Includes memory corruption/disclosure on particular TIFF/JPEG/JP2 or multiframe decode/encode paths, APNG/BMP/GIF/XBM resource exhaustion, plus narrower font, Arrow, EPS/Ghostscript, PDF-append and Windows paths. Default-open issues cannot be dismissed universally. F0006 admission performs none of these operations; the specific malformed-image route through existing PDF conversion and bundled codecs is not established by these tests. Patch/qualify conversion dependencies; no claim that all 39 are unreachable or Critical. Listed fix: 13.0.0. |
| docling 2.126.0 / 8 and docling-slim 2.126.0 / 7 | Table-span and archive-detection resource exhaustion, local-image JSON disclosure, remote-fetch SSRF/credential forwarding, configured KServe policy gap, installed-plugin import and optional Tectonic file/shell access. Existing converter permits PDF and checks leading %PDF- before either parser, reducing non-PDF/archive/HTML/JSON/LaTeX routes. Remote fetching/headers, KServe, Tectonic and malicious installed plugin preconditions are not introduced/enabled by F0006. Detection-before-format checking is why allowed_formats alone is insufficient. Listed fixes 2.131.0/2.132.0; retain patch work under SEC-01. |
| certifi 2026.7.22 / 2 | Compromised intermediate chain trusted by old CA bundle: on-path attacker with a compromised CA key can impersonate HTTPS destinations. F0006 does no remote fetch; this is an inherited outbound TLS/build-download risk, not an authorization bypass. Advisory recommends 2026.10.19+ and image rebuild. |
| aiohttp 3.14.3 / 8 | Server request memory/CPU/FD exhaustion, idle connection handling, pure-Python parser smuggling/scheme spoofing, and client cookie/pool weaknesses need the affected server/parser/cookie usage. Brain API is FastAPI/uvicorn; no changed aiohttp server or shared-cookie path was found. Not established as an F0006 reachable exploit; patch to listed 3.14.4 and verify actual consumers. |
| filelock 3.32.6 / 13 | Local lock-directory/name/marker/SQLite side-file races and Windows ACL/oplock issues require relevant lock classes plus hostile writable/shared directories or Windows behavior. No new locking surface is added. Local cache ownership remains a deployment precondition; patch to a release covering the relevant set (scan generally lists 4.2.1; one earlier fix is 4.0.9), then check compatibility. |
| setuptools 84.0.0 / 1 | Windows legacy install-as-egg metadata path issue requires malicious wheel plus that Windows install path. Linux application-container feature tests do not exercise it. Build/supply-chain hygiene carryover; listed fix 84.1.0. |

## OWASP Top 10 Coverage

| Category | Status | Notes |
|---|---|---|
| A01 Broken Access Control | OK in reviewed scope | Current server authority/owner/proof/eligibility enforced; SEC-04 repair and SEC-05 G7 caller reconciliation verified; graph limits disclosed |
| A02 Cryptographic Failures | Inherited risk | SEC-01 certifi preconditions; no new cryptography |
| A03 Injection | OK in changed scope | Parameterized ORM/static SQL; strict JSON; model selectors not executable authority; no new command execution |
| A04 Insecure Design | OK in bounded scope | Claims remain separate from truth; no producer activation; legacy completeness boundary disclosed |
| A05 Security Misconfiguration | Issue | SEC-03 public nosniff header; local proof is not production hardening |
| A06 Vulnerable / Outdated Components | Issue | SEC-01 real inherited advisories, not a clean dependency result |
| A07 Identification & Authentication | OK / unchanged | Existing verified-principal path; no identity/token changes |
| A08 Software & Data Integrity | OK | Immutable verified source and hashes, replay, composite/deferred guards; A-IMPL-01 repaired |
| A09 Security Logging & Monitoring | OK with planning gap | Atomic durable decisions tested; SEC-02 global documentation incomplete |
| A10 Server-Side Request Forgery | No new path | Offline schema retrieval; inherited optional Docling remote-fetch preconditions retained in SEC-01 |

All ten role dimensions were assessed: injection, authentication, access control, data exposure, configuration, component risk, auditability, secrets, abuse/resilience and safe failure. The tables above identify their evidence and limits. No new HTTP admission rate limit is claimed; the service is internal and deterministic, while parser resource exhaustion is an explicit component concern.

## Findings

Open grouped findings: **Critical 0; High 1; Medium 1; Low 1.** These counts are review findings, not advisory-record counts. Resolved A-IMPL-01, SEC-04 and SEC-05 are excluded from open counts. No unresolved implementation blocker remains in the reviewed source. The three open recommendations are explicitly non-blocking/deferred for the accepted trusted local synthetic-fixture scope under the named PM dispositions below. SEC-05's required G7 reconciliation and precise limitation disclosure are complete.

### SEC-01 — High: inherited PDF parser and conversion dependency exposure

Location: neuron/uv.lock:3035; neuron/packages/brain-ingestion/src/brain_ingestion/docling_adapter.py:49, :109, :137; existing conversion_process.py and run-local Compose configuration. Raw advisory authority: artifacts/security/dependency-neuron.json.

What/why: pypdf 6.21.2 is directly used to open and walk accepted PDFs before/after Docling. CVE-2026-119209, CVE-2026-119207 and CVE-2026-119204 describe potentially large allocations; the remaining pypdf findings add CPU/loop exposure. The existing PDF-only guard excludes other formats, not malicious PDFs. A supervised 300-second process deadline bounds duration but is not a memory ceiling. The reviewed Compose configuration declares no per-worker memory limit; no equivalent current memory containment evidence was supplied.

Exploit scenario: an attacker whose PDF reaches an existing authorized ingestion flow supplies a crafted xref/dictionary/shared-resource PDF. Parsing consumes substantial memory before the watchdog deadline; without effective process/container memory isolation, the converter or host/co-resident workloads can become unavailable. This is conditional on document ingestion, not anonymous access to the new internal assertion seam. No malicious-PDF exploit was executed and no RCE is asserted.

Remediation: update and qualify pypdf to a fixed compatible version (scan: 6.21.4+) and address the other seven dependency packages using the precondition table; rebuild images and rerun conversion/worker recovery plus raw dependency scans. Add tested memory/CPU/process isolation for untrusted conversion rather than relying on wall-clock timeout. Preserve PDF magic and offline/remote-fetch restrictions. Owner: AI Engineer + DevOps, with Security verification. Accepted follow-up target: 2026-11-10, and before untrusted or production PDF ingestion. Tracking: SEC-01 in this report; preproduction conversion-security carryover.

Accepted bounded G4 mitigation: **trusted local synthetic fixtures only**. Remediate/qualify affected conversion dependencies and verify memory/CPU/process isolation before untrusted or production PDF ingestion. Keep the reviewed pipeline/writer defaults and producer boundary. The operator explicitly approved the quoted mitigation; Codex / Product Manager recorded the named SEC-01 acceptance in [gate-decisions.md](gate-decisions.md#named-pm-recommendation-acceptances). SEC-01 remains an **open High technical finding**, deferred and non-blocking only within that accepted local scope. The acceptance is neither a remediation claim nor a dependency waiver or production activation.

### SEC-02 — Medium: inherited project security planning audit fails

Location: planning-mds/security/; raw g3-planning-security-audit.log. Missing threat-model.md, data-protection.md, secrets-management.md, owasp-top-10-results.md and reviews directory; strict parser does not recognize the current authorization-review.md Status format. The document contains a Draft status semantically, so a parser-format failure must not be represented as absent status knowledge.

Why/scenario: security design, deployment assumptions and ownership remain fragmented, increasing the chance a broader release overlooks a trust boundary or secret/data lifecycle obligation. The feature-local threat/control/scan review here reduces this bounded review gap but does not create the missing global artifacts.

Remediation: Security and Architect complete the authored baseline artifacts, normalize required metadata, and rerun the strict audit. Owner: Security + Architect; accepted follow-up target 2026-11-10 / before production security qualification. Tracking: SEC-02. Codex / Product Manager explicitly accepted this non-blocking local feature carryover in [gate-decisions.md](gate-decisions.md#named-pm-recommendation-acceptances), because these existing global documents are outside approved F0006 implementation scope. The strict audit remains failed and the Medium finding remains open.

### SEC-03 — Low: public responses omit X-Content-Type-Options

Location: final ZAP alert 10021, public health/OpenAPI responses (2 instances). Missing nosniff permits avoidable MIME interpretation behavior in clients; the scanned responses are public JSON, and no script/content injection exploit was demonstrated.

Remediation: set X-Content-Type-Options: nosniff consistently at the response/proxy boundary and verify public/error/protected responses. Owner: Backend Developer + DevOps; accepted follow-up target 2026-11-17. Tracking: SEC-03. Codex / Product Manager accepted this non-blocking local feature hardening follow-up in [gate-decisions.md](gate-decisions.md#named-pm-recommendation-acceptances). The Low finding remains open; the anonymous DAST limitation remains unchanged.

### SEC-04 — Medium, resolved: discovery originally materialized protected payloads before READ

Original location: brain_persistence/assertions.py resolve_lineage, repository discovery methods, and brain_assertions/service.py internal read discovery. Full ORM loads made assertion values and semantic/evidence JSON available before source READ. No current returned-content exploit was demonstrated, but this violated the approved IDs/owners-only discovery boundary and required repair within F0006.

Verified repair: new frozen SourceDiscovery/discover_sources (assertions.py:578/:583) uses column projections of evidence assertion/artifact IDs, review-decision linkage, review-item assertion ID, and assertion parent/discriminator. It never selects the semantic table, values, review evidence or corrected payloads. Commit/review/internal-read discovery all use it. Direct require_commit_sources validates the session-bound proof and current-transaction READ audits before calling full resolve_lineage, then checks discovered/full source equality and integrity/ownership; the all-legacy branch exits without loading protected claim rows. Cycles, missing assertions and excessive depth fail closed.

Proof: engine/tests/integration/test_assertion_authority_projection.py captures real PostgreSQL SELECTs for four discovery paths, denied internal read, direct commit without proof, and missing/cycle/overlong ancestry (9 cases). Forbidden assertion values, semantic-table reads and review payload projections are asserted absent. artifacts/test-results/g3-sec04-focused.xml has 25 passes with existing consumers; g3-sec04-regression.xml has 306 passes including the new nine. No failures, errors or skips. Owner: Backend Developer. Disposition: mitigated in source and independently reviewed; no deferred risk acceptance needed.

### SEC-05 — Low, resolved: KG authorization caller reconciliation verified at G7

Original finding: the required mutate callers lookup returned an empty set despite real facade callers in the fact/review routes and AssertionWriteService. The Low finding concerned retrieval-map coverage, not a demonstrated missing authorization check.

Completed evidence: [kg-reconciliation.md](kg-reconciliation.md#sec-05-authorization-caller-reconciliation--resolved) records PASS. The final [G7 gate output](artifacts/test-results/command-output/g7-gate-final.log) records status pass and all three ordered operations: compile, symbol/decision regeneration and checks, then drift validation. The manifest records kg_reconciliation PASS. The [caller artifact](artifacts/test-results/g7-authorization-callers.json) contains 15 mutate callers: **four production methods** (AssertionWriteService.admit/read, facts.commit_fact, reviews.submit_review_decisions) and **eleven test methods**. They are not fifteen production entry points.

Security independently reran the exact mutate callers lookup and obtained the same 15 IDs. A separate source search confirmed all **seven read/mutate facade call sites**: facts.py:75/:133, reviews.py:101/:175, and brain_assertions/service.py:111/:129/:140. The [manual source inventory](artifacts/test-results/g7-authorization-source-callers.json) records these call sites and fingerprints; Security independently verified all seven entries against the current three source-file hashes. The [reference audit](artifacts/test-results/g7-symbol-reference-audit.json) reports zero unknown caller/callee IDs across 1,785 symbols. Commands and outputs are retained in commands.log.

Precise caveat, verified against scripts/kg/symbols.py: files are assigned to their first claiming canonical node; Python bare instance-call names use same-node fallback. Imported module/class-qualified calls have additional resolution, but injected or untyped instance receivers do not gain full type inference. The unbound-file sidecar skips unresolved local-instance calls rather than guessing from bare names. Closures, Protocol dispatch, property access and framework-driven calls are not exhaustively modeled. Same-node matching can over-link names; therefore the map is a retrieval aid, not exhaustive reachability, runtime authority or complete test coverage. The reviewed manual call inventory and existing PostgreSQL authorization/projection/denial tests remain the behavioral authority.

Disposition: **resolved through actual G7 reconciliation plus the precise documented static-analysis limitation**, independently checked by Security. Architect owned the follow-up; the historical G4 PM acceptance remains in gate-decisions.md. SEC-05 is no longer an open recommendation and needs no further risk acceptance. No runtime code change or scanner/test rerun was needed for this evidence-only closure.

## Recommendations

The three remaining recommendations, SEC-01/02/03, are **accepted, non-blocking/deferred only for the trusted local synthetic-fixture feature scope**. Their original severities are retained. Each has an owner, follow-up and named PM acceptance in the actual [G4 record](gate-decisions.md#g4-operator-approval-recorded). SEC-05 is closed by the independently verified G7 evidence above; its historical acceptance is retained in the gate record.

- [high] SEC-01: accepted bounded mitigation restricts feature use to trusted local synthetic fixtures; qualify/remediate affected conversion dependencies and verify memory/CPU/process isolation before untrusted or production PDF ingestion; target 2026-11-10; PM acceptance: Codex / Product Manager, gate-decisions.md, Named PM Recommendation Acceptances — owner: AI Engineer + DevOps (Security verifies); follow-up: SEC-01
- [medium] SEC-02: accepted non-blocking local carryover to complete global security artifacts and rerun the strict audit, target 2026-11-10 and before production security qualification; PM acceptance: Codex / Product Manager, gate-decisions.md, Named PM Recommendation Acceptances — owner: Security + Architect; follow-up: SEC-02
- [low] SEC-03: accepted non-blocking local hardening follow-up for nosniff across public/protected/error responses, target 2026-11-17; PM acceptance: Codex / Product Manager, gate-decisions.md, Named PM Recommendation Acceptances — owner: Backend Developer + DevOps; follow-up: SEC-03

The approval source is the operator's actual message, **"yes i am approvingf with the message you mentioned"**, recorded at 2026-11-04T02:37:42.390119+00:00. Its quoted reference was:

> Approve F0006 with SEC-01 mitigation: trusted local synthetic fixtures only. Before untrusted or production PDF ingestion, remediate affected dependencies and verify resource isolation. Owners: AI Engineer + DevOps, with Security verification; target November 10, 2026.

Named PM: **Codex / Product Manager**, under that explicit operator approval. The gate record separately accepts SEC-01's bounded mitigation and the SEC-02/03 routine carryovers; its SEC-05 acceptance is historical because that follow-up is now complete. [G4 validation output](artifacts/test-results/command-output/g4-approved-validation.log) records status pass and exit 0. The actual G4 record remains the acceptance source for the three open recommendations.

SEC-04 and A-IMPL-01 are mitigated in source with observed PostgreSQL proof; SEC-05 is resolved by verified G7 reconciliation. All three are excluded from open counts. SEC-01 remains open High; its accepted mitigation is scope containment, not demonstrated parser remediation/resource isolation. No dependency waiver, broader deployment approval or primary-owner PR acknowledgement is inferred.

## Per-Story Security Assessment

| Story | Verdict | Security basis and limits |
|---|---|---|
| S0001 AC1–7 | PASS | Scoped authorized writes, independent dimensions/confidence, append-only correction/evidence and composite-owner rejection; real PG proof |
| S0002 AC1–7 | PASS | Strict typed/open/version contract, offline schemas, legacy-reader refusal, scoped references and no canonical eligibility |
| S0003 AC1–8 | PASS | Authorization before source-port inspection; server grounding/selectors, protected outcomes, zero model/conversion/canonical effect; SEC-04 lineage discovery minimization is repaired and verified |
| S0004 AC1–6 | PASS | Independent mood/open/described restrictions and inherited basis/evidence; sanitized authorized versus unauthorized error behavior |
| S0005 AC1–7 | PASS | Existing importer/review/commit and PG rollback/recovery preserved; current source proof and repair verified; SEC-04 minimal-projection/direct-guard repair and real SQL-projection proof verified |

All 35 ACs have concrete mappings in test-plan.md; these judgments evaluate their security aspects and do not replace QE functional acceptance. Final g3-sec04-regression.xml has 306 passing cases; g3-sec04-focused.xml has 25 overlapping cases and g3-evidence-tamper-final.xml has 17 overlapping migration passes; do not sum them. Additional 15 importer passes, SQLite five crash points, PostgreSQL five crash points, and five actual-OCR worker cases are recorded separately. Changed executable-line coverage is 1,170 / 1,266 = 92.4171% with 20 matching production hashes and no waiver. The native-format/time examples are synthetic trusted fixture proof, not live parser quality, producer activation, frozen evaluation or production qualification.

## Result

**PASS WITH RECOMMENDATIONS** for the bounded feature review and accepted trusted local synthetic-fixture scope. All five story security assessments remain PASS. A-IMPL-01 and SEC-04 are resolved with source-bound PostgreSQL proof; SEC-05 is resolved by completed G7 caller reconciliation and independently verified source/static-analysis evidence. Open technical findings are **Critical 0, High 1, Medium 1 and Low 1**: SEC-01, SEC-02 and SEC-03.

The operator approved the quoted SEC-01 mitigation, Codex / Product Manager explicitly accepted the three remaining recommendations in [gate-decisions.md](gate-decisions.md#named-pm-recommendation-acceptances), and actual G4 validation passed. These recommendations remain non-blocking/deferred only within that recorded bounded scope, with severity, owner, follow-up and named PM acceptance retained. Untrusted or production PDF ingestion still requires dependency remediation/qualification and verified memory/CPU/process isolation. SEC-01 remains an open High technical risk; no production or new producer activation is granted.
