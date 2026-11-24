# Deployability Check — F0011-json-schema-contract-system run 2026-11-22-885e8734

Reviewer: Codex / DevOps; final refresh Claude / DevOps. Date: 2026-11-23. Verdict: PASS.
Product root: /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain.

## Runtime / Deployment Config Changes

The feature adds the bounded application validation targets in `docker/contracts/Dockerfile`, documents them in `docker/contracts/README.md`, excludes host state through `.dockerignore`, and adds the unconditional contracts build/conformance/install/Neuron job plus PostgreSQL consumer tests in `.github/workflows/ci-gates.yml`. These targets do not add a deployed service.

The Engine build pins Python 3.14.4, uv 0.11.31 and the engine contract-build lock group (datamodel-code-generator 0.96.0, build 1.6.1, setuptools 84.1.0 and wheel 0.48.0). Node is 22.23.1 and the project package manager is pnpm 12.21.0. Shared package resources/generated models are included in distributions. Both Python workspaces lock rfc8785 0.1.4; [the lock comparison](artifacts/runtime/rfc8785-lock-comparison.json) records that this addition did not rebaseline unrelated pins.

The canonical Node target originally failed its clean frozen install: Corepack selected pnpm 12.23.0 from the root working directory and the project rejected it with ERR_PNPM_BAD_PM_VERSION. The [two-line correction](artifacts/runtime/pnpm-selection.patch) (`COREPACK_DEFAULT_TO_LATEST=0`; `corepack prepare pnpm@12.21.0 --activate`), first proven under [a proposal Dockerfile](artifacts/runtime/Dockerfile.pnpm-pin-proposal), is now applied to canonical `docker/contracts/Dockerfile`. The source hold is released. After the change, all three canonical targets were rebuilt. They were rebuilt again after the G4 Low fixes changed `neuron/uv.lock` (SoupSieve 2.9.2 → 4.1.3, a single-package delta) and the API error handlers.

## Migrations / Rollback

No F0011 database migration was added. Dev initially lagged the already-shipped schema; existing migrations 0011–0015 restored it from 0010 to 0015 without payload repair, reparsing, or history writes. A private PostgreSQL custom backup was retained before restoration; only its hash is recorded. [Baseline restoration](artifacts/runtime/baseline-restoration.json) records exit 0 and unchanged zero history counts. Integration was already 0015.

Rollback retains the previous application/package release and intact authored schema sources. The generator's publication rollback/readability tests cover restoring the old artifact bytes and modes on failure; no database down migration is part of this feature. If the earlier dev baseline must be restored, use the retained private backup under the established database recovery process, preserving the ledger constraints. No actual rollback of the healthy database was performed.

## Env / Config Contract

Existing BRAIN_DATABASE_URL credential handling is unchanged. `scripts/contracts/environments.json` binds the existing nonsecret integration database `brain_f0008_shared` and dev database `brain` on the existing PostgreSQL service; it does not create databases or embed credentials. Runtime build variables UV_PYTHON_DOWNLOADS=never, UV_PROJECT_ENVIRONMENT and temporary cache paths affect validation containers only. The staged Node correction adds COREPACK_DEFAULT_TO_LATEST=0 and explicitly prepares the project's existing pinned pnpm version.

Required validation services were restored healthy using the run-local [Compose definition](artifacts/runtime/compose.yaml); [the fresh preflight](artifacts/runtime/resume-preflight-2026-11-23.json) records the actual environment. The real final signed read-only history sweeps [integration](artifacts/test-results/stored-versions-integration-cutover-review-final.json) and [dev](artifacts/test-results/stored-versions-dev-cutover-review-final.json) passed against guard code 8118399dc19ddfd3f3abdd6ca94a91814bbb1a69c48560570d160a1c8d0e05be before the private DAST API started. Both selected and checked all zero observed rows with explicit signed inventory; no empty-history bypass was used.

## Manifest Boolean Cross-Check

The current manifest correctly records runtime_bearing=true, deployment_config_changed=true, frontend_in_scope=true and security_sensitive_scope=true. Runtime reader/guard changes, the new Docker/CI harness, JavaScript tooling and fail-closed security boundaries support these values. This report does not finalize the manifest or any gate.

## Build / Start / Smoke Results

All paths below are durable evidence for this run. The common bundle digest is 054119f11aa89c39f7687968424b9e40c63bbceadaaee145790f5908ab927959.

- Clean canonical Engine image (rebuilt after the Dockerfile correction): build exit 0; [offline generate --check](artifacts/runtime/clean-generation-check.json) passes all 86 artifacts. [Input fingerprints](artifacts/runtime/clean-source-comparison.json) match the current selected source, locks, schemas and configuration; local .git, virtualenvs, node_modules, evidence and caches were absent from the clean context.
- [Clean cross-language join](artifacts/test-results/clean-conformance.json): 443 cases, 1329 results, zero mismatches across jsonschema, generated Pydantic and real AJV.
- [Installed wheel and sdist](artifacts/install-final/installed-distribution-results.json): both pass in fresh virtualenvs as UID 1001, with networking disabled, the checkout hidden by an empty read-only mount and only built distributions/exact dependency wheels available. Includes rfc8785 0.1.4, native v1/v2 readers and typed round trips. [Preparation](artifacts/install-final/preparation.json) hashes the distributions and 16 exact dependency/build wheels.
- [Installed JavaScript probe](artifacts/test-results/installed-js-results.json): 443 cases pass with the whole four-file runtime folder and exact dependencies, outside the checkout with networking disabled.
- [Neuron shared callers](artifacts/test-results/neuron-shared-bundle.xml): 8 tests pass. [Ruff](artifacts/test-results/neuron-ci-lint.txt), [format](artifacts/test-results/neuron-ci-format.txt) and [mypy](artifacts/test-results/neuron-ci-mypy.txt) pass; mypy checked 51 files. Current installer and Neuron traces are [install.coverage](artifacts/coverage/install.coverage) and [neuron-smoke.coverage](artifacts/coverage/neuron-smoke.coverage); QE owns aggregate coverage.
- Canonical Neuron clean image (rebuilt after the Dockerfile correction): build exit 0, 190 locked entries resolved and 186 active packages installed. Its actual default CI command passes [all 8 caller tests offline](artifacts/runtime/neuron-clean-smoke.txt); no checkout or host virtualenv is mounted into this container. The exact image digest and build result are in the image receipts below.
- Canonical Node image: [build exit 0](artifacts/runtime/canonical-node-build.stderr.txt) with pnpm 12.21.0 from the frozen lock. Its default command passes [19 tests offline](artifacts/runtime/canonical-node-tests.txt). In the same image `contracts:check` passes [443 cases](artifacts/test-results/canonical-node-cases.json), and the clean Engine image joins them into [1329 results with zero mismatches](artifacts/test-results/canonical-node-conformance.json). [Image receipts](artifacts/runtime/clean-build-receipts.json) record all three canonical image IDs. No final GitHub CI run is claimed; that happens on the PR.

## Runtime Warnings

Four required scan classes have actual receipts: [strict installed dependency audits](artifacts/security/dependency/summary.json), [redacted filesystem secrets scan](artifacts/security/secrets/2026-11-24-closeout-final/execution.json) (final re-run after the G4 fixes and G8 archive move; 166 files, 0 findings), [SAST](artifacts/security/sast-closeout/execution-summary-closeout.json) and [DAST](artifacts/security/dast/execution.json). Engine audits 75 exact third-party pins with zero advisories; frontend is clean. Neuron audits 171 exact third-party pins with zero advisories after the G4 SoupSieve 2.9.2 → 4.1.3 lock-only upgrade. The pre-upgrade four-advisory report is retained, not erased. Only actual editable brain-* workspace entries are disclosed separately for source review.

Security's [independent reachability disposition](artifacts/security/dependency/soupsieve-disposition.md) finds no demonstrated exploitation path through the current PDF-only adapter, while preserving the vulnerable-component finding and preferring a compatible upgrade. Any residual recommendation requires Security's final verdict and named PM acceptance; DevOps has not granted either. The SAST warning and DAST informational categories are interpreted by Security, not converted here into an independent security approval.

## Result

Result: PASS

All three canonical validation images build and pass offline on current source, including the G4 Neuron lock change ([receipts](artifacts/runtime/clean-build-receipts.json)). The clean context matches the current selected source, locks and Dockerfile exactly ([comparison](artifacts/runtime/clean-source-comparison.json)). Installed wheel/sdist proofs pass and their packaged sources are unchanged by the G4 fixes. No migration or deployed-service change is introduced. The earlier SoupSieve recommendation is resolved by the upgrade ([disposition](artifacts/security/dependency/soupsieve-disposition.md)).

This report does not grant approval, signoff, latest-run publication, archive or deployment.
