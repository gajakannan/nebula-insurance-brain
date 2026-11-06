# F0006 Feature Evidence Run

## Run Summary

- Run ID: `2026-11-02-5a00b0ff`
- Feature: F0006 — Assertion plane + origin + interpretation basis
- NEBULA_PRODUCT_ROOT: `/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain` (recorded environment selection, normalized once)
- Mode: clean; slice order: assembly-plan; prior completion run: none
- Contract: 2026-07-11
- Resumed: 2026-11-03T00:06:32+00:00

## Status

**Completed and approved**: G0 through G8 passed in this same run. The PM archived all five Done stories on 2026-11-05; 35/35 acceptance criteria and all 25 required story-role signoffs are verified. Latest approval is published at `planning-mds/operations/evidence/features/F0006-assertion-plane-origin-and-interpretation-basis/latest-run.json`.

Approval is limited to trusted local synthetic fixtures under the operator-accepted SEC-01 mitigation. Dependency remediation/qualification and verified resource isolation remain required before untrusted or production PDFs. The inherited High finding remains technically open. SEC-02/03 retain owners and dated follow-ups. No new producer or production activation is included.

The initial runtime-blocked README is preserved verbatim under `artifacts/test-results/initial-runtime-block-readme.md`.

## Evidence Index

| Evidence | Meaning |
|---|---|
| `g0-assembly-plan-validation.md` | Architect assembly judgment and implementation constraints |
| `artifacts/test-results/g0-migration-lineage.json` | Static source migration head: 0010 |
| `g1-runtime-preflight.md` | Recovered, passing runtime preflight; original failure retained separately |
| `g2-self-review.md`, `ai-compatibility-self-review.md` | Bounded implementation and compatibility self-reviews |
| `test-plan.md`, `test-execution-report.md`, `coverage-report.md` | QE's 35-AC map, observed runtime results and changed-code coverage |
| `deployability-check.md` | Locked builds, image/source integrity, schema packaging and safe rollback |
| `artifacts/security/` | All four scan classes and final changed-source snapshot |
| `artifacts/test-results/runtime-*` | Original Docker discovery and WSL transport evidence |
| `artifacts/runtime/` | Current run's application runtime definitions, owned by DevOps |
| `commands.log`, `lifecycle-gates.log`, `gate-state.json` | Executed commands, stage results and durable journal |
| `artifacts/diffs/changed-files.txt` | Current product-repository changed-path inventory |

## Validation Summary

G0 was attempted through `run-gate.py`. Initial failures exposed missing base-run
headings/diff/G0 decision row from the stopped attempt and premature scan
completeness checks at G0. The base-run omissions are addressed here. Parent
orchestration is fixing the validator's security-scan stage boundary; security
scope stays true, and pending scans are not represented as runs or waivers.
The repaired stage was rerun successfully with exit 0. Exact failures remain in the journal/logs
and `artifacts/test-results/g0-validator-diagnostic.json`.

## Open Follow-ups

SEC-01 High: AI Engineer + DevOps, Security verification, target2026-11-10 and before untrusted/production PDF ingestion. SEC-02 Medium: Security + Architect, target2026-11-10/before production security qualification. SEC-03 Low: Backend Developer + DevOps, target2026-11-17. Exact dispositions and SEC-05 G7 caller-map evidence are in [Security review](security-review-report.md) and [PM closeout](pm-closeout.md).

Both implementation review findings and all framework-validator defects are resolved without waivers. Historical failed/retried/skipped attempts remain evidence, separately from the final passing lanes.

## Resolved Validator Repair

VF-G0-001 (owner: framework maintainer / Codex) is resolved without waiver.
Security scan completeness now waits through G0/G1; G2 through closeout retain
enforcement. The parent ran seven staging regressions in the application runtime
container; JUnit: `artifacts/test-results/framework-security-scan-staging.xml`.
G0 then passed through run-gate.py (validate-g0 exit 0). Scope flags remain true;
all four scan classes were subsequently executed at G2, with raw findings retained.

## Resume

VF-G2-002 is resolved without waiver: the generic framework artifact-reference
parser now excludes Markdown delimiters and sentence punctuation while retaining
containment and missing-file checks. Eleven new Markdown/reference regressions
and the existing closure/security staging tests passed (45 total):
`artifacts/test-results/framework-artifact-markdown.xml`.

Reuse this run from the framework checkout:

```bash
python3 agents/scripts/resume-brief.py --product-root /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain --run-id 2026-11-02-5a00b0ff
python3 agents/scripts/project_context.py --product-root /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain --action feature
```

The missing journal from the first attempt is now created by actual G0 execution.
Never initialize another F0006 completion run or publish latest-run.json before G8.

## Resolved Completed-Story Validator Repair

VF-G8-003 is resolved without waiver. Completed `[x]`/`[X]` acceptance lists were falsely rejected by validate-stories.py, while an empty unchecked marker was accepted. The generic parser now accepts nonempty anchored Markdown criteria in all completion states and retains invalid/empty rejection. Red: 5 failed / 12 passed; green: 17 passed, zero failures/errors/skips. Framework lifecycle: six gates passed; all agents Python compiled successfully. The five actual archived stories then passed strict validation with no warnings.

Evidence: `artifacts/test-results/vf-g8-003-green.xml`, `artifacts/test-results/vf-g8-003-resolution.json`, `artifacts/diffs/framework-completed-checklist.patch`. Framework checkout was `5b3acf0681873a44b4d5977a97aa3f52ecf26110` plus that local patch; the prior two validator repairs are already in that observed commit. Product BLUEPRINT/CI pin was not advanced. The older framework-validator.patch remains historical evidence of those prior repairs.

## Resolved Recommendation-Verdict Tracker Repair

VF-G8-004 is resolved without waiver. The old tracker provenance parser rejected contract-passing PASS/APPROVED WITH RECOMMENDATIONS, despite accepted mitigations and passing scoped feature evidence. The generic hook now recognizes those canonical passing labels. Required roles, reviewer/date/evidence checks and the actual deep feature-evidence invocation remain enforced. Red: 10 failed / 10 passed; combined green: 60 passed, including the 20 new tracker cases, existing tracker tests, actual §15/PM-acceptance controls and the completed-checklist cases. Framework lifecycle: all six gates pass; compilation passes. The actual F0006 tracker rerun has zero errors and warnings.

Evidence: `artifacts/test-results/vf-g8-004-green-rerun.xml`, `artifacts/test-results/vf-g8-004-resolution.json`, `artifacts/diffs/framework-g8-validator-fixes.patch` (combined current local framework fixes). Original rejection and red cases remain in command-output logs and JUnit. The initial combined attempt passed 59 cases and exposed one incomplete test-registry fixture; the corrected fixture then reached the intended real deep-validator rejection. No product verdict was changed to hide recommendations, and no security acceptance control was bypassed.
