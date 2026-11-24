# Independent security review working notes

Reviewer: Codex / independent Security Reviewer. Local run date: 2026-11-22.
These notes are preparatory evidence; the final verdict belongs in
`security-review-report.md` after G2 and the final scan outputs are available.

## Scope and retrieval

Canonical product root: `/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain`.
Framework root: `/home/gajap/uSandbox/repos/nebula/nebula-agents`.
Run: `2026-11-22-885e8734`; comparison base:
`bf78e111934570f83439057ea3c73a1eaefbb022`.

Read the Security role, exact report template, review action, resolved product
context, `.agentignore`, evidence README, raw feature assembly plan, PRD, all six
stories, GETTING-STARTED, STATUS, ADR-0079, solution patterns and project security
baseline. The in-progress feature has no completion latest-run pointer. Evidence
retrieval is restricted to this selected run and exact feature references.

Inspected the actual Git diff and untracked source inventory, including the new
runtime, model adapter, generated resources, JS facade, generator, consumer
guards, packaging, dependency locks and CI/build configuration. No implementation
edits were made by this reviewer.

## Completed independent checks

- Strict planning artifact audit: `security-audit.py .../planning-mds/security
  --strict`, exit 0, all required artifacts present and nonempty. The command is
  recorded in this run's commands.log.
- KG lookup for F0011 and the execution facade; callers-only queries for
  `symbol:capability-durable-authorization-decisions:authorization-execution.read`
  and `.mutate` identify `facts.get-fact` and `facts.commit-fact` respectively.
  The route implementation retains those facade calls. An initial guessed class
  symbol was absent; it was corrected using the file lookup, with no inference
  of missing authorization from that unsupported query.
- The registry checks every manifest-selected schema digest, identity, supported
  instruction/annotation and dormant reference before becoming usable. No remote
  retrieval callback can return a resource. Exposed schema/metadata views are
  detached, and runtime consumers use installed resources.
- Portable raw JSON rejects duplicate keys, nonfinite/unsafe integral numbers,
  unpaired Unicode and malformed syntax; admission is bounded. Existing native
  readers select their compatibility profile first and never retry failed input
  via another profile/version. Source-gated Pydantic validates before parsing and
  after serialization and checks for lossy changes.
- Protected source discovery/READ and established domain reasons precede the new
  normalized schema guards. Commit serialization/output checks occur inside the
  mutation callback before the facade commits. Public invariant failures use a
  generic 500 without protected payload, exception text or schema pointers.
- Existing PostgreSQL evidence has 81 tests, zero failures/errors/skips, including
  source denial/revocation, rollback and PR-L3 fault injection. Engine unit
  evidence has 1,148 tests and Neuron smoke has eight, with no failures or skips.
  These counts precede the final JS boundary corrections and must be reconciled
  against the final G2 evidence rather than reported as a final refreshed total.
- Both actual target sweeps use READ ONLY / REPEATABLE READ, fully enumerate
  canonical_fact_version without history filtering, roll back, and disclose safe
  aggregate counts only. Both local targets are empty and have QE/DevOps signed
  inventories. Separate owned-database tests contain nonempty closed history,
  legacy remainders and mapper/format failure cases. Empty live history is not
  claimed as nonempty-history compatibility proof.
- Current installed wheel/sdist evidence is PASS outside the checkout, with
  network disabled, nonroot UID 1001, installed site-packages and matching bundle
  digest `054119f11aa89c39f7687968424b9e40c63bbceadaaee145790f5908ab927959`.

## Scope correction

The original `security_sensitive_scope=false` classification is not supportable
under CONSUMER-CONTRACT section 7: this feature changes dependency/security
controls and adds validation runtimes. Reported to the orchestration owner, who
agreed to set true and collect all four required scan classes before formal G2.
This is an evidence correction in progress, not an implied scanner waiver.

## PR-L3 independent decision

Accept the bounded internal-invariant audit meaning for this feature. The
SUCCEEDED decision means current authority was checked, the exact protected
payload was read, all disclosed-source READ checks completed, and the decision
became durable. It does not assert HTTP serialization, delivery or client receipt.
No schema result creates permission, suppresses a denial or changes stored facts.

Actual fault injection in
`test_pr_l3_read_audit_precedes_safe_http_failure_and_denied_source_precedes_guard`
passed in `artifacts/test-results/consumer-integration-ci.xml`: an authorized read
has a durable succeeded audit and generic `contract_invariant_failed` 500 with no
payload/pointer; a principal denied the exact source receives non-disclosing 404
without invoking the failing response guard; business counts remain unchanged.

PR-L3 remains a Low residual semantic discrepancy and is explicitly accepted for
this bounded internal read-completion interpretation. It is not described as
fixed. No Architect redesign is required by this decision. Final release review
must retain this meaning and may not equate this audit outcome with HTTP success.

## Cross-review observations

Code Reviewer identified an exact portable depth 127/128 boundary mismatch and
the implementation owner is correcting it with common cases. Security also
identified JS caller-selected annotation pointers were more permissive than
Python schema-position selection; Code Reviewer confirmed this correctness/policy
gap and requested a fix. The selected 21 schemas do not expose a current object
annotation bypass; no live unauthorized security exploit is asserted. Both
corrections and their refreshed evidence remain subject to final review.

## Pending

Final G2 PASS, refreshed conformance/coverage/build evidence after corrections,
and raw dependency/secrets/SAST/DAST outputs with manifest-backed dispositions.

## Resumed scanner assessment — 2026-11-23

The final-timeout60 Semgrep execution summary reports 36/36 selected source
inputs scanned with 287 applicable rules, no scanner errors, no missing/unexpected
source files and one WARNING. Wrapper exit 1 is retained; this is not called a
zero-finding scan. The one warning is the dynamic `urllib.request.urlopen` at
`scripts/contracts/install_smoke.py:119`.

Independent source assessment: this is not an exploitable URL-input path in the
reviewed product. The URL is selected exclusively from the reviewed engine lock
entry matching an installed exact active package/version and compatible wheel;
its SHA-256 must match that lock entry before the wheel is staged. All 1,017
wheel URLs in the current engine lock use HTTPS `files.pythonhosted.org`.
`urlopen` uses default TLS verification; no network/request/document input supplies
the URL. This code only prepares build/test installation inputs. The actual
installation runs with network disabled, and the installed runtime schema
registry never retrieves a URL. A maintainer maliciously editing trusted lock
content is a code-review/build-trust attack, not the claimed runtime user URL
injection. Disposition: manually reviewed nonfinding; no suppression or source
edit requested.

The final secrets SARIF has 222 configured rules and zero results. Earlier
frontend audit evidence is deliberately retained: 15 advisory records initially,
then one Moderate minimatch 10.2.6 advisory after compatible patch updates.
Neither is represented as the final current lock's audit. Root subsequently
selected TypeScript-eslint 8.73.0 and minimatch 11.0.9 through existing package
ranges; final audit and frozen-install/regression evidence are pending.

Independent minimatch reachability check inspected the actual installed parser
in node-validation. The only call in typescript-estree is
`useProgramFromProjectService.js:205`, where `allowDefaultProject` configuration
patterns are matched against file paths. Current `experience/eslint.config.js`
uses the recommended rules without projectService or allowDefaultProject; user
HTTP/document input does not supply these patterns, and the dependency is dev
tooling. This assessment bounds the earlier advisory rather than waiving it as a
generic preexisting baseline issue. The current selected 11.0.9 is above the
raw advisory's patched floor 11.0.1; a fresh final audit remains required.

Initial direct resolution of the transitive parser from the package root failed
with MODULE_NOT_FOUND because pnpm does not expose that transitive package there.
It was corrected by resolving through the declared typescript-eslint package;
both commands and exits are logged, and no missing scan is inferred from it.

Independent raw DAST review: `dast/api-scan.json` and `.md` show zero High,
Medium and Low alerts, plus three Informational categories: client-error status
responses (43 instances, expected unauthenticated 401/404), non-storable protected
401 responses, and storable public `/health` and `/openapi.json` (two instances,
no protected or personalized data). These informational observations are not
security findings in this reviewed scope. The CLI summary's INFO0 is not a claim
that the raw report has no Informational observations. The raw insight reporting
99% 4xx responses confirms the unauthenticated scope limitation; authenticated
source checks, denial ordering and atomicity are established by the separate
PostgreSQL tests. No authenticated DAST coverage is claimed.

The fresh final frontend audit has now been read: `dependency/frontend.json`
contains no advisories and zero at every severity;
`dependency/frontend-execution.json` records exit 0 and unchanged lock SHA-256
`38ee91f55455c471e0632fbe9cc5901aaaa97c5adeaf52341085e1cc4be3f8e4`.
The final delta preserves the package manifest ranges and removes the vulnerable
minimatch 10.2.6 path. No frontend dependency advisory is carried forward as a
residual recommendation.

Read the corrected source for raw/scalar depth boundaries, JS schema-position
selection, the Python portable-only exact-end pattern registry and RFC8785 byte
measurement. These changes retain the native registry/source schemas and do not
add a source-authority or network boundary. No additional security defect found.
Final conformance/package/coverage results remain the G2 owner's responsibility
and must be available before the final Security report/signoff.
