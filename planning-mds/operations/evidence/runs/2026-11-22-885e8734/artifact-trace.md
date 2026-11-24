# Artifact Trace — F0011 run 2026-11-22-885e8734

## Artifacts Read

- Framework ROUTER, agent-map, AGENT-USE, PROJECT-EXTENSIONS, feature action and applicable role skills.
- Product BLUEPRINT and docs/agent-instructions.md via project_context.py; unchanged on resume.
- F0011 approved assembly plan, six stories, PRD, design, inventory, profile and examples.
- Lookup-selected source schemas, governing ADR-0079 and SOLUTION-PATTERNS.
- Four prior features' exact contract-examples.json paths resolved through their KG shards.
- Evidence manifest scan restricted to F0011 concurrency/supersession validation.
- Exact prior F0008 G1 report consulted by DevOps to establish existing integration DB identity.

## Artifacts Created Or Updated

- Run base artifacts, manifest, G0 report and current STATUS progress matrix.
- Stable scripts/contracts sources/profile/case inventories and provenance/behavior maps.
- Python runtime, deterministic generator, source-gated model adapter, consumer
  integration and tests; final1237 unit/81 PostgreSQL consumer tests passed.
- Headless JavaScript runtime/runner/tests; locked package install,19 Node tests,
  12 existing UI tests and443-case AJV verification passed.
- Runtime handoff and live story-role progress; final reviewer/approval state pending.

## Generated Evidence

- artifacts/diffs/g0-resource-mappings.json and g0-mapping-check.txt.
- artifacts/diffs/changed-files.txt and gate validation diagnostics.
- artifacts/runtime/compose.yaml and baseline restoration evidence (DevOps-owned).
- artifacts/test-results/ac-evidence.md maps every one of41 criteria to actual
  runtime, domain/authorization/transaction or packaging evidence.
- artifacts/test-results/conformance-review-final.json records1329 matched actual
  consumer results,21 source conditionals and79 branch witnesses.
- artifacts/test-results/python-unit-final.xml, consumer-integration-ci.xml,
  neuron-shared-bundle.xml, js-review-unit-final.tap and frontend-test.txt are raw test results.
- artifacts/test-results/stored-versions-{integration,dev}-cutover-ci.json and
  zero-row-inventory-{integration,dev}.json record actual signed empty histories;
  nonempty legacy/closed/remainder histories are separately proved by real tests.
- artifacts/install-final/installed-distribution-results.json records actual
  wheel/sdist probes outside the checkout with network disabled.
- artifacts/coverage/combined-python.json and combined-python.xml, plus
  changed-line-coverage.json, are feature Python coverage evidence; JS V8 results
  are included in artifacts/test-results/js-review-unit-final.tap.
- G2 role reports cite these raw artifacts; G3 reviews/approval are separate gates.

## External Or Global Evidence References

No global frontend lane substitutes for feature proof. Prior contract fixture
provenance is recorded in scripts/contracts/case-provenance.json. Cold archive
bypasses are restricted to exact artifacts needed for this action's validation.

## Omissions And Waivers

No waiver. UI screenshots/theme proof and AI behavior work are outside the approved
scope; all five planned reviewer roles remain required. Other omissions will be
reconciled with actual changed paths at G2/G6.

## Run Environment

Product and framework command working directories are normalized in commands.log.
Application-specific checks execute inside the run's Engine/Neuron/Node validation
containers at /app/brain, mounting the same current product checkout.

## DevOps final receipts (2026-11-23)

- deployability-check.md and g2-deployability-check.md are identical DevOps reports.
  Their current verdict is FAIL, preserving the canonical Node/Corepack build
  failure and outstanding Security/PM disposition rather than asserting G2 PASS.
- artifacts/runtime/clean-generation-check.json, clean-engine-context.json,
  current-source-context.json and clean-source-comparison.json record the clean
  Engine generation check and matching selected final source/lock fingerprints.
- artifacts/test-results/clean-conformance.json joins all 443 common cases into
  1329 actual results with no mismatches. Installed JavaScript inputs/results are
  in artifacts/install-final/javascript and artifacts/test-results/installed-js-*.json.
- artifacts/install-final/preparation.json hashes actual distribution inputs;
  installed-distribution-results.json records final wheel/sdist offline proof,
  including rfc8785 0.1.4. artifacts/runtime/devops-evidence-validation.json checks
  all report links and all 22 immutable wheel/sdist file hashes.
- artifacts/coverage/install.coverage and neuron-smoke.coverage are current
  executable proof traces for the authored installer and eight Neuron callers.
- artifacts/runtime/clean-build-receipts.json distinguishes the canonical image
  build failure from the successfully tested pnpm proposal. The precise source
  correction remains reviewable in artifacts/runtime/pnpm-selection.patch.
- artifacts/security/dependency/{engine,neuron,frontend}.json and adjacent
  execution/inventory/requirements receipts audit actual installed third-party
  pins against each lock; editable product packages are explicitly disclosed.
  Neuron retains four raw SoupSieve advisories. The independent Security
  disposition is dependency/soupsieve-disposition.md; no DevOps waiver is implied.
- artifacts/security/secrets/2026-11-23-held-lock contains the fresh redacted
  filesystem scan of 146 changed/untracked files after the final frontend lock.
  SAST final-timeout60 and DAST execution receipts remain under artifacts/security.
  artifacts/security/sast/current-input-reconciliation.json confirms that all 36
  scanned code files still match and no newly selected code is unscanned.
- artifacts/test-results/stored-versions-{integration,dev}-cutover-review-final.json
  are the latest signed real-history cutover receipts; older -ci artifacts above
  remain historical evidence rather than substitutes for the current receipts.
