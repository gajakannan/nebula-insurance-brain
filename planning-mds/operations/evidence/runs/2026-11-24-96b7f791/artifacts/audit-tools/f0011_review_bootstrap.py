"""Append transparent retrospective records for setup commands issued before the log existed."""
import datetime as dt
import json
from pathlib import Path

W = '/home/gajap/uSandbox/repos/nebula'
F = W + '/nebula-agents'
P = W + '/nebula-insurance-brain'
R = Path(P) / 'planning-mds/operations/evidence/runs/2026-11-24-96b7f791'
records = [
 (W, 'printenv NEBULA_PRODUCT_ROOT', 0),
 (W, 'python3 agents/scripts/_product_root.py --product-root ' + P, 2),
 (W, 'printenv PR_URL FEATURE_ID MODE DIFF_RANGE FEATURE_RUN_ID RUN_DEVOPS', 1),
 (W, "rg --files --hidden -g _product_root.py -g AGENTS.md -g '!node_modules' -g '!.git'", 0),
 (F, 'python3 agents/scripts/_product_root.py --product-root ' + P, 0),
 (F, 'python3 agents/scripts/project_context.py --product-root ' + P + ' --action feature-review', 0),
 (F, 'python3 agents/scripts/project_context.py --product-root ' + P + ' --action feature-review', 0),
 (P, 'git status --short --branch', 0),
 (P, "rg -n 'F0011' planning-mds/features/REGISTRY.md", 0),
 (F, 'cat agents/ROUTER.md agents/agent-map.yaml agents/docs/AGENT-USE.md agents/docs/PROJECT-EXTENSIONS.md', 0),
 (F, 'cat agents/actions/feature-review.md', 0),
 (P, 'git remote get-url origin', 0),
 (P, 'cat planning-mds/operations/evidence/features/F0011-json-schema-contract-system/latest-run.json', 0),
 (F, 'cat agents/ROUTER.md agents/agent-map.yaml', 0),
 (F, 'cat agents/actions/feature.md', 0),
 (P, "sed -n '240,370p' planning-mds/BLUEPRINT.md", 0),
 (F, 'cat agents/scripts/init-run.py', 0),
 (F, 'python3 agents/scripts/run-gate.py --help', 0),
 (F, "python3 -c 'import secrets; print(secrets.token_hex(4))'", 0),
 (F, 'python3 agents/scripts/init-run.py --product-root ' + P + ' --action feature-review --feature F0011 --run-id 2026-11-24-96b7f791 --json', 0),
 (F, "rg -n '^#{1,4} |schema_version|\"timestamp\"|\"artifacts\"|\"redactions\"' agents/docs/AGENT-OPS.md", 0),
 (P, 'cat planning-mds/operations/evidence/runs/2026-11-22-885e8734/evidence-manifest.json .agentignore', 0),
 (P, 'rg --files planning-mds/features/archive/F0011-json-schema-contract-system', 0),
]
marker = R / 'artifacts/context/bootstrap-telemetry-note.md'
if marker.exists():
    raise SystemExit('Bootstrap records already appended; refusing duplication')
timestamp = dt.datetime.now().astimezone().isoformat()
with (R / 'commands.log').open('a') as log:
    for cwd, command, code in records:
        log.write(json.dumps(dict(schema_version=1, timestamp=timestamp, cwd=cwd, command=command,
                                 exit_code=code, artifacts=[], redactions=[])) + '\n')
marker.write_text('''# Bootstrap telemetry provenance

The 23 commands listed by /tmp/f0011_review_bootstrap.py ran before the review command wrapper was installed. They were appended retrospectively from the tool transcript. Their timestamp is the append time, not a reconstructed execution time. Exit codes are the observed tool results. No command was re-executed to manufacture setup history. Later command records use execution-start timestamps and retain captured output artifacts.

The initial resolver failed because the session started in the common parent rather than the framework checkout. Framework discovery then located nebula-agents; the product selection remained the same explicit environment value throughout. The run ID was minted exactly once using secrets.token_hex(4).
''')
print(json.dumps({'retrospective_bootstrap_records': len(records), 'timestamp_semantics': 'record-append time'}))
