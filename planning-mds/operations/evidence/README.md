# Operations Evidence

This directory stores evidence packages produced by `nebula-agents` action runs against this product repo.

Effective `2026-05-19` (the framework default for the Feature Evidence Contract; see the framework `CONSUMER-CONTRACT.md`). Runs initialized on or after 2026-09-05 are stamped with the active policy version `2026-07-11` in `evidence-manifest.json`.

## Base Run Profile (§8)

Non-feature, manual, init, plan, and validate-action runs produce the base package only:

```text
planning-mds/operations/evidence/runs/{run-id}/
  README.md
  action-context.md
  artifact-trace.md
  gate-decisions.md
  commands.log
  lifecycle-gates.log
```

Base runs do not require an `evidence-manifest.json`. The validate action additionally writes `pm-validation-report.md`, `architect-validation-report.md`, and `implementation-validation-report.md` alongside the base files.

## Feature Evidence Profile (§9, §10)

`feature` and `build` closeouts write the full artifact matrix:

```text
planning-mds/operations/evidence/features/F####-{slug}/
  latest-run.json                       # only after PM closeout + supersession patch

planning-mds/operations/evidence/runs/{run-id}/
  <§8 base files>
  evidence-manifest.json                # §11 schema
  feature-action-execution.md
  g0-assembly-plan-validation.md
  g1-runtime-preflight.md               # when runtime_bearing = true
  g2-self-review.md
  test-plan.md
  test-execution-report.md
  coverage-report.md
  deployability-check.md
  code-review-report.md
  security-review-report.md             # when security_sensitive_scope or required
  signoff-ledger.md
  pm-closeout.md
  kg-reconciliation.md                  # G7
  artifacts/{coverage,diffs,test-results,security,screenshots}/
```

Run ID format: `YYYY-MM-DD-XXXXXXXX` (`secrets.token_hex(4)` suffix, never uuid4). Templates for each artifact live under `nebula-agents/agents/templates/`.

## Effective-Date Boundary (§6)

- This product has no pre-contract features: every feature that reaches `Done`, `Completed`, or `Archived` requires the canonical feature evidence package.
- Retired features (`Terminal Status = Abandoned` or `Superseded`) are registry-only and never satisfy completion-evidence requirements.

## Path Class Extensions (§7)

The framework default path classes (in `nebula-agents/agents/product-manager/scripts/validate-feature-evidence.py` `DEFAULT_PATH_CLASSES`) cover `engine/**` and `experience/**`, plus `**/migrations/**`, container and CI files, and capitalized `Auth*`, `Identity*`, `Permissions`, `Security`, and `Secrets` directories. This product extends them additively as declared in `planning-mds/BLUEPRINT.md` section 2.4:

| Path class (glob) | Forces |
|-------------------|--------|
| `neuron/**` | `runtime_bearing = true` |
| `neuron/**/migrations/**` | `runtime_bearing = true` and `deployment_config_changed = true` |
| `ontology/**` | `runtime_bearing = true` |
| `profiles/**` | `runtime_bearing = true` |
| `schemas/**` | `runtime_bearing = true` |
| `knowledge-packs/**` | `runtime_bearing = true` |
| `integrations/label-studio/**` | `runtime_bearing = true` and `deployment_config_changed = true` |
| `golden-corpus/**` | `runtime_bearing = true` |
| `**/brain_security/**` | `security_sensitive_scope = true` |
| `**/brain-security/**` | `security_sensitive_scope = true` |
| `**/auth/**` | `security_sensitive_scope = true` |
| `**/authz/**` | `security_sensitive_scope = true` |
| `**/identity/**` | `security_sensitive_scope = true` |
| `**/principals/**` | `security_sensitive_scope = true` |

Rationale: `neuron/` hosts the AI and semantic runtime (Docling ingestion, extraction, interpretation, conversation, learning, MCP tools) and is runtime-bearing; the authored semantic assets (`ontology/`, `profiles/`, `schemas/`, `knowledge-packs/`) drive interpretation at runtime; Label Studio integration changes alter deployment topology; the Golden Corpus is executable test input; Python security and identity packages use lowercase directory names that the capitalized framework defaults do not match. The extension is additive; framework defaults are not overridden (`path_class_extension_conflict_fails`).

## Global Lanes (§20)

- `planning-mds/operations/evidence/frontend-quality/` is the global frontend quality lane once `experience/` exists; the lifecycle gate consumes its `latest-run.json`.
- `planning-mds/operations/evidence/frontend-ux/` is the rolling UX audit lane (`ux-audit-YYYY-MM-DD.md`).

Both lanes may be referenced from a feature evidence package via `manifest.global_evidence_refs`. They do not substitute for feature-level role reports. Neither lane exists yet.

## Validators

Run from the framework repo (`nebula-agents`) with `NEBULA_PRODUCT_ROOT` exported:

```text
python3 agents/product-manager/scripts/validate-trackers.py --product-root /path/to/nebula-insurance-brain
python3 agents/product-manager/scripts/validate-feature-evidence.py --product-root /path/to/nebula-insurance-brain --json
```

Closeout (`--stage closeout`) is run by the closeout action after tracker results are appended to `lifecycle-gates.log`.

## Runs

| Run | Action | Scope | Outcome |
|-----|--------|-------|---------|
| `runs/2026-09-05-6823e66e/` | init | bootstrap | PASS (I0 to I6; five I6 validators exit 0) |
