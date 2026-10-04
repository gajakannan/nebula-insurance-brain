# Test Execution Report — F0003-postgresql-persistence run 2026-10-03-57d14a51

## Commands Executed

```text
- engine/.venv/bin/pytest -q engine/tests/contract/test_authx_kernel.py → exit 0 (15 passed)
- UV_CACHE_DIR=/tmp/nebula-uv-cache uv run --offline --project engine pytest -q engine/tests/integration/test_persistence_contract.py → exit 1 (workspace build could not resolve uncached setuptools>=68)
- engine/.venv/bin/pytest -q engine/tests/integration/test_persistence_contract.py engine/tests/integration/test_bitemporal_commit.py engine/tests/integration/test_commit_concurrency.py engine/tests/integration/test_outbox_replay.py → interrupted, exit 130; no completed report
- timeout 15s engine/.venv/bin/pytest -q engine/tests/integration/test_persistence_contract.py → exit 124; no completed report
```

Each command and exit code is recorded in `commands.log`.

## Pass/Fail Counts

| Lane | Total | Pass | Fail | Skip | Retries |
|---|---:|---:|---:|---:|---:|
| Contract (`test_authx_kernel.py`) | 15 | 15 | 0 | 0 | 0 |
| PostgreSQL integration | Not completed | Not established | Not established | Not established | 0 |

## Skipped Tests And Rationale

No completed PostgreSQL pytest summary was produced, so there is no reliable skip count. The command was stopped/timed out before pytest reported final counts.

## Raw Test Artifact Paths

- `artifacts/test-results/g2-contract.log`
- `artifacts/test-results/g2-persistence-contract.log`
- `artifacts/test-results/g2-persistence-integration.log`
- `artifacts/test-results/g2-uv-offline.log`
- `artifacts/test-results/g2-environment-blocker.md`

## Failed / Retried Command History

The offline `uv` attempt failed because the restricted cache lacks `setuptools>=68`. The engine virtualenv then ran the contract suite successfully. The PostgreSQL integration batch stopped producing output and was interrupted; a bounded rerun of the new direct PostgreSQL test timed out. A host socket probe raised `PermissionError`, and Docker API access from this sandbox was denied, so the live Compose database could not be used by pytest.

## AC Coverage Result

| Story | Outcome |
|---|---|
| F0003-S0001 | Plan inventory and ownership validated at G0; implementation signoff remains open. |
| F0003-S0002 | Partial/unverified: test sources inspected; PostgreSQL tests not executed. |
| F0003-S0003 | Partial/unverified: contract unit lane passed; temporal, exclusion, concurrency, audit, and outbox integration evidence is incomplete. |
| F0003-S0004 | Unverified: migration acceptance suite and clean PostgreSQL upgrade were not executed. |

## Result

Result: FAIL
