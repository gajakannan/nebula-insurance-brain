import datetime
import json
import sys
sys.path.insert(0, '/tmp')
from f0008_review_exec_d34a095e import ROOT, FRAMEWORK, RUN, append

# Run-scoped logging cannot exist before init-run. Preserve discovery commands
# retrospectively and distinguish recording time from unavailable execution time.
commands = [
    (ROOT.parent, "python3 -c 'import json, os; keys = (\"NEBULA_PRODUCT_ROOT\", \"PR_URL\", \"FEATURE_ID\", \"MODE\", \"DIFF_RANGE\", \"FEATURE_RUN_ID\", \"RUN_DEVOPS\"); print(json.dumps({key: os.environ.get(key) for key in keys}, indent=2))'", 0),
    (ROOT.parent, "rg --files --hidden -g 'AGENTS.md' -g '_product_root.py' -g '!**/.git/**' -g '!**/node_modules/**' -g '!**/.venv/**'", 0),
    (FRAMEWORK, f'python3 agents/scripts/_product_root.py --product-root {ROOT}', 0),
    (FRAMEWORK, f'python3 agents/scripts/project_context.py --product-root {ROOT} --action feature-review', 0),
    (ROOT.parent, "python3 -c 'from pathlib import Path; roots = (Path(\"/AGENTS.md\"), Path(\"/home/AGENTS.md\"), Path(\"/home/gajap/AGENTS.md\"), Path(\"/home/gajap/uSandbox/AGENTS.md\"), Path(\"/home/gajap/uSandbox/repos/AGENTS.md\"), Path(\"/home/gajap/uSandbox/repos/nebula/AGENTS.md\"), Path(\"/home/gajap/uSandbox/repos/nebula/nebula-agents/AGENTS.md\"), Path(\"/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain/AGENTS.md\")); [(print(str(p)), print(p.read_text())) for p in roots if p.is_file()]'", 0),
    (FRAMEWORK, 'cat agents/ROUTER.md agents/agent-map.yaml agents/docs/AGENT-USE.md agents/docs/PROJECT-EXTENSIONS.md agents/actions/feature-review.md agents/actions/feature.md', 0),
    (FRAMEWORK, 'cat agents/actions/feature-review.md', 0),
    (FRAMEWORK, "sed -n '1,240p' agents/scripts/init-run.py", 0),
    (ROOT, 'git status --short; git branch --show-current; cat .agentignore; rg -n \'F0008\' planning-mds/features/REGISTRY.md; cat planning-mds/operations/evidence/README.md; cat planning-mds/operations/evidence/features/F0008-bitemporal-canonical-facts/latest-run.json', 0),
    (FRAMEWORK, f'python3 agents/scripts/resume-brief.py --product-root {ROOT} --run-id 2026-11-18-a3709ba0', 2),
    (ROOT, 'cat planning-mds/operations/evidence/runs/2026-11-18-a3709ba0/action-context.md planning-mds/operations/evidence/runs/2026-11-18-a3709ba0/README.md planning-mds/operations/evidence/runs/2026-11-17-1a4ae2f0/evidence-manifest.json', 0),
    (FRAMEWORK, "cat agents/docs/AGENT-USE.md agents/docs/PROJECT-EXTENSIONS.md; sed -n '1,250p' agents/scripts/run-gate.py; cat agents/scripts/gate_policy.py", 0),
    (FRAMEWORK, "sed -n '240,430p' agents/scripts/init-run.py; sed -n '520,780p' agents/scripts/run-gate.py; cat agents/product-manager/SKILL.md agents/architect/SKILL.md agents/quality-engineer/SKILL.md agents/code-reviewer/SKILL.md agents/security/SKILL.md agents/devops/SKILL.md", 0),
    (FRAMEWORK, 'python3 -c \'import secrets; from datetime import date; print(date.today().isoformat() + "-" + secrets.token_hex(4))\'', 0),
]
stamp = datetime.datetime.now().astimezone().isoformat()
for cwd, command, code in commands:
    append(RUN / 'commands.log', dict(schema_version=1, timestamp=stamp, cwd=str(cwd),
           command=command, exit_code=code, artifacts=[], redactions=[],
           recording_note='Retrospective bootstrap record; timestamp is recording time, not original execution time. Original execution order is the order of these bootstrap records.'))
with (RUN / 'action-context.md').open('a') as handle:
    handle.write('\n## Bootstrap telemetry\n\nCommands before run creation are preserved retrospectively in commands.log; their recording_note explicitly distinguishes recording time from unavailable execution timestamps. All commands after setup are logged by the shared wrapper at execution. Some large initial context output was truncated by the terminal; lane-specific instructions and exact artifacts were subsequently retrieved in smaller reads.\n')
print(f'Recorded {len(commands)} pre-setup commands transparently.')
