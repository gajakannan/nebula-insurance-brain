import hashlib
import json
import re
import shutil
import sys
from pathlib import Path
sys.path.insert(0, '/tmp')
from f0008_review_exec_d34a095e import ROOT, RUN

policy = json.loads((RUN / 'artifacts/test-results/fr4-policy.json').read_text())
validation = json.loads((RUN / 'artifacts/test-results/fr2-summary.json').read_text())
assert validation['result'] == 'PASS' and policy['status'] == 'NOT DONE'
assert policy['totals'] == {'critical': 1, 'high': 0}
state = json.loads((RUN / 'gate-state.json').read_text())
assert all(state['stages'][stage]['status'] == 'completed' for stage in ['FR0','FR1','FR2','FR3','FR4'])
assert not (RUN / 'evidence-manifest.json').exists()
findings = json.loads((RUN / 'artifacts/review/findings.json').read_text())
counts = {key: sum(f['severity']==key for f in findings) for key in ['critical','high','medium','low']}
assert counts == {'critical':1,'high':0,'medium':3,'low':6}
for item in findings:
    for ref in item['raw'].split('; '):
        raw = ref.split('#',1)[0]
        match = re.fullmatch(r'(.+):(\d+)', raw)
        rel = match.group(1) if match else raw
        path = ROOT / rel if (ROOT / rel).is_file() else RUN / rel
        assert path.is_file(), (item['id'], path)
        if match:
            assert int(match.group(2)) <= len(path.read_text().splitlines()), ref
scripts_dir = RUN / 'artifacts/review/scripts'
scripts_dir.mkdir(exist_ok=True)
preserved = []
for path in Path('/tmp').glob('f0008*d34a095e*.py'):
    shutil.copyfile(path, scripts_dir / path.name)
    preserved.append(path.name)
protected = json.loads((RUN / 'artifacts/review/protected-input-check.json').read_text())
assert not protected['changed_protected_files']
readme = '''# F0008 Feature Review — 2026-11-18-d34a095e

**Done state: NOT DONE.** Read-only closeout audit of approved feature run `2026-11-17-1a4ae2f0`, merged diff `2badb9a..339c920`, product `/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain`.

One Critical completion finding, zero High, three Medium and six Low. Critical refers to the framework's unmet-acceptance-criterion policy, not an established security exploit. S0002 AC7 requires temporal metadata in successful commit responses, but the delivered response has only the three legacy fields; S0007's narrower API scope was never explicitly reconciled with that requirement.

Only 44/46 criteria are verified. The second unresolved criterion is S0004 AC1's zero-audit losing-commit clause; actual failed authorization auditing and the successful-only test filter must be reconciled while preserving the security audit contract.

Raw results substantiate 1,081 passing engine tests, no failures/errors/skips, and 695/709 changed executable production lines covered (98.03%). All five required validators pass; story-index regeneration on a temporary mirror is byte-identical. gate_policy.py returns NOT DONE because Critical=1.

## Review artifacts

- [Feature review report](feature-review-report.md): decision, findings, six owned role sections, validation and raw trace.
- [Action context](action-context.md): resolved root/run/diff, assumptions and retrieval boundaries.
- [Gate decisions](gate-decisions.md): FR0–FR4; [gate-state.json](gate-state.json) confirms all five stages completed.
- [Validation summary](artifacts/test-results/fr2-summary.json), [policy result](artifacts/test-results/fr4-policy.json), [findings](artifacts/review/findings.json).
- [Protected-input verification](artifacts/review/protected-input-check.json): 131 hashed canonical files unchanged, no tracked or staged diff.
- [Artifact trace](artifact-trace.md), [command telemetry](commands.log), [lifecycle results](lifecycle-gates.log).

## Open follow-ups

- Code Reviewer routes CR-F8-01 to PM/Architect for explicit requirement reconciliation, then Backend/QE for the agreed contract, tests and fresh lifecycle evidence.
- QE routes QE-M1 to PM/Architect/Security to settle the loser-audit clause and prove the agreed behavior.
- Architect owns the legacy temporal:null schema mismatch and the lower-severity lineage/ADR follow-ups.
- PM owns the exact F0018 carry-over registration and stale metadata/inventory. QE/Security own raw execution/scan-summary drift.

Reviewers performed no repair. Implementation, tests, feature docs, trackers, KG, canonical evidence and pre-existing audit `2026-11-18-a3709ba0` are preserved. No commit, publication or rollout was performed. This base review run has no evidence-manifest.json by contract.
'''
(RUN / 'README.md').write_text(readme)
with (RUN / 'gate-decisions.md').open('a') as handle:
    handle.write('''
## FR4 — Done gate

**NOT DONE.** Required evidence validation PASS; counts Critical=1, High=0, Medium=3, Low=6. `gate_policy.py --profile review-family --variant feature --code-critical 1` computes NOT DONE, approve_enabled=false. Actual full domain input and result: artifacts/test-results/fr4-policy.json and commands.log. The Critical is CR-F8-01 (unmet AC / unreconciled requirement), not a security exploit. All gate-driver stages FR0 through FR4 completed in order. Outstanding fixes route to the original lifecycle owners; no automatic repair or feature completion approval occurs here.
''')
with (RUN / 'lifecycle-gates.log').open('a') as handle:
    for stage, summary, artifact in [
        ('FR0','PASS: feature/run/diff/root locked; DevOps yes.','action-context.md'),
        ('FR1','COMPLETED: six owned role lanes; 10 findings.','feature-review-report.md'),
        ('FR3','PASS: raw citations/self-review/omissions verified.','artifacts/review/protected-input-check.json'),
        ('FR4','NOT DONE: review-family policy, critical=1, high=0; validation PASS.','artifacts/test-results/fr4-policy.json')]:
        handle.write(f'\n### {stage} — judgment\nStage: {stage}\nExit Code: 0 (gate driver)\nResult: {summary}\nOutput References: {artifact}, artifacts/review/{stage.lower()}-driver.json\nSkipped Gates: -\n')
with (RUN / 'artifact-trace.md').open('a') as handle:
    handle.write('\n## Final review trace\n\n')
    for name in ['product-manager.md','architect.md','quality-engineer.md','code-reviewer.md','security.md','devops.md']:
        p = RUN / 'artifacts/review' / name
        digest = hashlib.sha256(p.read_bytes()).hexdigest()
        handle.write(f'- Role-owned section: artifacts/review/{name}; SHA-256 {digest}. Exact raw paths are in that section and the compiled report.\n')
    handle.write('\nRequired validator operation records: artifacts/test-results/fr2-operation-results.json. Story currency and explicit-root tracker output: artifacts/test-results/fr2-story-index-currency.json and fr2-explicit-trackers.txt. Policy: artifacts/test-results/fr4-policy.json. Protected inputs: artifacts/review/initial-canonical-hashes.json and protected-input-check.json. Canonical files unchanged.\n\nTemporary diagnostic/orchestration scripts preserved under artifacts/review/scripts/: '+', '.join(sorted(preserved))+'.\n\nFramework limitation: run-gate retained operation exit/completion records but not validator stdout; no raw stdout transcript is claimed. Original cwd-placeholder rows are preserved in artifacts/review/gate-runtime-cwd-original.jsonl and expanded transparently in this run log. Pre-setup bootstrap records disclose recording-time limits. These are audit trace limits, not F0008 feature defects.\n')
with (RUN / 'action-context.md').open('a') as handle:
    handle.write('\n## Final position\n\nFR0–FR4 complete. Verdict NOT DONE; required validators PASS; C1/H0/M3/L6. Only this review run and /tmp were written. All 131 protected file hashes match; tracked/staged diffs remain empty. Next work belongs to original lifecycle owners.\n')
result = dict(verdict='NOT DONE', validation='PASS', findings=counts, stages='FR0–FR4 completed',
              all_raw_finding_paths_exist=True, protected=protected, preserved_scripts=len(preserved))
(RUN / 'artifacts/review/completion-check.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps(result, indent=2))
