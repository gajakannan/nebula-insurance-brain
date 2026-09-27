# Action Context

## Run Identity

- **action:** validate
- **contract:** Feature Evidence Contract, scope `base-run-only`, version 2026-07-11
- **run_id:** 2026-09-25-9aa87cdf (contract scheme: date + `secrets.token_hex(4)`)
- **run_folder:** `planning-mds/operations/evidence/runs/2026-09-25-9aa87cdf`
- **product_root:** `/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain`
- **framework:** `nebula-agents` at the product's pinned commit `c218bf1776f509a30f71967a1ee79879caa9a000` (checked out as a detached worktree; the sibling checkout's `main` is one commit ahead and was not used)
- **scm:** branch `docs/utopia-evolution`, head `b1f4357`, base `main` (`93cc8c1`)

## Inputs (V0 scope lock)

- **VALIDATION_SCOPE:** `all`
- **FEATURE_ID:** unset. The implementation lane uses the registry-wide commands.
- **STAGE:** `closeout` (default; unused because FEATURE_ID is unset)
- **EFFECTIVE_DATE:** framework default (2026-05-19); no override

## Lanes decided at V0

| Lane | Agent | Runs because | Preconditions |
|---|---|---|---|
| Requirements | product-manager | scope `all` | BLUEPRINT.md, REGISTRY.md, ROADMAP.md exist: yes |
| Architecture | architect | scope `all` | solution-ontology.yaml, canonical-nodes.yaml, feature-mappings.yaml exist: yes |
| Implementation (registry-wide validators) | product-manager (tool lane) | scope `all` | at least one completed-terminal feature in REGISTRY.md: yes (F0001, Done/archived) |

## Purpose

This run is a retroactive framework validation of branch `docs/utopia-evolution`. That branch was authored outside an action. It adds:

- ADR-0063 (accepted as direction) and ADR-0064 to ADR-0069 (Proposed);
- the F0066 feature reservation;
- scope amendments to 28 planned features, with their kg-source shard `governed_by` edges;
- ADR node shards, glossary terms, examples EX-SEM-001 to 011, and data-model and evaluation additions;
- in-place master blueprint revisions, and a recompiled knowledge graph.

The run gives the change an auditable validation record before integration.

## Assumptions

- No runtime code changed, so application-runtime execution is not required. The implementation lane is the framework validator set.
- Validators are tools; the PM and Architect reports carry the judgment.

## Scope Boundaries

- Read-only with respect to feature evidence packages.
- The only permitted mutation is the `v1-story-index` operation (trackers). Any resulting diff is reported.
- Findings are reported, not fixed, in this run. Fixes go back to the branch, followed by a rerun.

## Deviations from the generated prompt

- `init-run.py` requires `--feature`, and `validate` has no feature, so the six base run files and artifact subdirectories were created manually as `notes.session_setup` specifies. No `evidence-manifest.json` was created: `validate.md` §8/§14 says the manifest profile is feature/build only. The generated prompt's session-setup line asks for a manifest, which conflicts with the spec; this is recorded as a framework finding.
