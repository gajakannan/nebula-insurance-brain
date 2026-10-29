# Feature Evidence README — F0005-one-time-docling-ingestion run 2026-10-25-4020923b

## Run Summary

Feature action for F0005, run by the operator on 2026-10-25. The approved assembly plan is being checked before local qualification work; this run has not yet established runtime or release evidence.

## Status

Current state: `in-progress`; G0 passed and the manifest has advanced to `in-progress`.

## Evidence Index

- `evidence-manifest.json` — contract version 2026-07-11
- `action-context.md` — resolved root, run identity, inputs, assumptions, and scope
- `artifact-trace.md` — consulted planning artifacts and run evidence
- `gate-decisions.md` — gate decisions as they are evaluated
- `commands.log` — JSON Lines command record
- `lifecycle-gates.log` — gate validation results
- `g0-assembly-plan-validation.md` — G0 architect review

## Validation Summary

G0 passed on 2026-10-25 after correcting the missing Architect role result and durable diff artifact. G1 remains failed after Docker was started: Compose services are healthy and the Brain secret is now provisioned with mode `0600`, but CUDA and loopback access remain blocked. The latest stage validator is recorded in `lifecycle-gates.log`.

## Open Follow-ups

- G1 cannot proceed until this execution environment has GPU and loopback access and the Brain inference server is verifiably running with the pinned model. PostgreSQL and Authentik containers are healthy; the Brain secret is provisioned. No implementation tests ran.
- Resume the same run after restoring the documented runtime; do not create another run ID.
