# Code Review Static Checks — F0003 run 2026-10-03-57d14a51

Product root: `/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain`

## Results

- `agents/code-reviewer/scripts/check-code-quality.py engine/tests/integration/test_persistence_contract.py` — PASS; TODO/FIXME count 0, no lines over 120 characters, file below 500 KB.
- `engine/.venv/bin/ruff check engine/tests/integration/test_persistence_contract.py` — PASS; all checks passed.
- `scripts/kg/diff-impact.py main...HEAD` — `affected_nodes: []`; the test path and evidence paths are unresolved by symbol bindings. The only code diff changes an existing test's context-manager formatting and introduces no symbols.
- `scripts/kg/lookup.py --file engine/tests/integration/test_persistence_contract.py` — no matched nodes or bindings.
- `scripts/kg/risk.py --file engine/tests/integration/test_persistence_contract.py` — no KG bindings, so no canonical-node risk score applies.

These are review checks, not additional test executions.
