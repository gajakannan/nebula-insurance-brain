# F0006 feature action — runtime blocked

- Run: `2026-11-02-5a00b0ff`
- NEBULA_PRODUCT_ROOT: `/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain` (shell environment, normalized by `_product_root.py`)
- Framework: `/home/gajap/uSandbox/repos/nebula/nebula-agents`
- Mode: `clean`; slice order: `assembly-plan`; prior completion run: none
- Recorded: 2026-11-02T20:49:04.283619+00:00
- Manifest: **draft**; no gate has passed and no approval is requested.

## Position and stop condition

Setup created this run and loaded product/framework context and the approved assembly plan.
The required runtime discovery failed before G0 validation or implementation. The operator
contract says to stop when **"Runtime preflight cannot be restored."** This session has no
usable Docker daemon, socket, or Windows CLI connection. The run is classified `runtime-blocked`.

G0 remains pending; G1 preflight has failed discovery evidence. G2–G8 remain pending. No stage
was bypassed or claimed complete. All five stories remain Not Started. No source code,
feature STATUS, contracts, schemas, trackers, defaults, or archived evidence were changed.
No compile, tests, lint, migration, security scan, or closeout was executed.

## Evidence

- [Runtime preflight](g1-runtime-preflight.md)
- [Execution position](feature-action-execution.md)
- [Docker discovery stdout](artifacts/test-results/runtime-discovery.stdout.txt)
- [Docker discovery stderr](artifacts/test-results/runtime-discovery.stderr.txt)
- [Endpoint discovery](artifacts/test-results/runtime-endpoints.json)
- [Windows CLI stdout](artifacts/test-results/runtime-windows-cli.stdout.txt)
- [Windows CLI stderr](artifacts/test-results/runtime-windows-cli.stderr.txt)
- [Startup command audit](artifacts/test-results/session-setup-audit.json)

## Resume prerequisites

Restore Docker Desktop WSL integration for this distro and ensure the agent session can
reach the daemon and start the project's application runtime containers. The Windows CLI
also fails its WSL transport in this session. Host-only tests cannot replace the required
application runtime evidence.

Reuse this run; do not initialize another F0006 feature-completion run. From the framework:

```bash
python3 agents/scripts/resume-brief.py --product-root /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain --run-id 2026-11-02-5a00b0ff
python3 agents/scripts/project_context.py --product-root /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain --action feature
```

Then restore and recheck runtime health, finish G0 validation against the approved plan,
and execute G0–G8 in order through `run-gate.py`. If setup repair is needed, use
`init-run.py --resume --run-id 2026-11-02-5a00b0ff --product-root /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain --action feature --feature F0006`.
No validator waiver or acceptance decision has been made.
