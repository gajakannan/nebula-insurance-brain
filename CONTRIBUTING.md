# Contributing

Read [README.md](README.md), [the blueprint](planning-mds/BLUEPRINT.md), and [local agent instructions](docs/agent-instructions.md). Keep product requirements and validation scripts in this repository. Generic framework changes belong in the sibling `nebula-agents` repository.

## Install planning tooling

From `nebula-insurance-brain/`, use Python 3.12 or newer:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[test]'
git config core.hooksPath .githooks
git config merge.ours.driver true
```

These are the planning-tool dependencies; the future application runtime requires the Python version specified in the blueprint.

## Product checks

```bash
.venv/bin/python scripts/run-lifecycle-gates.py
.venv/bin/python scripts/validation/validate_plan_readiness.py --plan-scope project --target project
.venv/bin/python -m pytest scripts/validation/tests
```

The copied KG tooling suite is separate: `.venv/bin/python -m pytest scripts/kg/tests`. Existing failures in framework-specific lookup fixtures are tracked in the adoption plan and do not represent completed runtime features.

For framework checks, set the product identity and run from the sibling framework:

```bash
export NEBULA_PRODUCT_ROOT="$(pwd)"
cd ../nebula-agents
python3 agents/product-manager/scripts/validate-trackers.py --product-root "$NEBULA_PRODUCT_ROOT"
python3 agents/product-manager/scripts/validate-stories.py --product-root "$NEBULA_PRODUCT_ROOT"
python3 agents/product-manager/scripts/validate-feature-evidence.py --product-root "$NEBULA_PRODUCT_ROOT"
```

With the project-extension framework revision installed, load the local instruction text before action work:

```bash
python3 agents/scripts/project_context.py --product-root "$NEBULA_PRODUCT_ROOT" --action plan-review
python3 agents/scripts/run-gate.py --product-root "$NEBULA_PRODUCT_ROOT" --action plan-review --plan-scope feature --target F0001 --list
```

Use the normal action procedure and run ID for gate execution. A paused checkpoint is not an approval, and a structural validator pass is not a readiness judgment.

## Changes and Git

- Work on a descriptive branch and keep the diff focused.
- Edit authored KG shards, then regenerate projections and trackers. Follow `planning-mds/features/TRACKER-GOVERNANCE.md`.
- Include scope, validation results, and outstanding findings with a change.
- Run Git from this repository, or use `git -C nebula-insurance-brain ...` from the parent workspace. The parent `nebula/` folder contains several independent repositories.
- New files appear under `git status --short --untracked-files=all`. Plain `git diff` only shows tracked changes; review new files before explicitly staging them.

## Explain semantic changes with examples

Start with the [worked GL case](planning-mds/examples/neurosymbolic-gl/README.md). Each new or changed concept needs a glossary definition, worked and boundary examples, and links to its owning contract and story in the [coverage map](planning-mds/examples/README.md). Label delivery phase and synthetic versus observed output. Run `python3 scripts/validation/validate_semantic_examples.py` for the structured teaching artifacts. Runtime delivery adds a verified reproduction command and independently expected outcomes; documentation fixtures stay outside the frozen holdout.
