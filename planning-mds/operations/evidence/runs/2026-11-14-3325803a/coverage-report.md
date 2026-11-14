# Coverage Report — F0064

Role: Quality Engineer (Claude Opus 5.5). Date: 2026-11-14.

## Coverage Target And Actual Per Layer

| Layer | Changed executable lines | Coverage | Note |
|---|---|---|---|
| Backend (`engine/`) | 0 | n/a | Not in scope |
| Frontend (`experience/`) | 0 | n/a | Not in scope |
| AI (`neuron/`) | 0 | n/a | Not in scope |
| Repository tooling under verification: `scripts/validation/validate_plan_readiness.py` | 0 changed (delivered 2026-09-07) | **88% branch coverage** (127 statements, 62 branches) | Above the contract floor |

This run changes no executable code; only Markdown documentation and planning files changed (`artifacts/diffs/changed-files.txt`). Coverage was therefore measured on the delivered validator that S0003 verifies. The measurement combines the fixture suite with the S0003 CLI invocations: the real tree, the four invalid invocations, feature and feature-set targets, an unregistered target, and copies with a missing checklist rule or an Active row without a PRD. The fixture suite alone covers 68%, because it calls `validate()` directly and bypasses `main()`, the exit-code contract that the CLI runs exercise.

Uncovered lines 21, 38, 57, 61–62, 65, 68, 82–83, 123, 127 and 129 are defensive error branches: path escape, empty artifact, a malformed or duplicate checklist row, an unknown owner, an invalid registry entry, and link-escape or external-link handling. They were read and found consistent with the S0003 contract. No waiver is needed.

## Raw Artifact Paths

- `artifacts/coverage/combined-coverage.sh` — reproducible measurement script (coverage 7.10.7 and pytest 9.0.3 through `uv run --no-project`; the repository `.venv` is untouched)
- `artifacts/coverage/combined-coverage.txt` / `combined-coverage.json` — combined report (88%)
- `artifacts/coverage/validator-coverage.txt` / `validator-coverage.json` — fixture-only report (68%)

## Result

PASS
