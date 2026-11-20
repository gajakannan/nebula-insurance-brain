# Deployability Check — F0008 review remediation (run 2026-11-18-bce4909b)

- Role: DevOps
- Reviewer: Claude (Opus 5.5) / DevOps
- Date: 2026-11-18
- Verdict: PASS

## What deploys

- Migration `0015_f0008_split_lineage_same_slot.py` (`down_revision = "0014"`) adds one `SECURITY INVOKER` function and one BEFORE INSERT trigger.
  - Its preflight refuses to install over an existing cross-slot lineage row.
  - Its downgrade drops only those two objects.
- Engine code changes are in existing packages. No dependency, environment variable, port or container changes, and `uv.lock` is unchanged.
- **CI:** the existing F0008 step already runs every file that changed. No workflow edit is needed.

## Evidence

- Fresh database 0001→0015 rc=0: `command-output/fresh-db-upgrade-head.txt`.
- 0015 preflight refusal and up/down/up: `test_0015_*`.
- Full regression on 0015: 1085/0/0.

## Rollback

`alembic downgrade 0014` removes only the guard; the 0014 rollback rules are unchanged. F0011 must renumber its migration after 0015.
