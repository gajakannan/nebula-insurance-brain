# PostgreSQL identity CHECK proof

The same SQL defect is present in the plan at `feature-assembly-plan.md:186` and the delivered migration at `0012_f0007_factslot_identity.py:77`.

Successful read-only PostgreSQL SELECT evaluation of the exact delivered expression returned `t|t` for both a v1 NULL-fingerprint slot and a NULL-version row with populated v1 fields. Columns mean check_returns_unknown and postgres_check_accepts. No shared database rows were written.

Full query text is in this run's `artifacts/architect-probes.json`. Successful invocation details are recorded in the peer feature-review run `2026-11-09-8b8456df/artifacts/architect-postgres-proof.md`.
