import json
import sys
from pathlib import Path
sys.path.insert(0, '/tmp')
from f0008_review_exec_d34a095e import ROOT, RUN

findings = [
    {'id':'CR-F8-01','severity':'critical','owner':'code-reviewer','title':'Commit response cannot satisfy S0002 AC7; conflicting API scope has no recorded reconciliation','raw':'engine/apps/api/src/brain_api/schemas/facts.py:47; engine/apps/api/src/brain_api/routes/facts.py:152; planning-mds/features/archive/F0008-bitemporal-canonical-facts/F0008-S0002-distinguish-open-bounded-and-unknown-ends.md:28'},
    {'id':'FR-ARCH-M1','severity':'medium','owner':'architect','title':'Legacy GET emits temporal:null against the new object-only contract','raw':'planning-mds/api/brain-api.yaml:694; engine/apps/api/src/brain_api/schemas/facts.py:84; engine/tests/integration/test_temporal_reads.py:304'},
    {'id':'QE-M1','severity':'medium','owner':'quality-engineer','title':'Concurrency proof counts only successful audit rows; literal zero-audit loser criterion remains unresolved','raw':'planning-mds/features/archive/F0008-bitemporal-canonical-facts/F0008-S0004-enforce-temporal-integrity-under-concurrency.md:22; engine/tests/integration/test_temporal_concurrency.py:52; engine/packages/brain-security/src/brain_security/execution.py:480'},
    {'id':'PM-M1','severity':'medium','owner':'product-manager','title':'Exact F0018 carry-overs are absent from receiving planning inputs; current refusal-reason wording is stale','raw':'planning-mds/operations/evidence/runs/2026-11-17-1a4ae2f0/pm-closeout.md:30; planning-mds/kg-source/features/F0018.yaml:31'},
    {'id':'FR-ARCH-L1','severity':'low','owner':'architect','title':'ADR prose conflicts with current date-selection and remainder timestamp semantics','raw':'planning-mds/architecture/decisions/ADR-0078-bitemporal-version-contract-and-close-only-immutability.md:111; engine/packages/brain-persistence/src/brain_persistence/repositories.py:533; engine/packages/brain-temporal/src/brain_temporal/commit.py:268'},
    {'id':'FR-ARCH-L2','severity':'low','owner':'architect','title':'Direct-insert predecessor lineage lacks same-slot binding','raw':'engine/migrations/versions/0014_f0008_bitemporal_contract.py:175; engine/migrations/versions/0014_f0008_bitemporal_contract.py:331'},
    {'id':'QE-L1','severity':'low','owner':'quality-engineer','title':'Supplemental repeat/no-database execution claims and report dates lack their cited raw support','raw':'planning-mds/operations/evidence/runs/2026-11-17-1a4ae2f0/test-execution-report.md:24; planning-mds/operations/evidence/runs/2026-11-17-1a4ae2f0/commands.log:16; planning-mds/operations/evidence/runs/2026-11-17-1a4ae2f0/artifacts/test-results/g3-full-engine-regression.xml:1'},
    {'id':'PM-L1','severity':'low','owner':'product-manager','title':'Manifest changed_paths inventory differs from the actual locked diff','raw':'planning-mds/operations/evidence/runs/2026-11-17-1a4ae2f0/evidence-manifest.json:15; artifacts/diffs/manifest-scope-drift.json'},
    {'id':'PM-L2','severity':'low','owner':'product-manager','title':'Feature status Last Updated predates recorded closeout','raw':'planning-mds/features/archive/F0008-bitemporal-canonical-facts/STATUS.md:4'},
    {'id':'SEC-F8-L1','severity':'low','owner':'security','title':'Manifest SAST clean label hides seven safely triaged raw findings','raw':'planning-mds/operations/evidence/runs/2026-11-17-1a4ae2f0/evidence-manifest.json:318; planning-mds/operations/evidence/runs/2026-11-17-1a4ae2f0/artifacts/security/sast/sast-semgrep-20261117-052326.sarif#/runs/0/results'},
]
(RUN / 'artifacts/review/findings.json').write_text(json.dumps(findings, indent=2)+'\n')
final = (RUN / 'artifacts/test-results/fr4-policy.json').exists()
validation = (RUN / 'artifacts/test-results/fr2-summary.json')
validation_data = json.loads(validation.read_text()) if validation.exists() else None
state = 'NOT DONE' if final else 'Pending FR2–FR4; substantive completion blocker established at FR1'
parts = [f'''# Feature Review — F0008 Bitemporal canonical facts

## Decision

**{state}.** Mode: closeout-audit. Audited approved run: `2026-11-17-1a4ae2f0`; review run: `2026-11-18-d34a095e`; product root: `{ROOT}`. Locked diff: `2badb9ad2756f38ee9a1d84930787a3df989a245..339c9209385290247c01d1eea97a7c2c8b47fada` (135 paths). DevOps: yes. No implementation or canonical feature evidence was changed.

One Critical completion finding remains: the delivered commit response omits temporal metadata required by S0002 AC7, while S0007 limits API scope to request/read changes. PM and Architect must explicitly reconcile the requirement and prove the agreed behavior before the feature can be called complete. Critical is the Code Reviewer skill's classification for an unmet acceptance criterion; no Critical security exploit was established.

The raw artifacts substantiate **1,081 passing engine tests**, zero failures/errors/skips, and **695/709 changed executable production lines covered (98.025388%, floor 80%)**. Nevertheless, only **44/46 criteria are verified**: S0002 AC7 and S0004 AC1's losing-audit clause remain unresolved. The blanket 46/46 completion claim is not adopted. Existing signoffs and operator feature approval remain historical provenance and do not override contradictory raw evidence.

Counts: **Critical 1; High 0; Medium 3; Low 6.** The FR4 policy input includes each owning domain once. No new mitigation acceptance or calendar deadline is fabricated. Repair routes: original feature/review/test/closeout owners; never this read-only review.

## Findings By Severity

| ID | Severity | Owner | Finding and exact evidence |
|---|---|---|---|
''']
for finding in findings:
    refs = '; '.join('`'+p+'`' for p in finding['raw'].split('; '))
    parts.append(f"| {finding['id']} | {finding['severity'].title()} | {finding['owner']} | {finding['title']}. {refs} |\n")
parts.append('''
Detailed triggers, impact, scope boundaries and owning repair routes appear in the role-owned sections below. The shared CR-F8-01 is counted only in Code Review; QE and Architect references do not add severity counts. The accepted local superuser residual, production-role work and formal ADR acceptance are disclosed separately and are not reopened as new findings.

## Completion Checks

| Role | Result |
|---|---|
| Product Manager | Provenance/trackers align structurally; completion claim must be reconciled with raw AC gaps. 1 Medium, 2 Low. |
| Architect | Design largely implemented; new legacy-read schema mismatch and two guard/prose follow-ups. 1 Medium, 2 Low. |
| Quality Engineer | Raw execution/coverage pass; 44/46 criteria verified, two unresolved; unsupported supplemental claims disclosed. 1 Medium, 1 Low. |
| Code Reviewer | REQUEST CHANGES; one Critical unmet-AC/reconciliation finding. |
| Security | PASS WITH RECOMMENDATIONS for scoped controls; one Low raw-SAST labeling mismatch. |
| DevOps | PASS for declared local runtime; no new deployment finding. No production rollout or live daemon state asserted. |

All role lanes ran concurrently within available execution slots, with PM in the parent, Architect/DevOps sharing one reviewer, QE one, and Code/Security one. Each role owns its findings and section. All reviewers checked raw source/artifact paths; no global evidence lane replaces feature-scoped evidence.

''')
for section in ['product-manager.md','architect.md','quality-engineer.md','code-reviewer.md','security.md','devops.md']:
    parts.append((RUN / 'artifacts/review' / section).read_text()+'\n\n')
parts.append('## Validation Evidence\n\n')
if validation_data:
    parts.append('| Required check | Exit | Result | Artifact |\n|---|---|---|---|\n')
    for item in validation_data['checks']:
        parts.append(f"| {item['name']} | {item['exit_code']} | {item['result']} | `{item['artifact']}` |\n")
    parts.append('\nRequired evidence validation: **'+validation_data['result']+'**. Structural validation cannot settle a semantic AC conflict or a missing response field.\n\n')
else:
    parts.append('FR2 pending. No final completion verdict has been computed.\n\n')
if final:
    policy = json.loads((RUN / 'artifacts/test-results/fr4-policy.json').read_text())
    parts.append('Policy: `gate_policy.py --profile review-family --variant feature`; computed status **'+policy['status']+'**, totals '+json.dumps(policy['totals'])+'. Input and output are `artifacts/test-results/fr4-policy.json` and `commands.log`. Validation PASS is required for any done outcome; a Critical finding independently forces NOT DONE.\n\n')
parts.append('''## Artifact Trace

- Input binding and assumptions: `action-context.md`; product instructions: `artifacts/review/product-context.txt`.
- Source inventory, exact implementation patch and pre-existing untracked files: `artifacts/diffs/changed-files.txt`, `implementation.diff`, `initial-working-tree.txt`. No tracked edits existed at start; pre-existing audit `2026-11-18-a3709ba0` was preserved and its verdict was not treated as completion proof.
- Raw evidence entry points: `planning-mds/operations/evidence/features/F0008-bitemporal-canonical-facts/latest-run.json` and selected run's `evidence-manifest.json`. Role sections cite precise raw evidence reached from that manifest, including JUnit, JSON coverage, runtime/migration probes and four final scanner outputs. `CAN/` and ellipses in role tables refer to that selected canonical run; bare feature story names refer to `planning-mds/features/archive/F0008-bitemporal-canonical-facts/`.
- Actual response-model and schema diagnostics: `artifacts/review/code-response-probe.json`, `architect-temporal-null-schema.json`. Independent execution/coverage arithmetic: `qe-raw-artifact-check.json`. Signoff row comparison: `pm-source-checks.json`.
- Currency check: same story generator on byte-identical story files at identical relative paths in a temporary mirror, with the canonical product root passed explicitly. Original STORY-INDEX and feature files are never regenerated in place. The resulting diff and hashes are retained under `artifacts/diffs/fr2-story-index-currency.diff` and `artifacts/test-results/fr2-story-index-currency.json`.
- Protected canonical inputs were hashed before review; end-of-run hashes and tracked Git state establish that no source/evidence/tracker/KG repair occurred. Audit output is confined to this review run and /tmp.
- Gate procedure: `gate-decisions.md`, `gate-state.json`, `lifecycle-gates.log`. Shell commands: `commands.log`; retrospective bootstrap rows explicitly identify their recording-time limitation. Role-specific probes and reads are logged with rebinding of the canonical root.
- Self-review: every owned role section includes FR3 evidence and omission checks. No new broad regression or scanner run is claimed. UI, AI, live OIDC and production-role/deployment limits are justified in the relevant sections.
''')
(RUN / 'feature-review-report.md').write_text(''.join(parts))
print(json.dumps({'report': str(RUN / 'feature-review-report.md'), 'state': state, 'findings': len(findings)}))
