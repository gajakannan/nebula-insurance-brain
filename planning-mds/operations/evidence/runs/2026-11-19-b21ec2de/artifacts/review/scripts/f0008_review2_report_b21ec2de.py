import json
import sys
sys.path.insert(0,'/tmp')
from f0008_review2_exec_b21ec2de import ROOT,RUN

findings=[
 dict(id='SEC-F8-NEW-01',severity='high',owner='security',title='New commit response returns predecessor temporal metadata without corresponding predecessor-source READ checks',raw=['engine/apps/api/src/brain_api/routes/facts.py:210','engine/packages/brain-temporal/src/brain_temporal/commit.py:505','engine/apps/api/src/brain_api/schemas/facts.py:97'],mitigation='Proposed, not accepted: enforce current READ authority for every source behind returned predecessor/remainder metadata, or restrict the response to metadata the caller is allowed to receive; prove differing-source-readability behavior.',target_date=None,acceptance=None),
 dict(id='R2-ARCH-L1',severity='low',owner='architect',title='Four-copied-timestamps wording remains in the assembly plan and docstring',raw=['planning-mds/features/archive/F0008-bitemporal-canonical-facts/feature-assembly-plan.md:48','engine/packages/brain-temporal/src/brain_temporal/commit.py:251']),
 dict(id='QE2-L1',severity='low',owner='quality-engineer',title='Recorded runtime preflight does not precede the full-suite start',raw=['planning-mds/operations/evidence/runs/2026-11-18-bce4909b/artifacts/test-results/full-engine-regression.xml:1','planning-mds/operations/evidence/runs/2026-11-18-bce4909b/commands.log:4']),
 dict(id='PM2-L1',severity='low',owner='product-manager',title='Current manifest splits four space-containing filenames into nonexistent paths',raw=['planning-mds/operations/evidence/runs/2026-11-18-bce4909b/evidence-manifest.json','artifacts/diffs/manifest-inventory-drift.json']),
 dict(id='PM2-L2',severity='low',owner='product-manager',title='Feature Run shortcut and blueprint planning label remain stale',raw=['planning-mds/features/archive/F0008-bitemporal-canonical-facts/STATUS.md:9','planning-mds/BLUEPRINT.md:260']),
]
(RUN/'artifacts/review/findings.json').write_text(json.dumps(findings,indent=2)+'\n')
policy_path=RUN/'artifacts/test-results/fr4-policy.json'
validation_path=RUN/'artifacts/test-results/fr2-summary.json'
policy=json.loads(policy_path.read_text()) if policy_path.exists() else None
validation=json.loads(validation_path.read_text()) if validation_path.exists() else None
decision='Pending FR2–FR4; one High finding requires disposition'
if policy:
    decision=policy['status']+' — High conditions unaccepted; completion not cleared'
parts=[f'''# Fresh Feature Review — F0008

## Decision

**{decision}.** This is the second independent closeout audit requested after remediation. Product root: `{ROOT}`. Audited latest approved run: `2026-11-18-bce4909b`; review run: `2026-11-19-b21ec2de`. Immutable remediation diff: `339c9209385290247c01d1eea97a7c2c8b47fada..3290d17750b62d70b9130ac9010d096a584eead5` (198 paths). Full F0008 source was also checked against `2badb9a..3290d17`. DevOps is required.

**What remains pending:** one new **High** output-authorization finding and four **Low** documentation/evidence findings. The original missing commit-response fields and losing-audit requirement conflict are resolved by implementation plus explicit operator-approved amendments. The legacy serializer and same-slot lineage fixes are also present. The remainder of the old timestamp wording finding is still incomplete. Prior passing summaries and the remediation approval were not accepted as proof of these conclusions.

The new response includes copied predecessor/remainder attestation dates. Source authorization on POST checks the current proposal's sources, while equivalent GET reads check the returned version's sources. No matching check for the newly returned predecessor metadata was found. This is a **source-supported missing control**, not a claimed live reproduction. The attempted targeted runtime probe was stopped by automated cybersecurity safeguards; it was not retried. Source inspection and existing tests support the finding, but no new mixed-authority runtime result is asserted.

The recorded raw suite has **1,085 passing tests, zero failures/errors/skips**, with **217 F0008 cases**. Fixed-diff coverage is **24/24 remediation lines (100%)** and **718/732 whole-feature lines (98.087432%)**, both above 80%. The amended 46 functional criteria have executed mapping for the tested caller, while that coverage does not prove the new response authorization boundary.

Severity counts: **Critical 0, High 1, Medium 0, Low 4**. The High has a role owner and proposed defensive correction, but **no accepted mitigation or committed target date**. The review does not fabricate those commitments or treat the earlier Low SEC-F8-02 acceptance as accepting this new High. A policy result of CONDITIONALLY DONE is not an accepted completion or merge/release clearance; its required High disposition remains pending with the original lifecycle owners.

## Findings By Severity

| ID | Severity | Owner | Finding | Raw evidence |
|---|---|---|---|---|
''']
for f in findings:
    parts.append(f"| {f['id']} | {f['severity'].title()} | {f['owner']} | {f['title']} | "+'; '.join('`'+r+'`' for r in f['raw'])+' |\n')
parts.append('''
The High is counted only in Security. Architect/QE references to the same new response surface do not add counts. Complete triggers, uncertainty, source flow and repair ownership are in the role sections below.

## Completion Checks

| Lane | Fresh result |
|---|---|
| Product Manager | Current 35 signoffs and latest approved pointer agree; receiving F0018 handoffs exist. Two Low inventory/tracker findings remain. |
| Architect | Legacy omission and migration0015 lineage fixes verified. One Low timestamp-prose residual. New authorization concern transferred to Security. |
| QE | Raw 1,085 tests and fixed-range coverage verified. Prior functional gaps resolved for tested caller; one Low preflight-chronology finding. Mixed-readability response coverage absent. |
| Code Reviewer | Original Critical response omission resolved; source remains bounded to F0008. Security owns the new output-authority concern. |
| Security | One new High missing predecessor-source READ check on returned metadata. Source-only finding; no fresh runtime proof. |
| DevOps | Current local runtime/migration deployability passes; framework pin bump remains an assigned follow-up. |

Six lanes ran concurrently within available slots: parent PM, Architect/DevOps sharing a slot, QE in one slot, Code/Security sharing a slot. Each owns its findings and report section. All canonical artifacts are read-only.

''')
for name in ['product-manager.md','architect.md','quality-engineer.md','code-reviewer.md','security.md','devops.md']:
    path=RUN/'artifacts/review'/name
    parts.append(path.read_text()+'\n\n' if path.exists() else f'### {name}\n\nLane report pending.\n\n')
parts.append('''### Pending work already assigned outside this audit

- **Backend + Architect, verified by Security/QE:** correct and test SEC-F8-NEW-01; obtain a documented High disposition and target date through the owning lifecycle. This audit does not authorize or perform a repair.
- **Architect:** finish timestamp wording in the current plan/docstring. **PM:** preserve complete space-containing inventory paths and align current run/status shortcuts. **QE/DevOps:** preserve preflight chronology for the next validation run.
- **Operator:** formal ADR-0078 acceptance remains a separate decision.
- **F0018 / Architect + DevOps:** non-superuser application role and durable refusal reason persistence. The handoffs are now recorded; future implementation remains pending.
- **DevOps:** update BLUEPRINT and CI framework pins together; timezone-data pinning remains an older documented follow-up.
- **F0011:** number its future migration after0015. **Architect:** previously acknowledged valid/recorded API naming drift remains for the next contract revision. Production hosting remains F0026 scope.

## Validation Evidence

''')
if validation:
    parts.append('| Check | Exit | Result | Raw output |\n|---|---|---|---|\n')
    for item in validation['checks']:
        parts.append(f"| {item['name']} | {item['exit_code']} | {item['result']} | `{item['artifact']}` |\n")
    parts.append('\nRequired validation: **'+validation['result']+'**. Fresh validator streams are retained through the gate runtime’s supported capture parameters; checks are not inferred from old report PASS labels. Actual framework revision: `'+validation['framework_head']+'`; source-only security finding is independent of structural validator success.\n\n')
else:
    parts.append('FR2 pending.\n\n')
if policy:
    parts.append('`gate_policy.py --profile review-family --variant feature` returns **'+policy['status']+'** with Critical=0/High=1 and requires_justification=true. Raw domain input/output: `artifacts/test-results/fr4-policy.json`. Mandatory High acceptance details remain incomplete; no completion acceptance is issued.\n\n')
parts.append('''## Artifact Trace

- Current root/run/diff binding: `action-context.md`; context reload: `artifacts/review/product-context.txt`; exact changed sets and patch: `artifacts/diffs/`.
- Entry points: F0008 `latest-run.json` and current feature-run `evidence-manifest.json`. Role sections cite the exact raw source, contracts, JUnit, JSON coverage, migration/runtime and final scanner outputs reached from these manifest citations. `CAN/` means the selected run `2026-11-18-bce4909b`; bare story names mean the archived F0008 feature directory.
- Original review findings are used only for comparison. New raw source and evidence establish each resolved/partial/pending disposition. No global lane substitutes for feature-scoped evidence.
- Independent raw checks: `artifacts/review/pm-source-checks.json`, `qe-raw-artifact-check.json`, `architect-remediation-runtime.json`, and the source-only Security section. No fresh runtime access-boundary probe was completed. The automated safeguard rejection is explicitly retained as a verification limit, not a product test failure.
- Required gates: `gate-state.json`, `gate-decisions.md`, `lifecycle-gates.log`. Shell telemetry: `commands.log`; bootstrap records transparently distinguish recording time. Driver invocation uses unchanged `run-gate.py` with a temporary wrapper forwarding the supported stdout_path/stderr_path options and explicit tracker root binding; no framework source is edited.
- Fresh per-validator stdout/stderr/result metadata: `artifacts/validators/`. Story currency is checked using the identical generator against a byte-identical temporary story mirror; the canonical index is never regenerated in place.
- Framework checkout advanced from6d19d91 to840e724 during the audit. Exact validation revision is recorded. Product HEAD advanced from the reviewed3290d17 to squash-merge e024cd7 during the final integrity check; `artifacts/diffs/merge-tree-equivalence.json`, `merge-tree-hashes.txt` and an empty `merge-tree-equivalence.diff` prove the tracked trees are identical. The original immutable diff therefore reviews the current merged content. The initially strict commit-ID guard failed, this equivalence was verified, and FR3 was rerun after that check; no changed source was silently ignored. Canonical protected-file hashes and final tracked/staged diff checks verify that the audit made no repairs.
- Role sections include FR3 self-review and all justified omissions: no UI/AI change, no production rollout, no scanner rerun claim, no fresh mixed-authority runtime verification, and explicit current-role boundaries.
''')
(RUN/'feature-review-report.md').write_text(''.join(parts))
print(json.dumps(dict(report=str(RUN/'feature-review-report.md'),decision=decision,findings=len(findings))))
