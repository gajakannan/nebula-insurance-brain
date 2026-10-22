# Security Review Report — F0004-content-artifact-model run 2026-10-17-8a6cc79f

## Scope

- Feature: F0004, approved assembly plan and S0001–S0004.
- Run: 2026-10-17-8a6cc79f. Review date: 2026-10-20.
- Reviewer: Codex, independent Security Reviewer role.
- Environment: current uncommitted Python worktree and run-scoped application validation containers. This is a bounded local feature review, not production qualification, user approval, implementation signoff, or acceptance of Proposed ADR-0073/0060.
- Scope includes every runtime/operations surface in `artifacts/diffs/changed-files.txt` ; including new untracked modules. No UI, public mutation route, new grant, canonical write, or production Graph activation is included. `content.v2_writer_enabled` remains false. The existing candidate worker still requires explicit operator activation.

Inputs: evidence README, action-context, manifest, approved feature assembly plan and four stories, implementation-decisions, test-execution-report, coverage-report, solution patterns, ADR-0061/0062/0073, existing security planning index/authorization review, raw four-class security scans, selected actual test output and current source. The final post-fix evidence records engine 229 passing/0 skips, neuron 93 passing/4 optional inference-tokenizer skips, restore 4 passing, and changed-runtime coverage 2371/2617 = 90.60% across all 44 measured changed runtime files (engine 91.97%, neuron 88.58%, ops 84.40%). The extra PostgreSQL table-index proof passed separately before the refresh and is covered in the refreshed engine lane; it is not added again. Exact refreshed artifacts: `artifacts/test-results/g3-engine-regression.txt` ; `g3-neuron-regression.txt` ; `g3-restore-regression.txt` ; `g3-current-coverage-threshold.txt` and `artifacts/coverage/changed-runtime.json`. These are evidence reviewed, not Security independently rerun full-suite totals; the independent bounded security probes are identified below. Optional live inference/tokenizer skips do not qualify a production model or Graph activation.

## Reviewed Surfaces

API authentication dependencies, both content GET routes, shared async authorization facade, sync current-authority worker reads/publication, queue fence, fallback receipts, ingestion source/converter/projection, immutable stores and version dispatch, date verifier ports/service, PostgreSQL indexes/ownership/history triggers, operator sweep/backfill/repair/reconciliation, run outputs/import and local backup/restore. Dependency locks and actual installed Docling configuration/plugin inventory are included.

## Threat Boundary

Assets: private PDF/native/text/image bytes; exact manifests/hashes and indexes; tenant/KB/source/version/artifact/run identity; classifications/source ACLs/current grants; date candidates/selection history and human receipts; job lease generation; durable decision/mutation audit; backup snapshots and operator credentials.

Actors: external document supplier; verified tenant member; Reviewer without content-member authority; ingestion ServicePrincipal; delegated executor/acting principal; trusted operator; installed dependency/plugin author; storage/database administrator. The document supplier remains untrusted even when a trusted operator submits the document. Host administrators, installed code and injected verifier implementations are trusted deployment authorities, not identities authenticated by checksums.

| Subject → boundary → resource/operation | Control and residual risk |
|---|---|
| Bearer caller → API → manifest/file | Verified issuer/audience/signature/time claims → stable principal → current locked authority → trusted resource owner → verified bytes/indexes → durable audit → response. Denial is non-disclosing 404; no object lookup occurs on denied content access. |
| Document supplier → trusted enqueue/worker → parser | Current ingest/interpret authority, scoped retained source hash and deterministic identities. Exact initial PDF signature now rejects archive/PDF polyglots before either parser. SEC-H1 was independently reproduced and then closed by a focused source guard/recheck. |
| Worker → queue/authority → filesystem + readiness DB | Generation fence and current ingest decisions cover original and deterministic fallback resource. Files/intent may survive rollback, but no ready row or payload is published from an orphan. Authorized retry must reverify. |
| Reader/operator → DB indexes + filesystem | Indexes are pointers, not alternate text authority; full byte and owner comparison, same-artifact composite FKs, immutable history and explicit operator repair. Normal failed reads only record their failed decision. |
| Date producer/human integration → trusted verifier port → date history | Default human/source verifiers deny. Returned human receipt must bind exact version/value/precision or candidate/previous-selection command; current ingest decision and referenced-content authority still apply. Hashes/DTO validity do not establish human authority. |
| Interpreter/importer → retained run → downstream records | Run marker validates tenant/KB/artifact/run and hashes; actual content is currently authorized; importer checks task/source/profile identity. Current worker emits null date selection until an authoritative producer exists. No canonical acceptance follows from a parse or candidate date. |
| Operator → backup/Docker/database → isolated restore | Explicit quiesced window; before/after inventory; required lock/schema/DB/content files; safe extraction; fresh container and directory; owner/index/date/audit/citation checks. Docker socket is a privileged operator-only test surface; checksum manifests do not authenticate an adversarial backup. |

STRIDE assessment:

| Category | Threat/precondition/impact | Controls, gap and mitigation |
|---|---|---|
| Spoofing | Forged bearer, actor IDs or schema-valid human receipt could impersonate an authority. | API uses OIDC verification and governed principal resolution; worker actor comes from trusted submitter/current authority; human/source ports deny by default. Preserve this trust boundary when F0022 supplies a producer. |
| Tampering | Changed content, swapped owner/index/run/date reference, stale lease or modified fallback count could alter evidence. | Strict contracts, exact hashes, scoped metadata, record inventory checks, append-only DB guards, fenced publication and command-bound intent. Filesystem/DB administrators remain trusted; unkeyed receipt/backup hashes detect inconsistency, not hostile administrator replacement. |
| Repudiation | Failed or unauthorized operation could leave effects without attributable audit. | Decisions staged in same transaction for mutations; fresh failure audit after rollback; audit failure prevents effect/payload; mutation/state/repair events reference the successful decision. PostgreSQL fault tests cover commit/expiry/mid-unit failures. |
| Information disclosure | Cross-tenant/KB/source access, cached private files, native resource URI fetch or remote OCR could disclose documents. | Current scope checks, manifest allowlist, URI closure, private/no-store/nosniff responses, local observed RapidOCR and PDF-only conversion. No claim of TLS/encryption/production monitoring qualification. |
| Denial of service | Adversarial source may exhaust parser memory before allowed-format enforcement. | SEC-H1 reproduced, fixed and independently rechecked. General PDF CPU/memory quotas and authenticated download rate limits are not production-qualified by this feature; F0005/F0026 own wider operational qualification. |
| Elevation of privilege | Reviewer, old grant, backup metadata, parse provenance or date candidate could gain ingest/canonical authority. | Existing permission catalog only; independent membership/restriction/delegation checks; current grant reload; no public date mutation; human default denial; no canonical writes. Package/plugin installation is trusted code deployment, not restricted by `allow_external_plugins=False` on this pinned Docling version. |

## Auth / Authz

No permission is added. `content_artifact:read` protects both GETs (`engine/apps/api/src/brain_api/routes/content.py:58` ; `:83`). The facade reloads the active policy, principal revisions/grants/delegation and server-hydrated owner (`brain_security/execution.py:179`); its read/mutate paths audit before return or atomically with effects (`:355` ; `:388`). Mutation success staging at `:415` is transactional and does not grant authority independently.

The synchronous source reader (`engine/apps/worker/src/brain_worker/content_access.py:48`) verifies the accepted artifact's tenant/KB/source against the lease and rechecks before returning. Publication (`content_publication.py:139`) validates both the lease resource and deterministic fallback pair, obtains current ingest authority for both, verifies queued source/recipe identities, rechecks before storage and readiness, then commits decision/indexes/event through the original queue fence. Operator operations use the same `decide`/`recheck` path under current ingest authority (`brain_persistence/content_operations.py:97`); global uniqueness reconciliation explicitly requires authority for every affected artifact (`:158`).

Actual route tests cover Reviewer without TenantMember, other tenant/KB, revoked grants, exact versioned bytes and corrupt reads (`engine/apps/api/tests/test_content.py:269` ; `:303` ; `:365` ; `:382` ; `:403`). PostgreSQL tests cover expiry after marker, current denial before object writes, orphan/repair failure and owner FKs. These tests supplement the passive unauthenticated DAST; that scan does not establish authenticated route safety.

KG routing was performed before broad implementation reads. `--callers-only` was executed for actual symbol IDs for `AuthorizationExecution.read` ; `mutate` ; `execution.decide` ; `execution.recheck` and `evaluation.evaluate`. It returns empty callers for read/mutate/evaluate and only old async callers for decide/recheck; `artifacts/test-results/g3-current-authority-callers.txt` also retains the decide query. Exact missing current paths are recorded in SEC-L3. Raw-source review establishes enforcement for this pass; graph coverage is not a substitute for it.

## Validation

Strict schema and integer-version dispatch reject unknown versions, extras, duplicate JSON keys/nonfinite values, unsafe file names, missing/extra inventory, hash/size mismatch, unresolved native refs, local/external URI assets, invalid Unicode spans/geometry, cross-artifact cells/continuations and cycles. See `brain_content/validation.py:92` ; `:118` ; `:167`; `verified_store.py:31`; packaged contract proof in `artifacts/test-results/g2-wheel-schema-deployment-proof.txt`. Dynamic database inputs use bound SQLAlchemy operations. Fixed migration SQL and catalog-derived constraint changes have no untrusted request interpolation; the remaining suppressed SAST migration result is discussed below.

Dates validate lexical precision/calendar, exact line ordinal/hash/quote and same-version owner (`dates.py:42` ; `:281`; `document_dates.py:197`). Processing timestamps are not document dates. Human selection/clear is a separate verified decision with exact candidate/previous-selection binding, CAS and idempotency; current default verifiers cannot authorize it (`document_dates.py:120` ; `:334`). A content quote supports a candidate, not semantic proof of the proposed date and not automatic selection. Human verifier injection is a trusted service composition responsibility; a receipt SHA alone is not a signature or independent authorization.

The revised adapter checks the exact first five bytes for `%PDF-` before pypdf or Docling input handling (`docling_adapter.py:35`–`:42`). This closes the demonstrated pre-detection polyglot boundary (SEC-H1); a PDF suffix/Docling allowlist/non-strict pre-reader alone did not do so.

The date-read consistency correction identified by Code Reviewer was also rechecked: reads acquire the same document-version row FOR SHARE, while writers use FOR UPDATE (`document_dates.py:136` ; `:495`). The shared lock is held until the read decision commits, preventing a new selection from referencing a candidate missing from the earlier candidate query. `artifacts/test-results/g3-date-read-regression.txt` records eight PostgreSQL cases passing. This strengthens consistency without changing authority, grant or historical-selection semantics.

## Audit / Logging

Decision audit carries actor/delegate, resource/action, policy hash, grant revision, scope, reason, trace and outcome. `ContentArtifactRepository.authorization_audit` checks decision UUID, allowed/succeeded, actor, ingest action, resource and scope rather than treating any audit UUID as permission (`content_repository.py:170`). One publication mutation event is deterministic; normalized content/date/index rows are append-only. State timestamps originate in PostgreSQL. Error paths sanitize internal integrity/unavailability details and do not mutate readiness/quarantine during reads.

Fallback intent is private immutable producer diagnostics, bound to source/version/artifact/owner/recipe/bundle plus count, written under fenced authority (`publication_intent.py:54`). It is deliberately not served by content routes. Its SHA verifies consistency; it neither authenticates an untrusted writer nor confers permission. Audit and immutable storage assume protected DB/filesystem administration; cryptographic external audit anchoring, retention/deletion and production alerting are not established here.

## Secrets / Config

Three raw secrets results are empty arrays, covering engine/neuron/scripts. No newly exposed credential or token logging found. OIDC keys remain supplied by trusted issuer/JWKS configuration; PyJWT is now 2.15.0 in both locks. Worker/ops connections use existing local environment/config boundaries. Committed `brain:brain` credentials in local Compose/backup/restore are the existing synthetic local database convention, not a discovered production credential; the restore copy is transient. This evidence does not qualify that convention for deployment.

The writer flag validates an actual boolean and defaults false (`brain_content/config.py:21`); Graph candidate still needs `BRAIN_ENABLE_GRAPH_CANDIDATE=1`. Safe YAML loading is used. The operator-only restore job's Docker socket gives host-level Docker authority and must remain outside normal API/neuron role deployment. Backup confidentiality/access control and production key rotation/TLS remain broader deployment responsibilities.

## Scan Disposition

All four manifest classes ran through framework wrappers/application jobs. No waiver is assumed. The implementation lead refreshed source SAST after review fixes (`artifacts/test-results/g3-current-source-sast.txt`: 569 targets, zero unsuppressed/blocking findings). Security did not duplicate the four scan classes. A bounded process-local source probe and post-fix recheck were necessary because recorded configuration alone did not settle archive reachability.

| Class | Ran | Result / finding summary | Raw evidence |
|---|---|---|---|
| dependency | yes | Engine clean; neuron 15 advisory records on docling/docling-slim 2.126.0, representing 8 unique vulnerability families. The demonstrated High path (SEC-H1) is now closed by source input validation; other preconditions assessed below. All advisory records remain present in the lock. | `artifacts/security/dependency-engine.json` ; `dependency-neuron.json`; installed format/plugin evidence `artifacts/test-results/g2-docling-reachability-runtime.txt` |
| secrets | yes | Zero leaks in all three scoped outputs. | `artifacts/security/secrets-engine.json` ; `secrets-neuron.json` ; `secrets-scripts.json` |
| sast | yes | No unsuppressed blocking results. SARIF retains one in-source suppressed pre-existing `0005_tenancy_authx_expand.py:79` SQL construction audit. Its table/column values are fixed migration inventory and regex is bound; not an externally supplied identifier path. Suppression is visible, not treated as a deleted result. | `artifacts/security/sast.sarif` |
| dast | yes | OpenAPI imported 16 URLs, zero FAIL; 2 Low header classes on public `/health` and `/openapi.json` ; plus informational findings. Protected probes return 401; successful private responses are assessed through route tests/source. | `artifacts/security/dast.json` ; `dast.md` ; `zap.yaml` |

Individual dependency disposition (the first two columns identify every raw advisory record):

| docling PYSEC | docling-slim PYSEC | Family / reachability judgment |
|---|---|---|
| 2026-4194 | 2026-4209 | CVE-2026-105747 / GHSA-3cr3-8m4c-fpxw, METS gzip member-list memory exhaustion. **Initial source path reachable, now closed by exact initial PDF magic guard; SEC-H1 remediated.** Non-strict pypdf alone still accepts the demonstrated gzip/PDF polyglot; both adapter modes now reject it before detection. The dependency itself remains vulnerable if another unguarded converter path is introduced. |
| 2026-4195 | 2026-4211 | CVE-2026-105749, unbounded HTML/JATS/ODS/BoxNote table spans. Those backends are excluded by actual PDF-only converter options. No reachable span backend shown on this PDF path; revisit on format changes. |
| 2026-4189 | 2026-4212 | CVE-2026-105742, cross-origin remote-image credential forwarding. Requires HTML remote fetch/images and configured credential headers, none enabled here. PDF-only conversion excludes that backend. |
| 2026-4193 | none | CVE-2026-105746, KServe OCR ignores enable_remote_services. Actual provenance spike observes local RapidOCR, not KServe, and no caller-selected OCR endpoint/configuration is exposed. The pin does not enforce the flag if KServe is later selected. |
| 2026-4192 | 2026-4210 | CVE-2026-105745, plugin import before allow_external_plugins filtering. Runtime entry-point inventory contains only `docling.models.plugins.defaults`; no hostile plugin is presently installed. `allow_external_plugins=False` is not a security boundary in this version. Trusted/locked installation is required; future dependency changes must recheck inventory. |
| 2026-4191 | 2026-4216 | CVE-2026-105744, Tectonic TikZ file read/write/shell. No LaTeX backend, Tectonic option or shell-escape path is configured; PDF-only path excludes it. |
| 2026-4190 | 2026-4214 | CVE-2026-105743, remote-image SSRF/DNS rebinding. Requires remote fetching/rendering in excluded non-PDF backends. No such setting or document-selected remote URL fetch is present; retained native URI closure forbids external resources. |
| 2026-4208 | 2026-4213 | CVE-2026-105748, serialized native JSON local-image disclosure. JSON_DOCLING conversion input is excluded. Saved native JSON is loaded only after verified bundle URI closure, which rejects plain/file/external paths before docling-core model loading. That verified-native path is a different control from PDF allowlisting. |

The higher fixed Docling versions identified by raw advisories require provenance-hook requalification (`item_provenance.py:17` pins 2.126.0). Configuration exclusions are scoped mitigations, not patches or approved waivers. SEC-L1 tracks the retained component risk.

Planning audit is separate from the four runtime scan classes: `artifacts/test-results/g3-security-planning-audit.txt` exits 1. SEC-M1 records the real documentation debt rather than silently converting this failure into a pass.

## Ten Review Dimensions

| Dimension | Assessment |
|---|---|
| 1. Injection resistance | Bound queries/SQLAlchemy operations, fixed frozen migration SQL, safe filesystem keys, strict native references; no request-to-shell construction found. |
| 2. Authentication robustness | Existing signature/algorithm/issuer/audience/time verification precedes stable-principal and protected storage resolution (`verification.py:78` ; `deps.py:145`). No new session/password/MFA surface. |
| 3. Access control correctness | All reviewed public content entry points and production worker composition use current authority; ownership and restriction checks survive version/fallback dispatch. Graph caller index lags actual enforcement (SEC-L3). |
| 4. Sensitive data exposure | Non-disclosing denial/errors, private no-store/nosniff, no signed URL, closed native resources. No new payload/secret logging found. No production at-rest encryption/retention claim. |
| 5. Security configuration | Writer disabled, deny-default trusted verifiers, local-only operational scope. Public route header debt SEC-L2; privileged restore job explicitly operator-only. |
| 6. Component risk | Targeted PyJWT/pypdf/urllib3/multidict patches reflected in final locked builds. Demonstrated archive path SEC-H1 now closed; retained pins/configuration risk SEC-L1. Package audit is not a complete base-image/OS qualification. |
| 7. Observability/auditability | Durable decision-before-payload/effect, atomic mutation events and failed-read-only audit, DB immutability. Planning baseline and model asset provenance limitations SEC-M1/SEC-L4. |
| 8. Secrets/key management | Empty scoped leaks scans; environment/issuer boundaries preserved. Local synthetic credentials are not production provisioning; rotation/secret-store qualification remains outside this feature. |
| 9. API abuse/resilience | Fenced/retry-safe immutable effects, idempotency/CAS and exact accepted-source reuse. Parser input DoS SEC-H1 was fixed and rechecked; wider download/converter rate/resource budgets are not established by current tests. |
| 10. Error/failure safety | Corruption is 409 and never conversion/cache fallback; storage/audit unavailability fails closed; orphan/retry and restore negatives exercised; destructive downgrade refuses history. |

## OWASP Top 10 Coverage

| Category | Status | Notes |
|---|---|---|
| A01 Broken Access Control | OK, scoped | Current authority + owner + referenced resource checks; KG debt SEC-L3. |
| A02 Cryptographic Failures | Bounded | Hash integrity verified; protected admin/storage assumptions remain. No encryption/key deployment qualification. |
| A03 Injection | OK, scoped | Bound DB values and validated local paths; suppressed migration audit manually assessed. |
| A04 Insecure Design | Recommendation | Pre-allowlist input boundary SEC-H1 remediated; documentation SEC-M1 remains. |
| A05 Security Misconfiguration | Recommendation | Public header hardening SEC-L2. |
| A06 Vulnerable / Outdated Components | Recommendation | 15 retained advisory records; demonstrated SEC-H1 source path closed, SEC-L1 residual. |
| A07 Identification & Authentication | OK, scoped | Existing verification/principal model retained. |
| A08 Software & Data Integrity | Recommendation | Immutable verification/audit/fence controls hold; model asset identity SEC-L4 and trusted installation assumptions remain. |
| A09 Security Logging & Monitoring | Bounded | Durable decisions/events tested; global documentation/production monitoring not qualified. |
| A10 Server-Side Request Forgery | Mitigated, scoped | PDF-only path + native asset closure; remote fetch/render/KServe remain disabled/unselected. |

## Findings

Counts at initial review: **Critical 0, High 1, Medium 1, Low 4.** After the fix and independent recheck: **open Critical 0, High 0, Medium 1, Low 4; remediated High 1.** Low findings are grouped by control/root cause rather than double-counting duplicate advisory packages or two public URLs.

### SEC-H1 — High, remediated — Gzip/PDF polyglot reached vulnerable archive enumeration

- Location: `neuron/packages/brain-ingestion/src/brain_ingestion/docling_adapter.py:35` ; `:78` (current file; original pre-reader was at lines 72–74); locked docling/docling-slim 2.126.0. CVE-2026-105747, PYSEC-2026-4194/4209.
- What: PDF-only converter configuration applies after Docling format detection. The preceding `PdfReader` defaults to non-strict mode and accepts a gzip archive with an appended valid PDF, despite its invalid initial header.
- Why it matters / exploit scenario: an external source supplier gives an authorized operator a `.pdf` polyglot containing a compressed tar with many empty members. The trusted worker accepts its PDF suffix and pypdf pre-read; Docling sees gzip magic and calls `TarFile.getmembers()` before enforcing the count or allowed formats. Small compressed input can exhaust worker memory/CPU. The v2 flag does not mitigate the default v1 path; no public upload endpoint is required for malicious source bytes to cross this boundary.
- Evidence: `artifacts/review/mets_polyglot_probe.py` creates a 523-byte, one-member benign sample and intercepts detection before enumeration/conversion. `artifacts/review/mets-polyglot-probe.txt` records `mime application/gzip` ; pypdf accepting one page and `REACHED_METS_DETECTION_BEFORE_PDF_ALLOWLIST` through actual adapter parse. Installed source confirms eager `tar.getmembers()` in `_detect_mets_gbs`. This is reachability proof, not a memory-exhaustion test.
- Remediation: reject non-PDF magic, specifically gzip/archive inputs, on exact source bytes before any Docling detection (cover both provenance modes), with a sentinel regression proving converter/detector is never called; or upgrade/requalify the pinned converter. Do not rely on suffix, PDF allowlist, timeout, or non-strict pypdf alone. Preserve legitimate PDF and actual OCR/provenance/compatibility evidence.
- Owner: AI Engineer + Backend; target: before G3 acceptance. Status: remediated and independently rechecked on 2026-10-20.
- Resolution: `docling_adapter.py:35`–`:42` now rejects any source without initial `%PDF-` before pre-reading, provenance initialization or conversion. The new parameterized regression covers gzip/PDF, zip/PDF, text/PDF and empty input in both modes (`tests/test_docling_adapter.py:40`); real native/scanned/projection tests remain passing (`artifacts/test-results/g3-sec-h1-tests.txt`: 21 pass).
- Independent recheck: `artifacts/review/mets-polyglot-postfix-probe.txt` records the same 523-byte sample still accepted by raw pypdf but rejected by the actual fixed adapter in both provenance modes with zero reader/pipeline/converter calls. The pre-fix transcript is preserved separately. Command: `docker compose -f planning-mds/operations/evidence/runs/2026-10-17-8a6cc79f/artifacts/runtime/compose.yaml exec -T neuron-validation python /app/brain/planning-mds/operations/evidence/runs/2026-10-17-8a6cc79f/artifacts/review/mets_polyglot_probe.py --expect-rejection` (exit 0). This closes the current guarded path; it does not patch Docling or remove either raw advisory record.

### SEC-M1 — Medium — Required baseline security artifacts remain pending

- Location: `planning-mds/security/README.md:15`; `authorization-review.md:3`; `artifacts/test-results/g3-security-planning-audit.txt`.
- What: threat-model, data-protection, secrets-management and OWASP results files are absent and explicitly Pending; authorization review is an old Draft. This is substantive baseline documentation debt, not four renamed complete documents. Strict audit also fails a bold `**Status:**` formatting mismatch and expects broader `reviews/` ; whereas feature reports correctly belong in the run folder.
- Why / scenario: a later release reviewer relying on the baseline index cannot distinguish accepted local controls from unqualified deployment/retention/secret boundaries and may infer unsupported security completeness. The F0004 controls are mapped above and in the assembly plan; no new scoped runtime bypass follows from the missing files.
- Remediation: reconcile a bounded current security index, link accepted ADRs and actual feature reports; author the missing baseline artifacts with explicit local scope and deferred production items. Align audit formatting/output-path expectations without inventing project-wide acceptance. Do not mark this audit clean or add an unapproved waiver.
- Owner: Security + Architect; target: 2026-11-03, before any production-readiness claim. Follow-up: F0026 security-baseline reconciliation. Status: deferred recommendation.

### SEC-L1 — Low — Retained Docling advisories require controlled upgrade/requalification

- Location: `neuron/uv.lock`; `brain_ingestion/item_provenance.py:17`; raw dependency JSON and advisory table above.
- What: seven additional vulnerability families remain installed; present format/OCR/plugin restrictions prevent demonstrated source reachability for those families, but changes to formats/options/installed plugins reopen their preconditions. The PDF allowlist did not close SEC-H1, illustrating why these must remain individually tracked.
- Scenario: a later plugin install or remote OCR/non-PDF setting is introduced while assuming the scanner findings were fixed. Plugin import and remote-service flags in this pinned release are specifically insufficient security controls.
- Remediation: requalify hooks on a fixed Docling release; retain PDF/native-closure and exact plugin/OCR configuration assertions until then. Reassess each family when changing dependencies, formats, OCR endpoint or remote-image settings.
- Owner: AI Engineer + DevOps; target: 2026-11-03, before broader worker/format activation. Follow-up: F0005 converter dependency qualification. Status: deferred recommendation; no waiver/acceptance implied.

### SEC-L2 — Low — Public health/OpenAPI header hardening

- Location: `artifacts/security/dast.json` ; alert IDs 90004 and 10021, `/health` and `/openapi.json`.
- What / scenario: public metadata responses lack nosniff/CORP headers, leaving avoidable browser interpretation/cross-origin exposure hardening gaps. Those routes contain no scoped private document payload in the scanned surface. Private successful content responses already set nosniff and no-store.
- Remediation: apply an appropriate shared public/error response header policy and repeat targeted passive checks. Preserve required same-origin/cross-origin product behavior.
- Owner: Backend + DevOps; target: 2026-11-03, before browser/deployment activation. Follow-up: F0026 API header policy. Status: deferred recommendation.

### SEC-L3 — Low — Authorization caller graph omits current protected workflows

- Location: `planning-mds/knowledge-graph/symbol-index.yaml` caller projections; actual `routes/content.py:73` ; `:102`; `document_dates.py:332` ; `:484` ; `:541`; `content_access.py:53`; `content_publication.py:167`; `content_operations.py:109`.
- What / scenario: callers-only has no read/mutate callers and does not include the new sync decide/recheck callers. Future security blast-radius reviews could omit these workflows. Actual source invokes the controls, so this is a coverage finding, not an authorization bypass.
- Remediation: include all listed API/date/worker/operator paths and existing evaluator/facade relationships in authored KG bindings and regenerated symbol/caller projections at G7; verify the callers query reflects every protected path.
- Owner: Architect; target: F0004 G7 before closeout. Follow-up: F0004 G7 authorization caller reconciliation. Status: deferred to required gate.

### SEC-L4 — Low — OCR asset identity is not retained in execution provenance

- Location: `brain_ingestion/item_provenance.py:50`–`:51`; `content_workflow.py:123`–`:129`.
- What: observed engine class/package version is retained, while producer model/model_version are null and `model_artifact_digests` is empty. No fabricated model identity is stored, but changing model cache assets without changing package versions is not represented by these fields.
- Why / scenario: an operator investigating changed OCR output cannot use the retained receipt alone to identify exact weights or show that the same recipe used the same assets. This limits supply-chain/reproduction evidence; it does not confer canonical/human/date authority or invalidate observed engine provenance.
- Remediation: observe and persist actual OCR asset identifiers/digests in a qualified runtime, or explicitly document the unavailable asset identity and activation limitation. Code/Architect reviewers own whether current AC/ADR proof requires stronger evidence.
- Owner: AI Engineer + Architect; target: before broader v2 writer activation. Follow-up: F0005 OCR asset provenance qualification. Status: recommendation, subject to AC review.

## Recommendation Disposition

- [medium] reconcile the pending baseline security documents and strict-audit contract with bounded current evidence by 2026-11-03, before production-readiness claims — owner: Security and Architect; follow-up: F0026 security-baseline reconciliation
- [low] upgrade/requalify pinned Docling and preserve individual advisory configuration guards by 2026-11-03, before broader activation — owner: AI Engineer and DevOps; follow-up: F0005 converter dependency qualification
- [low] add shared public/error response security headers by 2026-11-03, before browser/deployment activation — owner: Backend and DevOps; follow-up: F0026 API header policy
- [low] reconcile actual authorization callers in generated KG projections at required G7 before closeout — owner: Architect; follow-up: F0004 G7 authorization caller reconciliation
- [low] qualify exact OCR model asset provenance before broader v2 activation, with AC sufficiency decided by Code Reviewer/Architect — owner: AI Engineer and Architect; follow-up: F0005 OCR asset provenance qualification

These recommendations are proposed follow-ups, not recorded human risk acceptance or completed tickets. SEC-H1 is remediated; no High/Critical recommendation is being carried into approval.

## Result

PASS WITH RECOMMENDATIONS

The demonstrated SEC-H1 path was corrected and independently rechecked; no open High/Critical finding remains in the reviewed feature surface. Medium baseline documentation debt, four Low recommendations and all 15 raw dependency advisory records remain explicit. This bounded verdict does not make the failed planning audit clean or imply production qualification, G4 approval, G5 signoff or Proposed ADR acceptance.
