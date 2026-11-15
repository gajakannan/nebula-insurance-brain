import datetime
import json
from pathlib import Path
import shlex
import shutil
import subprocess
import sys

from f0064_review_exec import append_json

root = Path('/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain')
review = root / 'planning-mds/operations/evidence/runs/2026-11-14-7cba50ff'
framework = Path('/home/gajap/uSandbox/repos/nebula/nebula-agents')
locked = '6acd80560c0bc486bf9a7b28041631f907c2e901'
now = datetime.datetime.now(datetime.timezone.utc).isoformat()

checks = [
    ('head', ['git', 'rev-parse', 'HEAD']),
    ('tracked_worktree', ['git', 'diff', '--exit-code', 'HEAD']),
    ('tracked_index', ['git', 'diff', '--cached', '--exit-code', 'HEAD']),
    ('status', ['git', 'status', '--porcelain=v1']),
]
results = {}
for name, argv in checks:
    r = subprocess.run(argv, cwd=root, text=True, capture_output=True)
    results[name] = {'command': shlex.join(argv), 'exit_code': r.returncode,
                     'stdout': r.stdout, 'stderr': r.stderr}
    append_json(review / 'commands.log', dict(schema_version=1, timestamp=now,
                cwd=str(root), command=shlex.join(argv), exit_code=r.returncode,
                artifacts=[str((review / 'artifacts/read-only-check.json').relative_to(root))],
                redactions=[]))
expected_untracked = '?? ' + str(review.relative_to(root)) + '/'
ok = (results['head']['stdout'].strip() == locked
      and all(r['exit_code'] == 0 for r in results.values())
      and all(line == expected_untracked for line in results['status']['stdout'].splitlines())
      and not (review / 'evidence-manifest.json').exists())
results['passed'] = ok
results['explanation'] = 'HEAD unchanged; no staged/unstaged tracked changes; only review run is untracked; no review manifest.'
(review / 'artifacts/read-only-check.json').write_text(json.dumps(results, indent=2) + '\n')
if not ok:
    print(json.dumps(results, indent=2))
    sys.exit(1)

policy = json.loads((review / 'artifacts/gate-policy.json').read_text())
assert policy['status'] == 'TRULY DONE'
raw_names = ['closeout', 'trackers', 'kg-symbols', 'kg-drift', 'templates']
assert all((review / 'artifacts/validation' / (n + '.txt')).is_file() for n in raw_names)
assert (review / 'artifacts/diffs/story-index-currency.diff').read_text() == ''

report = (review / 'feature-review-report.md').read_text()
report = report.replace(
    'FR1 completed. All six role lanes have finished and performed evidence self-review. Final decision awaits required FR2 validators and FR4 policy computation. No implementation, test, feature document, canonical feature evidence, tracker or KG repair was performed.',
    '**TRULY DONE.** Required evidence validation PASS; 0 Critical, 0 High, 0 Medium, 4 Low findings. All six role reviews and evidence self-reviews pass. The review-family feature policy computes TRULY DONE; the four nonblocking documentation/evidence-quality follow-ups remain recorded. No implementation, test, feature document, canonical feature evidence, tracker or KG repair was performed.')

validation = '''| Required check | Exit | Raw output |
|---|---:|---|
| F0064 feature evidence, stage closeout | 0 | [closeout.txt](artifacts/validation/closeout.txt): one package validated |
| Tracker consistency, explicitly bound product | 0 | [trackers.txt](artifacts/validation/trackers.txt): 0 errors, 0 warnings |
| KG symbols | 0 | [kg-symbols.txt](artifacts/validation/kg-symbols.txt): integrity PASS, 2,175 indexed/bound symbols |
| KG drift | 0 | [kg-drift.txt](artifacts/validation/kg-drift.txt): integrity PASS |
| Framework templates | 0 | [templates.txt](artifacts/validation/templates.txt): prompts align with action contracts |
| Story-index currency (changed story files) | 0 | [story-index-currency.txt](artifacts/story-index-currency.txt): 47 stories, byte-identical; empty diff |

FR2 ran the five required operations in order through run-gate.py; artifacts/fr2-driver.txt and gate-state.json record all five completed. The driver's log_refs were empty, so the same read-only validators were explicitly captured once more to durable, distinct stdout artifacts above. Every exit code, summary and raw output path is appended to lifecycle-gates.log. The driver tracker operation used the bound NEBULA_PRODUCT_ROOT environment; the captured tracker command additionally supplies the same absolute --product-root. No feature-wide evidence validation of other features was requested.

KG validators emit two nonblocking global schema notices: declared edge types validated_by and supersedes are unused. They report no integrity/drift/symbol failure; this audit does not widen F0064 to repair global graph vocabulary.

Story-index regeneration ran only on an isolated temporary copy with the canonical product root passed explicitly. The canonical index was never written. Fresh feature-scope readiness also passed after archive (architect/QE raw outputs).

FR4 policy: artifacts/gate-policy.json, profile review-family, variant feature, all role domains Critical=0/High=0 and evidence-validation=PASS. It returns TRULY DONE. A failed required evidence validator would block that verdict; no failure was waived.

Read-only verification: artifacts/read-only-check.json confirms the locked HEAD and all tracked files are unchanged, only this review run is untracked, and no evidence-manifest.json exists in the base review run.'''
report = report.replace(
    'Pending FR2. Required validators will run through run-gate.py using the bound absolute product root. Story-index currency will be checked on an isolated temporary copy; canonical trackers will remain untouched.',
    validation)

roles = [('Product Manager', 'product-manager'), ('Architect', 'architect'),
         ('Quality Engineer', 'quality-engineer'), ('Code Reviewer', 'code-reviewer'),
         ('Security', 'security'), ('DevOps', 'devops')]
details = []
for title, slug in roles:
    lane = (review / 'artifacts/reviews' / (slug + '.md')).read_text().splitlines()
    transformed = []
    for line in lane[1:]:
        transformed.append('##' + line if line.startswith('#') else line)
    details.append('### ' + title + ' — owned review section\n\n' + '\n'.join(transformed).strip())
report = report.replace('\n## Validation Evidence\n',
                        '\n' + '\n\n'.join(details) + '\n\n## Validation Evidence\n')
(review / 'feature-review-report.md').write_text(report)

readme = '''# F0064 Feature Review

Verdict: **TRULY DONE** under review-family policy.

Reviewed PRs [48](https://github.com/gajakannan/nebula-insurance-brain/pull/48), [49](https://github.com/gajakannan/nebula-insurance-brain/pull/49), [50](https://github.com/gajakannan/nebula-insurance-brain/pull/50); closeout-audit of approved feature run 2026-11-14-3325803a.

All 23 ACs are supported. All five required validators pass; story index is byte-identical; final PR50 CI jobs pass. Critical 0, High 0, Medium 0, Low 4.

[Full report](feature-review-report.md) · [Gate decisions](gate-decisions.md) · [Artifact trace](artifact-trace.md).

Open nonblocking follow-ups:

- PM-01 (PM): archived PRD status/overview and persona reference.
- PM-02 (PM, with DevOps): canonical final-CI provenance still names PR49; actual PR50 success is captured in this review.
- QE-L1 (QE): relabel 88% as combined coverage; actual branch coverage is 83.87%.
- QE-L2 (QE/lifecycle coordinator): retain attempt-specific failed-gate diagnostic artifacts.

No repairs were made. Findings route back to the original lifecycle owners; no new mitigation acceptance was granted. The audit wrote only this base run and scratch files. The canonical feature package and all tracked source/planning files are unchanged. No review evidence manifest is created.
'''
(review / 'README.md').write_text(readme)

decisions = '''# F0064 Feature Review — Gate Decisions

Review run 2026-11-14-7cba50ff; product /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain; policy 2026-07-11.

| Gate | Decision | Decider | Evidence / rationale |
|---|---|---|---|
| FR0 | PASS | Codex / product-manager | action-context.md, exact aggregate changed-file list, merged PR metadata, approved latest-run pointer. Clean checkout already at PR50 merge. RUN_DEVOPS=auto -> yes. |
| FR1 | PASS with four Low findings | Six owning reviewer lanes | All 23 ACs supported by raw artifacts/source. Role sections and strict ownership are retained in the report and artifacts/reviews/. No repairs. |
| FR2 | PASS | Product Manager / validators | Five required driver operations pass. Durable individual stdout artifacts and lifecycle entries captured. Story-index currency has zero diff in an isolated copy. |
| FR3 | PASS | Each owning reviewer; PM aggregate check | Each lane records exact raw source/artifact citations, skip rationale and evidence self-review. Coverage counters recomputed; current final-head CI checked directly. |
| FR4 | TRULY DONE | Product Manager / computed review-family policy | Required evidence PASS; Critical=0, High=0, Medium=0, Low=4. artifacts/gate-policy.json. Low findings remain open and explicitly owned. |

This action requires a completion judgment, not a new operator approval. The original feature's G4 approve was checked only as process evidence. Raw evidence overrides summaries. No acceptance of a High/Critical finding or waiver of required validation was requested or recorded.

Exact execution timestamps (with timezone), commands, exit codes and output paths are in commands.log/lifecycle-gates.log; journal gate completion is in gate-state.json. The report includes applicability limitations and the missing historical retry-diagnostic finding.
'''
(review / 'gate-decisions.md').write_text(decisions)

trace = '''# F0064 Feature Review — Artifact Trace

## Bound roots and target

- /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain
- /home/gajap/uSandbox/repos/nebula/nebula-agents
- action-context.md
- artifacts/pr-metadata.json
- artifacts/diffs/changed-files.txt

## Primary read sources

- planning-mds/BLUEPRINT.md
- docs/agent-instructions.md
- .nebula-project.yaml
- docs/plan-review-checklist.md
- .agentignore
- planning-mds/features/archive/F0064-repository-instructions-and-planning-check-adoption/feature-assembly-plan.md
- planning-mds/features/archive/F0064-repository-instructions-and-planning-check-adoption/PRD.md
- planning-mds/features/archive/F0064-repository-instructions-and-planning-check-adoption/STATUS.md
- planning-mds/features/archive/F0064-repository-instructions-and-planning-check-adoption/README.md
- planning-mds/features/archive/F0064-repository-instructions-and-planning-check-adoption/GETTING-STARTED.md
- planning-mds/features/archive/F0064-repository-instructions-and-planning-check-adoption/F0064-S0001-declare-product-manifest.md
- planning-mds/features/archive/F0064-repository-instructions-and-planning-check-adoption/F0064-S0002-provide-agent-instructions-and-review-checklist.md
- planning-mds/features/archive/F0064-repository-instructions-and-planning-check-adoption/F0064-S0003-validate-plan-readiness-structure.md
- planning-mds/features/archive/F0064-repository-instructions-and-planning-check-adoption/F0064-S0004-enforce-checks-in-ci-and-document-setup.md
- planning-mds/features/TRACKER-GOVERNANCE.md
- planning-mds/features/REGISTRY.md
- planning-mds/features/ROADMAP.md
- planning-mds/features/STORY-INDEX.md
- planning-mds/kg-source/features/F0064.yaml
- planning-mds/kg-source/bindings/f0064.yaml
- planning-mds/knowledge-graph/code-index.yaml
- planning-mds/knowledge-graph/symbol-index.yaml
- planning-mds/knowledge-graph/feature-mappings.yaml
- planning-mds/architecture/feature-assembly-plan.md
- scripts/validation/validate_plan_readiness.py
- scripts/validation/tests/test_plan_readiness.py
- scripts/kg/validate_plan_compliance.py
- .github/workflows/ci-gates.yml
- CONTRIBUTING.md
- nebula.code-workspace
- docs/framework-adoption.md
- planning-mds/framework-adoption-plan.md
- planning-mds/operations/evidence/features/F0064-repository-instructions-and-planning-check-adoption/latest-run.json
- planning-mds/operations/evidence/runs/2026-11-14-3325803a/evidence-manifest.json
- planning-mds/operations/evidence/runs/2026-11-14-3325803a/test-plan.md
- planning-mds/operations/evidence/runs/2026-11-14-3325803a/test-execution-report.md
- planning-mds/operations/evidence/runs/2026-11-14-3325803a/coverage-report.md
- planning-mds/operations/evidence/runs/2026-11-14-3325803a/code-review-report.md
- planning-mds/operations/evidence/runs/2026-11-14-3325803a/deployability-check.md
- planning-mds/operations/evidence/runs/2026-11-14-3325803a/g1-runtime-preflight.md
- planning-mds/operations/evidence/runs/2026-11-14-3325803a/gate-decisions.md
- planning-mds/operations/evidence/runs/2026-11-14-3325803a/gate-state.json
- planning-mds/operations/evidence/runs/2026-11-14-3325803a/commands.log
- planning-mds/operations/evidence/runs/2026-11-14-3325803a/lifecycle-gates.log
- planning-mds/operations/evidence/runs/2026-11-14-3325803a/signoff-ledger.md
- planning-mds/operations/evidence/runs/2026-11-14-3325803a/kg-reconciliation.md
- planning-mds/operations/evidence/runs/2026-11-14-3325803a/pm-closeout.md
- planning-mds/operations/evidence/runs/2026-11-10-819c4124/gate-decisions.md

Exact additional raw file/line references, including test-results, coverage counters, context/hash pairs, negative executor JSON, historical gate retries and generated graph entries, are preserved in each owned reviewer section of feature-review-report.md and artifacts/reviews/. Commands.log retains exact targeted read commands; no canonical artifact directory was bulk-loaded.

## Review outputs

- README.md
- action-context.md
- artifact-trace.md
- gate-decisions.md
- commands.log
- lifecycle-gates.log
- gate-state.json
- feature-review-report.md
- artifacts/reviews/product-manager.md
- artifacts/reviews/architect.md
- artifacts/reviews/quality-engineer.md
- artifacts/reviews/code-reviewer.md
- artifacts/reviews/security.md
- artifacts/reviews/devops.md
- artifacts/ci-workflows.json
- artifacts/ci-pr50-jobs.json
- artifacts/validation/closeout.txt
- artifacts/validation/trackers.txt
- artifacts/validation/kg-symbols.txt
- artifacts/validation/kg-drift.txt
- artifacts/validation/templates.txt
- artifacts/story-index-currency.txt
- artifacts/diffs/story-index-currency.diff
- artifacts/gate-policy.json
- artifacts/read-only-check.json
- artifacts/review-summary.json
- artifacts/audit-support/review-exec.py
- artifacts/audit-support/story-currency.py
- artifacts/audit-support/finalize-review.py

## Scope and skipped layers

The six owning role sections provide individual skip reasons. No product UI, API, service, persistence, migration, authorization, model call or dependency change exists in the locked diff; no fresh product-runtime/browser/a11y/security-scanner suite was needed. Preserved feature tooling proof and final PR CI were checked directly. Story-index generation wrote only a temporary copy. No canonical feature evidence, tracker, KG, source or test was edited.
'''
(review / 'artifact-trace.md').write_text(trace)
context = (review / 'action-context.md').read_text()
context = context.replace('- FR0 scope locked; FR1 in progress.',
                          '- FR0–FR4 complete. Verdict: TRULY DONE. Required validators PASS; Critical 0, High 0, Medium 0, Low 4. Finished: ' + now + '.')
(review / 'action-context.md').write_text(context)

summary = dict(schema_version=1, action='feature-review', feature_id='F0064',
               review_run_id=review.name, feature_run_id='2026-11-14-3325803a',
               mode='closeout-audit', product_root=str(root), reviewed_prs=[48,49,50],
               diff_range='35631a459d2cfd6aa2c2f3d1627f23c31524d691..' + locked,
               verdict='TRULY DONE', required_validation='PASS',
               findings={'critical':0, 'high':0, 'medium':0, 'low':4},
               finding_ids=['PM-01','PM-02','QE-L1','QE-L2'],
               acceptance_criteria={'supported':23,'total':23},
               story_index_currency='byte-identical', read_only_verified=True,
               completed_at=now)
(review / 'artifacts/review-summary.json').write_text(json.dumps(summary, indent=2)+'\n')
support = review / 'artifacts/audit-support'
support.mkdir(parents=True, exist_ok=True)
for source, name in [('/tmp/f0064_review_exec.py','review-exec.py'),
                     ('/tmp/f0064_story_currency.py','story-currency.py'),
                     (__file__,'finalize-review.py')]:
    shutil.copyfile(source, support / name)
append_json(review / 'lifecycle-gates.log', dict(schema_version=1, timestamp=now,
            stage='FR4', result='TRULY DONE', critical=0, high=0, medium=0, low=4,
            evidence_validation='PASS', read_only=True,
            artifacts=['artifacts/gate-policy.json','artifacts/read-only-check.json',
                       'feature-review-report.md']))
print(json.dumps(summary, indent=2))
