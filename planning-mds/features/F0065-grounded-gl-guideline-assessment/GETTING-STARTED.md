# F0065 — Getting started

## Read first

1. [Synthetic GL walkthrough](../../examples/neurosymbolic-gl/README.md): follow one policy through source, assertion, fact, rule, and assessment.
2. [PRD](PRD.md) and [assessment contract](assessment-contract.md): scope and outcome/error rules.
3. [Assembly plan](feature-assembly-plan.md): upstream contracts, ownership, and proof sequence.
4. [STATUS.md](STATUS.md): all runtime stories remain unstarted.

## Planning checks available now

From the Brain repository with its planning dependencies installed:

```bash
python3 scripts/validation/validate_semantic_examples.py
python3 scripts/validation/validate_plan_readiness.py --plan-scope feature --target F0065
python3 scripts/run-lifecycle-gates.py
```

The example check verifies shape and local links/references. It does not execute Docling, a neural model, canonical commits, or a rule engine.

## Runtime prerequisites and reproduction

F0001 and the canonical/temporal/evidence prerequisites in the assembly plan must be delivered. S0006 then documents and verifies the actual command that loads the synthetic source package, runs interpretation and review, accepts facts, and assesses them in F0024/F0025. No runtime command is available today. Preserve independently authored expected outcomes, record observed outputs separately, and keep this development fixture out of the frozen holdout.
