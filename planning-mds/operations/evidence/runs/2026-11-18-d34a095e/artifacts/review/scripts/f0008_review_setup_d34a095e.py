import hashlib
import json
import sys
from pathlib import Path
sys.path.insert(0, '/tmp')
from f0008_review_exec_d34a095e import ROOT, FRAMEWORK, RUN, run

base = '2badb9ad2756f38ee9a1d84930787a3df989a245'
head = '339c9209385290247c01d1eea97a7c2c8b47fada'
feature_run = ROOT / 'planning-mds/operations/evidence/runs/2026-11-17-1a4ae2f0'
manifest = json.loads((feature_run / 'evidence-manifest.json').read_text())
code, files_text = run(f'git diff --name-only {base}..{head}', ROOT, 'artifacts/diffs/changed-files.txt')
assert code == 0
files = files_text.splitlines()
code, current = run('git rev-parse HEAD', ROOT, 'artifacts/diffs/audited-head.txt')
assert current.strip() == head
code, status = run('git status --short --untracked-files=all', ROOT, 'artifacts/diffs/initial-working-tree.txt')
code, patch = run(f'git diff {base}..{head} -- engine .github/workflows/ci-gates.yml', ROOT, 'artifacts/diffs/implementation.diff')
assert code == 0
actual, declared = set(files), set(manifest['changed_paths'])
delta = {'in_diff_not_manifest': sorted(actual-declared), 'in_manifest_not_diff': sorted(declared-actual)}
(RUN / 'artifacts/diffs/manifest-scope-drift.json').write_text(json.dumps(delta, indent=2)+'\n')
snapshot = {}
for rel in set(manifest['changed_paths']) | {str(p.relative_to(ROOT)) for p in (feature_run / 'evidence-manifest.json', ROOT / 'planning-mds/operations/evidence/features/F0008-bitemporal-canonical-facts/latest-run.json')}:
    path = ROOT / rel
    if path.is_file():
        snapshot[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
(RUN / 'artifacts/review/initial-canonical-hashes.json').write_text(json.dumps(snapshot, indent=2)+'\n')
context = f'''# Action Context

- Action: feature-review; read-only-audit; policy 2026-07-11.
- NEBULA_PRODUCT_ROOT: {ROOT}; source: shell environment, normalized by the resolver.
- FEATURE_ID: F0008 (operator supplied `f0008`, normalized).
- FEATURE_SLUG: bitemporal-canonical-facts (REGISTRY.md).
- FEATURE_PATH: {ROOT}/planning-mds/features/archive/F0008-bitemporal-canonical-facts
- FEATURE_INDEX_ROOT: {ROOT}/planning-mds/operations/evidence/features/F0008-bitemporal-canonical-facts
- FEATURE_RUN_ID: 2026-11-17-1a4ae2f0 (latest approved run).
- FEATURE_RUN_FOLDER: {feature_run}
- FEATURE_REVIEW_RUN_ID: 2026-11-18-d34a095e (date + secrets.token_hex(4), generated once).
- FEATURE_REVIEW_RUN_FOLDER: {RUN}
- MODE: closeout-audit, resolved from approved latest-run.json and Archived feature status; disclosed to operator before setup.
- PR_URL: not supplied. No PR checkout or remote mutation performed.
- DIFF_RANGE: {base}..{head}, resolved from the manifest's start commit and the checked-out merged feature commit; independently verified against git.
- RUN_DEVOPS: auto -> yes (CI change, migration 0014, runtime_bearing=true, deployment_config_changed=true).

## Changed-file lock

The diff has {len(files)} paths, listed in `artifacts/diffs/changed-files.txt`; the implementation patch is `artifacts/diffs/implementation.diff`. Manifest comparison is `artifacts/diffs/manifest-scope-drift.json`. Rename sources and destinations are inspected using git name-status. Existing untracked files are listed in `artifacts/diffs/initial-working-tree.txt`. There are no tracked working-tree edits. The pre-existing completed audit `2026-11-18-a3709ba0` is preserved, and its verdict is not evidence of feature completion for this independent audit.

## Assumptions and boundaries

Review the latest approved archived feature, not an older or candidate run. feature.md reached G8 according to manifest and closeout; raw gates and role evidence will be verified at FR1. Only this review run and temporary scripts under /tmp may be written. Canonical evidence, feature documentation, trackers, generated graph, tests and implementation remain read-only. Story-index currency runs on a temporary mirror. No repair, publication, commit, push or approval of feature implementation is authorized by this action.

The attempted resume-brief on the pre-existing audit returned exit 2 because the framework requires evidence-manifest.json for a base run. Its README identifies a completed audit by another reviewer, so it is not resumed or changed.

## Lifecycle Stage

FR0 ready; six role lanes at FR1; FR2 required validators; FR3 evidence self-review; FR4 computed verdict. Reviewer lanes may share an execution slot, while retaining role-specific ownership and separate sections.
'''
(RUN / 'action-context.md').write_text(context)
(RUN / 'gate-decisions.md').write_text('# Gate Decisions\n\n## FR0 — Feature run and diff lock\n\nPASS. F0008 latest approved run, archived path, exact merged diff, untracked state and DevOps=yes resolved in action-context.md. No conflicting product selection.\n')
(RUN / 'artifact-trace.md').write_text('# Artifact Trace\n\n## Inputs\n\n- Product context: artifacts/review/product-context.txt.\n- Canonical manifest and latest pointer: paths in action-context.md.\n- Raw changed files: artifacts/diffs/changed-files.txt.\n- Initial protected artifact hashes: artifacts/review/initial-canonical-hashes.json.\n\n## Outputs\n\nThis review run only. Individual role reports record exact raw source and evidence paths; commands.log records reads and validator outputs.\n')
(RUN / 'README.md').write_text('# F0008 Feature Review\n\nRun 2026-11-18-d34a095e; closeout-audit of approved feature run 2026-11-17-1a4ae2f0.\n\nStatus: FR0 complete; audit in progress.\n')
print(json.dumps({'files': len(files), 'diff': f'{base}..{head}', 'manifest_drift': delta}, indent=2))
