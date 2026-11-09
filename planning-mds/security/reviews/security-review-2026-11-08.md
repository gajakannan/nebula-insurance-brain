# Security Review — 2026-11-08

Date: 2026-11-08
Reviewer: Security role (remediation author: AI Engineer + DevOps scope, executed by Claude Code for the operator)
Status: Remediation recorded; independent Security verification pending at the PR

## Scope

Follow-ups SEC-01 (High) and SEC-02 (Medium) from the F0006 security review (run `2026-11-02-5a00b0ff`), both due 2026-11-10. SEC-03 (Low, due 2026-11-17) is not in this change.

## SEC-01 — conversion dependencies and resource isolation

**Dependencies.** pip-audit of the neuron environment before the change found 85 advisories in 8 packages, matching the F0006 report. After locking the minimum fixed versions it reports **no known vulnerabilities**:

| Package | Before | After | Note |
| --- | --- | --- | --- |
| docling, docling-slim | 2.126.0 | 2.142.0 | Fix is 2.132.0, but 2.132–2.141 cap Pillow below 13; 2.142.0 is the lowest release that allows Pillow 13 |
| pypdf | 6.21.2 | 6.21.4 | Stays on 6.x |
| pillow | 12.3.0 | 13.0.0 | Required docling-ibm-models 4.0.2 → 4.0.4 |
| aiohttp / certifi / filelock / setuptools | 3.14.3 / 2026.7.22 / 3.32.6 / 84.0.0 | 3.14.4 / 2026.10.18 / 4.2.1 / 84.1.0 | Minimum fixed versions |

Floors are recorded in `neuron/packages/brain-ingestion/pyproject.toml` and `neuron/pyproject.toml` (`constraint-dependencies`) so a re-lock cannot regress them. The item-provenance hooks are gated to the proven Docling version; they were revalidated on 2.142.0 with real native and OCR conversions. `DOCLING_PINNED_VERSION` and the dependency matrix were updated.

**Resource isolation (ADR-0074 §1a).** Measured conversions peak at 2.4–3.0 GiB resident memory but reserve ~64 GB of virtual address space, so address-space rlimits cannot bound memory. Implemented:

- kernel ceiling: each child runs in a transient systemd user scope with `MemoryMax`, `MemorySwapMax=0` and `TasksMax`; the worker refuses to start if the scope cannot be created (`conversion_isolation_unavailable`);
- child rlimits for CPU time, written file size, open files and core dumps, set before Docling loads;
- a parent memory sampler over the process group as defense in depth and as the only memory bound in `watchdog` mode (trusted fixtures);
- committed ceilings in `config/local.yaml`: 6144 MiB, no swap, 512 tasks, 1200 CPU-seconds.

**Evidence.**
- `test_conversion_limits.py`: the child's rlimits; the scope's `memory.max`, `memory.swap.max` and `pids.max`; a kernel SIGKILL of an over-allocating child with the sampler disabled; a sampler stop in watchdog mode; fail-closed startup without `systemd-run` or a usable scope. All pass on this host.
- Existing conversion negative controls (deadline, cancellation, cleanup, orphans): pass.
- Real native and scanned GL fixture conversions under the committed cgroup ceilings: accepted, peak 2.6 and 3.0 GiB.
- Neuron: ruff, mypy and pytest pass, including the PostgreSQL recovery and enqueue suites. Engine: ruff, mypy and the brain-content coverage gate pass.

**Residual.** The converter still shares the worker's OS user and network (SEC-F5-M1 remainder). SEC-01 is closed for dependency exposure and memory/CPU/process containment; untrusted or production PDFs still require that remainder.

## SEC-02 — project security planning baseline

Authored `threat-model.md`, `data-protection.md`, `secrets-management.md` and `owasp-top-10-results.md`, normalized the `authorization-review.md` status line, and added this dated review. The framework strict audit (`nebula-agents/agents/security/scripts/security-audit.py --strict`) passes. The documents are baselines for the v0.1 local scope, not a production security qualification.

## Assessment

- Critical: 0
- High: 0 open in this scope (SEC-01 remediated; SEC-F5-M1 remainder tracked as Medium in the threat model)
- Medium: 0 from SEC-02 (closed); SEC-F5-M1 remainder open
- Low: SEC-03 open, due 2026-11-17

## Recommendations

1. Independent Security verification of this record on the PR.
2. Close the SEC-F5-M1 remainder (separate OS user or container and no network for the converter) before any untrusted or production PDF.
3. Deliver SEC-03 response headers by 2026-11-17.
