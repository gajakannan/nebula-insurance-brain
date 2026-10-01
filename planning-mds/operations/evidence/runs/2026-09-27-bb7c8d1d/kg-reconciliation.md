# Knowledge-Graph Reconciliation — F0002 run 2026-09-27-bb7c8d1d

## Scope

- Feature ID: F0002
- Run ID: 2026-09-27-bb7c8d1d
- Date: 2026-09-28
- Reconciled by: Architect (agents/architect/SKILL.md, feature action G7)

## Binding Delta

The baseline is the G0 "Knowledge-Graph Binding Plan" in g0-assembly-plan-validation.md. The shard edits are kg-source/bindings/f0002.yaml (new) and kg-source/bindings/f0001.yaml (two F0001 capabilities updated in place).

| Capability / node | Bindings (as built) | G0-declared? | Action |
|---|---|---|---|
| capability:structural-tenancy-and-entity-identity | engine/packages/brain-domain/src/brain_domain/tenancy.py, engine/packages/brain-persistence/src/brain_persistence/tenancy.py, migrations 0005/0006/0007, scripts/dev/reconcile_authx.py | yes (0007 added by the G4 scope amendment) | added (f0002.yaml) |
| capability:credential-verification-and-principal-resolution | adds brain_security/identity_profile.py, brain_persistence/identity.py, config/authx-identity-profile.yaml | yes | updated (f0001.yaml) |
| capability:current-resource-scope | brain_persistence/authx.py, brain_persistence/grants.py, scripts/dev/revoke_membership.py | yes | added (f0002.yaml) |
| capability:authorization-enforcement | brain_security/evaluation.py and brain_domain/authx.py replace the deleted brain_security/authorization.py; casbin_adapter.py and the policies are kept | yes | updated (f0001.yaml); stale binding to the deleted file removed |
| capability:bounded-delegation | brain_security/delegation.py, scripts/dev/provision_delegation.py | yes | added (f0002.yaml) |
| capability:durable-authorization-decisions | brain_security/execution.py, brain_security/audit.py, brain_domain/audit.py | yes | added (f0002.yaml) |
| API routes, worker adapter, commit service, brain-jobs | brain_api/*, brain_worker/document_delivery.py, brain-temporal/**, brain-jobs/** | n/a | confirmed-existing-coverage (F0001 capability globs) |

The dev-only `engine/packages/brain-testing` package holds test fixtures, not a capability, so it is intentionally unbound.

## Canonical Nodes

No new canonical nodes were introduced; the implementation reuses the F0002 capability, entity, endpoint and schema nodes authored at plan time. Node notes changed from "planning contract only" to as-built descriptions: structural-tenancy-and-entity-identity, current-resource-scope, bounded-delegation, durable-authorization-decisions, authorization-enforcement.

Shared semantics touched in the Architect role: ADR-0061 and ADR-0062 are **Accepted, bounded to the F0002 scope** (their stated acceptance conditions are met by this run's evidence and signoffs; ADR-0042/0052/0053 stay Proposed). SOLUTION-PATTERNS §1 now names `AuthorizationExecution` / `execution.decide` as the enforcement point instead of the removed `AuthorizationService`. The v1 schema and API contract are unchanged.

## Validator Results

| Check | Command | Result |
|-------|---------|--------|
| compile | `scripts/kg/compile.py` | PASS (exit 0; the name-similarity warning is pre-existing) |
| symbol + decision regen/check | `validate.py --regenerate-symbols --check-symbols --regenerate-decisions --check-decisions` | PASS (exit 0); the index contains the new modules (for example execution.py 31 entries, brain_domain/authx.py 57) and no entries for the deleted authorization.py |
| drift | `validate.py --check-drift` | PASS (exit 0) |

`coverage-report.yaml` was **not** regenerated at this gate. That is deferred to G8, after the archive move.

## Handoff to Closeout

The semantic graph is green. PM closeout verifies it (without re-authoring), updates the feature shard's status/path for the archive move, recompiles, and regenerates coverage after the move.

Result: PASS
