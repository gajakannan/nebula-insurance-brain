import argparse
import json
from pathlib import Path
import re

P = Path('/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain')
R = P / 'planning-mds/operations/evidence/runs/2026-11-24-96b7f791'
p = argparse.ArgumentParser()
p.add_argument('--final', action='store_true')
a = p.parse_args()
identity = json.loads((R / 'artifacts/context/identity.json').read_text())
roles = ['pm', 'architect', 'qe', 'code-reviewer', 'security', 'devops']
sections = []
for name in roles:
    path = R / 'artifacts/role-reports' / (name + '.md')
    content = path.read_text()
    headings = [len(m.group(1)) for m in re.finditer(r'^(#+) ', content, re.M)]
    offset = 3 - min(headings)
    content = re.sub(r'^(#+)( )', lambda m: '#' * (len(m.group(1)) + offset) + ' ', content, flags=re.M)
    sections.append(content)
result = json.loads((R / 'artifacts/validators/results.json').read_text()) if a.final else None
decision = result['final_verdict'] if result else 'PENDING REQUIRED VALIDATION'
report = f'''# Feature Review — F0011: JSON Schema contract system

## Decision

**{decision}.** ''' + ('''Required evidence validation and all other required checks passed. No Critical or High finding remains. Two Medium and one Low documentation/evidence findings are nonblocking under the review-family policy; they remain explicitly open with their original owners.
''' if a.final and decision == 'TRULY DONE' else '''The six role reviews are complete. Required evidence validation must pass before any final completion verdict.
''') + f'''
- Product root: `{P}` (environment, normalized once).
- Mode: `closeout-audit`; canonical approved run: `2026-11-22-885e8734`.
- Review run: `{R.name}`; [merged implementation PR #64](https://github.com/gajakannan/nebula-insurance-brain/pull/64).
- Feature: `planning-mds/features/archive/F0011-json-schema-contract-system`.
- Immutable diff: `{identity['diff_range']}`; local HEAD matches its head.
- Complete changed set: `artifacts/diffs/changed-files.txt`, 586 paths with rename detection disabled (GitHub reports 571 with rename detection).
- RUN_DEVOPS: `yes`, resolved from `auto` because runtime, Docker and CI changed.

This verdict covers the approved F0011 implementation and its evidence. ADR-0079/0039 acceptance and production rollout remain separately scoped decisions. Fresh Docker execution was unavailable in this WSL session; checked raw feature-container artifacts, current-source hashes and successful exact-head CI provide runtime proof.

## Findings By Severity

Critical: **0**. High: **0**. Medium: **2**. Low: **1**.

| ID | Severity | Owner | Finding and raw evidence | Follow-up |
|---|---|---|---|---|
| FR-PM-M1 | Medium | Product Manager | Current status/signoff prose conflicts with completion. Archived `acceptance-criteria-checklist.md:8`, `PRD.md:187`, story S0001 `:20`/`:99`, and `README.md:5` retain Not Started/in-progress/pending text; actual STATUS, 30-row signoff ledger and raw tests support Done. | Reconcile current text or label retained planning history through PM-owned correction. |
| FR-PM-M2 | Medium | Product Manager / feature orchestrator | Canonical `evidence-manifest.json:15` and cited `artifacts/diffs/changed-files.txt` list426 paths; the complete PR contains586. One omitted actual change is `engine/tests/integration/test_temporal_migration.py`; the audit inspected and accepted its route-shape assertion change. Exact classifications: `artifacts/pa-scope-comparison.json`. | Finalize the original manifest/diff receipt, distinguishing committed changes from ignored transient evidence. |
| QE-L1 | Low | Quality Engineer | Canonical `test-execution-report.md:144` says86.0%, while raw `artifacts/coverage/changed-line-coverage.json:5` records1166/1350=86.37037%; `coverage-report.md:15` correctly rounds86.4%. | Correct the stale narrative percentage through QE-owned evidence maintenance. |

Feature-local references in FR-PM-M1 resolve under the archived feature path above. Canonical evidence references resolve under `planning-mds/operations/evidence/runs/2026-11-22-885e8734/`. Raw artifacts control each disagreement. No implementation, requirement, test, tracker, KG or canonical evidence repair was made. No High mitigation acceptance is required; the Medium/Low follow-ups are not treated as closed.

## Completion Checks

Six distinct role sections were reviewed in three concurrent reviewer tasks, within four available agent slots. Each section preserves role ownership and documents its FR3 evidence self-review.

| Role | Result | Principal checked evidence |
|---|---|---|
| Product Manager | Supported with2 Medium findings | All6 stories/41 ACs,30/30 signoffs, raw runtime proof, archive/trackers and actual complete diff. |
| Architect | PASS |21 source/publication hashes,114/114 new KG bindings, actual service/guard boundaries, source-current history receipts. |
| Quality Engineer | PASS with1 Low finding |1239 unit,83 PostgreSQL,443×3 conformance; Python1166/1350=86.37%, JS453/460=98.48%; source hashes match. |
| Code Reviewer | APPROVED | Actual changed implementation and CI repairs, generator/source-guard boundaries, original raw reprobes and failure-test bodies. |
| Security | PASS | Source READ ordering, transaction rollback, safe errors, explicit native boundary and four feature-scoped raw scan classes. |
| DevOps | PASS | Container build/install receipts, source freshness, coherent rollout/rollback scope and exact-head successful CI. |

''' + '\n\n'.join(sections) + '''

## Validation Evidence

'''
if result:
    report += '| Required check | Exit | Result | Output artifact |\n|---|---|---|---|\n'
    for check in result['checks']:
        report += f"| {check['name']} | {check['exit_code']} | {check['result']} | `{check['artifact']}` |\n"
    report += f'''
Severity arithmetic: `artifacts/validators/gate-policy.json`, produced by `gate_policy.py --profile review-family --variant feature` with zero Critical/High counts across every owner domain. The required-evidence status is **{result['required_validation']}**. The final verdict combines that prerequisite with the policy result; a required validation failure always forces NOT DONE.

Stock story-index CLI ran against a temporary mirror of all story files with the same relative paths. This preserves the prescribed currency check without writing the canonical STORY-INDEX. Generated bytes and its comparison are retained in `artifacts/validators/STORY-INDEX.generated.md` and `artifacts/diffs/story-index-currency.diff`.
'''
else:
    report += 'Pending FR2: closeout evidence, trackers, KG symbols, KG drift, framework templates and story-index currency.\n'
report += '''
## Artifact Trace

`artifact-trace.md` records input classes, generated review artifacts, connected GitHub sources, run environment and explicit omissions. Every lane names the exact raw evidence it checked. Shell commands and captured output paths are append-only in `commands.log`; gate execution and validation receipts are in `lifecycle-gates.log` and `gate-state.json`.

The original run and its latest-run pointer were read, never edited. Review-generated files remain under this review run; temporary audit helpers are under /tmp. Bootstrap command records were transparently appended retrospectively: their timestamps denote record time, as explained in `artifacts/context/bootstrap-telemetry-note.md`; subsequent records retain execution-start timestamps and output artifacts.
'''
(R / 'feature-review-report.md').write_text(report)
print(json.dumps({'report': str(R / 'feature-review-report.md'), 'decision': decision,
                  'role_sections': len(sections)}))
