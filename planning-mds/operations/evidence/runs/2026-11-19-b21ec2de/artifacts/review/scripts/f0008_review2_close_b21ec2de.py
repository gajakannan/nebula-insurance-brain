import datetime
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path
sys.path.insert(0,'/tmp')
from f0008_review2_exec_b21ec2de import ROOT,FRAMEWORK,RUN,append

policy=json.loads((RUN/'artifacts/test-results/fr4-policy.json').read_text())
validation=json.loads((RUN/'artifacts/test-results/fr2-summary.json').read_text())
state=json.loads((RUN/'gate-state.json').read_text())
findings=json.loads((RUN/'artifacts/review/findings.json').read_text())
assert validation['result']=='PASS' and policy['status']=='CONDITIONALLY DONE'
assert policy['totals']==dict(critical=0,high=1)
assert all(state['stages'][g]['status']=='completed' for g in ['FR0','FR1','FR2','FR3','FR4'])
assert not (RUN/'evidence-manifest.json').exists()
for finding in findings:
    for ref in finding['raw']:
        match=re.fullmatch(r'(.+):(\d+)',ref)
        rel=match.group(1) if match else ref
        path=ROOT/rel if (ROOT/rel).is_file() else RUN/rel
        assert path.is_file(),ref
        if match: assert int(match.group(2))<=len(path.read_text().splitlines()),ref

# Normalize only our log's known framework telemetry placeholder and preserve raw rows.
log=RUN/'commands.log'
rows=[json.loads(line) for line in log.read_text().splitlines()]
raw=[]
for row in rows:
    if row.get('cwd')=='{NEBULA_PRODUCT_ROOT}':
        raw.append(dict(row))
        row['cwd']=str(ROOT)
        row['recording_note']='Expanded actual bound product cwd; original row preserved in artifacts/review/gate-cwd-original.jsonl.'
if raw:
    (RUN/'artifacts/review/gate-cwd-original.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in raw))
    log.write_text(''.join(json.dumps(r)+'\n' for r in rows))
bootstrap=[
 (FRAMEWORK,f'python3 agents/scripts/resume-brief.py --product-root {ROOT} --run-id 2026-11-18-d34a095e',2),
 (ROOT,'git status --short',0),
 (ROOT,"git log -6 --format='%h %s'",0),
 (FRAMEWORK,f'python3 agents/scripts/_product_root.py --product-root {ROOT}',0),
 (FRAMEWORK,f'python3 agents/scripts/project_context.py --product-root {ROOT} --action feature-review > /tmp/f0008-rereview-product-context.txt',0),
 (ROOT,'cat planning-mds/operations/evidence/features/F0008-bitemporal-canonical-facts/latest-run.json',0),
 (FRAMEWORK,"sed -n '1,220p' /tmp/f0008-rereview-product-context.txt",0),
 (ROOT,'cat planning-mds/operations/evidence/runs/2026-11-18-bce4909b/evidence-manifest.json',0),
 (ROOT,'git diff --stat 339c920..3290d17',0),
 (FRAMEWORK,"sed -n '221,430p' /tmp/f0008-rereview-product-context.txt",0),
 (FRAMEWORK,"sed -n '431,680p' /tmp/f0008-rereview-product-context.txt",0),
 (FRAMEWORK,'python3 -c \'import secrets; from datetime import date; print(date.today().isoformat() + "-" + secrets.token_hex(4))\'',0),
]
stamp=datetime.datetime.now().astimezone().isoformat()
for cwd,command,code in bootstrap:
    append(log,dict(schema_version=1,timestamp=stamp,cwd=str(cwd),command=command,exit_code=code,artifacts=[],redactions=[],recording_note='Retrospective pre-setup discovery record. Timestamp is recording time, not original execution time.'))
scripts=RUN/'artifacts/review/scripts'
scripts.mkdir(exist_ok=True)
preserved=[]
for path in Path('/tmp').glob('f0008*b21ec2de*.py'):
    shutil.copyfile(path,scripts/path.name)
    preserved.append(path.name)
readme='''# F0008 fresh review — 2026-11-19-b21ec2de

**Policy verdict: CONDITIONALLY DONE; conditions unaccepted, completion not cleared.**

Audited latest approved remediation run `2026-11-18-bce4909b`. Prior response-metadata and losing-audit AC gaps are fixed; a new High authorization finding remains. The added commit response includes predecessor/remainder attestation dates while its READ set covers the new proposal's sources. Equivalent GET output has additional source READ checks. This finding is source-supported; no fresh runtime disclosure was demonstrated because automated safeguards stopped the proposed verification.

Counts: Critical0, High1, Medium0, Low4. The High has no accepted mitigation or committed target date. No new completion acceptance is issued by this audit.

Verified raw evidence: 1,085 tests passed, zero failures/errors/skips; remediation coverage24/24 (100%); whole-feature coverage718/732 (98.09%). All five mandatory validators pass and story-index currency is byte-identical. All FR0–FR4 stages are complete.

## Pending work

- **Security / Backend + Architect / QE:** settle the predecessor-metadata READ boundary and add differing-source-readability regression evidence, then document the High disposition and target date.
- **Architect:** finish timestamp wording. **PM:** fix the four whitespace-split manifest paths and stale current-run/blueprint labels. **QE/DevOps:** preserve preflight chronology.
- **Existing downstream follow-ups:** Operator ADR-0078 acceptance; F0018 application-role/refusal-reason work; DevOps framework-pin and tzdata update; F0011 migration numbering after0015; older API naming drift and F0026 production hosting.

## Evidence

- [Full report](feature-review-report.md) — findings, six owned role sections, prior dispositions, validation, limits and artifact trace.
- [Validation](artifacts/test-results/fr2-summary.json), [severity policy](artifacts/test-results/fr4-policy.json), [findings](artifacts/review/findings.json).
- [Protected inputs](artifacts/review/protected-input-check.json), [merge equivalence](artifacts/diffs/merge-tree-equivalence.json), [gates](gate-decisions.md), [telemetry](commands.log).

The reviewed commit3290d17 and current squash-merge e024cd7 have identical tracked trees. Validation used framework840e724. All194 protected canonical file hashes are unchanged; tracked/staged diffs are empty. Only this review run and /tmp were written. No source, tests, canonical evidence, trackers or KG were repaired. This base review run intentionally has no evidence-manifest.json.
'''
(RUN/'README.md').write_text(readme)
with (RUN/'gate-decisions.md').open('a') as h:
    h.write('''
## FR4 — Done gate

Computed **CONDITIONALLY DONE** with gate_policy.py review-family/feature, Critical0/High1; mandatory validation PASS. The High is SEC-F8-NEW-01. Conditions remain unaccepted: mitigation/target date are not approved, so no completion acceptance is issued. Exact input/output: artifacts/test-results/fr4-policy.json. Four Low findings and explicit downstream follow-ups remain. No repairs occur in this audit.

## Integrity recheck

The final commit-ID guard detected external squash-merge movement from3290d17 to e024cd7. A complete tracked diff is empty and both tree hashes match. The bound evidence run/latest pointer and194 protected hashes are unchanged. FR3 was explicitly rerun after this equivalence check. The initial failed guard is retained in commands.log; it is not an ignored product change or a failed feature validator. Framework advanced to840e724 before validation and remained stable during it; actual streams/revision are retained.
''')
with (RUN/'action-context.md').open('a') as h:
    h.write('\n## Final position\n\nFR0–FR4 complete. Policy: CONDITIONALLY DONE, High conditions unaccepted; C0/H1/M0/L4. Mandatory validators PASS. Audited3290d17 and currente024cd7 have identical tracked trees (merge-tree-equivalence.json);194 canonical hashes match. Framework FR2 revision840e724. Retrospective bootstrap rows identify their recording-time limit; the gate cwd placeholder is expanded transparently with originals retained. The proposed runtime authorization probe was stopped by automated safeguards and never retried. No live disclosure proof is claimed; source-supported finding remains with owners.\n')
with (RUN/'artifact-trace.md').open('a') as h:
    h.write('\n## Final role evidence\n\n')
    for name in ['product-manager.md','architect.md','quality-engineer.md','code-reviewer.md','security.md','devops.md']:
        path=RUN/'artifacts/review'/name
        h.write(f'- artifacts/review/{name}; SHA-256 {hashlib.sha256(path.read_bytes()).hexdigest()}; exact raw citations and limits in that owned section.\n')
    h.write('\nValidator stdout/stderr/result metadata: artifacts/validators/. Mandatory summary: artifacts/test-results/fr2-summary.json. Policy: artifacts/test-results/fr4-policy.json. Integrity: protected-input-check.json and merge-tree-equivalence.json. Diagnostic/orchestration scripts retained in artifacts/review/scripts/: '+', '.join(sorted(preserved))+'.\n\nNo actual runtime authorization probe was performed. Automated cybersecurity safeguards prevented the proposed verification; the safer source-only review completed, with remaining verification explicitly pending. Gate stream capture uses the supported runtime API; no framework source was edited. Bootstrap discovery was recorded retrospectively and gate cwd originals are preserved in gate-cwd-original.jsonl.\n')
with (RUN/'lifecycle-gates.log').open('a') as h:
    for gate,text,ref in [
      ('FR0','PASS: root/run/diff bound; DevOps yes.','action-context.md'),
      ('FR1','COMPLETED: all six lanes, source-supportedHigh1/Low4.','feature-review-report.md'),
      ('FR3','PASS after tree-equivalence/integrity recheck; limits explicit.','artifacts/review/protected-input-check.json'),
      ('FR4','CONDITIONALLY DONE; High conditions unaccepted; no completion clearance.','artifacts/test-results/fr4-policy.json')]:
        h.write(f'\n### {gate} — final judgment\nStage: {gate}\nExit Code: 0 (driver)\nResult: {text}\nOutput References: {ref}\nSkipped Gates: role-specific limitations in report\n')
result=dict(review_complete=True,policy_verdict=policy['status'],completion_accepted=False,validation='PASS',findings=dict(critical=0,high=1,medium=0,low=4),all_finding_refs_exist=True,canonical_files_unchanged=194,stages=list(state['stages']))
(RUN/'artifacts/review/completion-check.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
