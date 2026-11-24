# DevOps handoff — F0011 run 2026-11-22-885e8734

Product root: `/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain`.
Framework root: `/home/gajap/uSandbox/repos/nebula/nebula-agents`.
Recorded: 2026-11-23. Reuse this run; G0/G1 passed and G2 is pending.

## Current evidence

Both run-root deployability reports exist, are identical, and state FAIL. The
blocking canonical Node build chooses pnpm 12.23.0 while the project requires
12.21.0. The exact two-line correction is `pnpm-selection.patch` beside this
file. It is staged only: the canonical Dockerfile remains unchanged under the
orchestrator's source hold. `Dockerfile.pnpm-pin-proposal` actually builds, installs
the final frozen lock with pnpm 12.21.0, and passes all 19 tests offline.

Canonical Engine clean build/generation and source fingerprints pass. All 443
cross-language cases join into 1329 matching results. Both wheel and sdist probes
pass without checkout/network access, including rfc8785 0.1.4. Outside-checkout
JavaScript passes 443 cases. Neuron caller smoke passes 8 tests; Ruff/format/mypy
pass (51 typed files). `install.coverage` and `neuron-smoke.coverage` under coverage
are the current traces for QE aggregation, not stale pre-RFC receipts.

The final canonical Neuron clean-target build passed: 190 lock entries resolved,
186 active packages installed, image digest
`sha256:37c2990b278354acf9b51ca82c2199b61db6102c19a276c2b446289d5a5018af`.
Its actual default CI command passed all 8 caller tests with networking disabled
and no checkout or host virtualenv mounted. `neuron-clean-smoke.txt` and
`clean-build-receipts.json` record this separately from the mounted-runtime tests.

## Security receipts

The dependency collectors now enumerate every installed third-party package in
the actual candidate venv, verify its exact pin against the selected uv.lock,
and run pip-audit 2.10.1 with no dependency installation/resolution. Only actual
editable brain-* source entries are disclosed separately for manual/SAST review.
Engine: 75 third-party pins, zero findings. Neuron: 171 pins, four preserved
SoupSieve 2.9.2 advisories. Frontend: zero advisories on the final remediated lock.
Raw receipts and exact requirement inventories are under security/dependency.

Security's independent soupsieve-disposition.md finds no demonstrated exploit
through the current PDF-only adapter; it still prefers a compatible >=4.0.0
upgrade. If retained, the scoped Low component-hardening follow-up needs final
Security disposition and named PM acceptance. No DevOps waiver was granted.

Required SAST and DAST receipts are present. The refreshed held-lock Gitleaks
filesystem scan includes all 146 changed/untracked source files, redacts output,
and reports zero findings. Parent owns DAST interpretation/execution closeout.

## Exact next work

1. The orchestration/architecture owner must release the source hold and apply
   the staged two-line Node package-manager correction. Then run the canonical
   Node image build, its 19 tests and 443 cases; refresh selected Dockerfile
   fingerprints and clean COPY provenance as needed. Do not promote the proposal
   image receipt to a canonical passing receipt without that source change.
2. Resolve the disclosed SoupSieve advisories by a compatible lock-only upgrade
   with fresh installed audit/affected smoke, or record the complete Security/PM
   residual disposition. Preserve the current raw four-advisory receipt.
3. QE combines current proof traces, refreshes reports/manifest scan fields and
   runs G2 through run-gate. G3 final review and G4–G8 remain separate required
   gates. No completion approval, latest-run, KG reconciliation or archive move
   has been written by DevOps.

The orchestrator agent currently reports an automatic review error for possible
cybersecurity risk. No tool approval is pending on the staged Dockerfile change;
the outstanding constraint is its explicit source hold and the stopped parent
orchestration. This handoff does not authorize skipping lifecycle gates.
