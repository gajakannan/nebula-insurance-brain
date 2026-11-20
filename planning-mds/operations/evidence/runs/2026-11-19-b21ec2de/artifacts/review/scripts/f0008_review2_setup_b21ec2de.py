import hashlib
import json
from pathlib import Path
import shutil
import sys
sys.path.insert(0, '/tmp')
from f0008_review2_exec_b21ec2de import ROOT, FRAMEWORK, RUN, run

CAN = ROOT / 'planning-mds/operations/evidence/runs/2026-11-18-bce4909b'
manifest = json.loads((CAN / 'evidence-manifest.json').read_text())
code, head = run('git rev-parse HEAD', ROOT, 'artifacts/diffs/audited-head.txt')
assert code == 0 and head.startswith('3290d17')
head = head.strip()
base = manifest['scm']['head_commit_at_run_start']
for command, output in [
    (f'git diff --name-only {base}..{head}', 'artifacts/diffs/changed-files.txt'),
    (f'git diff --name-only 2badb9a..{head}', 'artifacts/diffs/full-feature-files.txt'),
    (f'git diff {base}..{head} -- engine planning-mds/schemas planning-mds/api', 'artifacts/diffs/remediation.diff'),
    ('git status --short --untracked-files=all', 'artifacts/diffs/initial-working-tree.txt'),
    ('git rev-parse HEAD', 'artifacts/review/framework-head.txt')]:
    cwd = FRAMEWORK if output.endswith('framework-head.txt') else ROOT
    code, _ = run(command, cwd, output)
    assert code == 0
shutil.copyfile('/tmp/f0008-rereview-product-context.txt', RUN / 'artifacts/review/product-context.txt')
paths = set(manifest['changed_paths'])
paths.update([str(CAN.relative_to(ROOT))+'/evidence-manifest.json',
              'planning-mds/operations/evidence/features/F0008-bitemporal-canonical-facts/latest-run.json'])
hashes = {rel: hashlib.sha256((ROOT/rel).read_bytes()).hexdigest() for rel in paths if (ROOT/rel).is_file()}
(RUN/'artifacts/review/protected-input-hashes.json').write_text(json.dumps(hashes, indent=2)+'\n')
files = (RUN/'artifacts/diffs/changed-files.txt').read_text().splitlines()
delta = dict(in_diff_not_manifest=sorted(set(files)-set(manifest['changed_paths'])),
             in_manifest_not_diff=sorted(set(manifest['changed_paths'])-set(files)))
(RUN/'artifacts/diffs/manifest-inventory-drift.json').write_text(json.dumps(delta,indent=2)+'\n')
context = f'''# Action Context

- Action: feature-review; read-only-audit; policy 2026-07-11.
- NEBULA_PRODUCT_ROOT: {ROOT}; recorded root reused from the prior review and explicitly resolved, no conflict.
- FEATURE_ID: F0008; FEATURE_SLUG: bitemporal-canonical-facts.
- FEATURE_PATH: {ROOT}/planning-mds/features/archive/F0008-bitemporal-canonical-facts
- FEATURE_INDEX_ROOT: {ROOT}/planning-mds/operations/evidence/features/F0008-bitemporal-canonical-facts
- FEATURE_RUN_ID: 2026-11-18-bce4909b (latest approved remediation run).
- FEATURE_RUN_FOLDER: {CAN} (read only).
- FEATURE_REVIEW_RUN_ID: 2026-11-19-b21ec2de (fresh review explicitly requested; secrets.token_hex(4), generated once).
- FEATURE_REVIEW_RUN_FOLDER: {RUN}
- MODE: closeout-audit (latest approved archived run).
- DIFF_RANGE: {base}..{head} (remediation's recorded starting commit through current HEAD).
- Full feature comparison: 2badb9a..{head}; inspect original delivered source too, without re-auditing other features.
- Changed-file set: {len(files)} paths, artifacts/diffs/changed-files.txt; full-feature inventory separately retained.
- RUN_DEVOPS: auto -> yes; migration0015 added and full feature still includes CI/migration0014.
- PR_URL: not supplied; no remote mutation or checkout performed.
- Prior audit: 2026-11-18-d34a095e, completed NOT DONE. Compare each prior finding to raw remediation, then seek additional gaps.

## Boundaries and assumptions

Only this review run and /tmp may be written. No implementation, tests, feature docs, trackers, KG or canonical evidence repair. Do not accept the remediation report's resolved labels without source/test/scan checks. Manifest-cited raw artifacts are retrieved narrowly. The existing completed audit cannot be resumed by resume-brief.py because the framework erroneously requires a manifest for a base run; no old review is altered. New review is independent.

The same role skills/framework action procedure loaded previously remain applicable; current framework revision is recorded separately. Product context was reloaded and read in three bounded chunks before substantive review. Findings preserve raw-source precedence and severity ownership. Required validators run through run-gate.py with its supported runtime stdout/stderr capture enabled by a transparent temporary wrapper, so each actual validator output is retained without reruns or framework edits.

## Lifecycle position

FR0 locked; FR1 next. Six role lanes will check prior resolutions and additional pending work. Final verdict awaits FR2–FR4.
'''
(RUN/'action-context.md').write_text(context)
(RUN/'README.md').write_text('# F0008 fresh feature review\n\nRun 2026-11-19-b21ec2de; closeout-audit of remediation2026-11-18-bce4909b. In progress.\n')
(RUN/'gate-decisions.md').write_text('# Gate Decisions\n\n## FR0\n\nPASS. Latest approved run, archived path, exact current diff, clean tracked tree and DevOps=yes resolved in action-context.md.\n')
(RUN/'artifact-trace.md').write_text('# Artifact Trace\n\nInputs: product-context.txt, latest-run.json and selected evidence-manifest.json, prior findings, exact current diffs. Role-owned sections cite raw paths. All outputs confined to this run and /tmp; protected-input-hashes.json tracks canonical file integrity.\n')
print(json.dumps(dict(head=head, diff=f'{base}..{head}', files=len(files), inventory_drift=delta),indent=2))
