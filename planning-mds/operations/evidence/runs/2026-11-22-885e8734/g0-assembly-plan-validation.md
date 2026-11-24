# F0011 G0 — Assembly plan validation

Reviewer: Codex / Architect
Date: 2026-11-22
Verdict: PASS
Run: 2026-11-22-885e8734
Product: /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain

The approved Phase B revision `2026-11-21-e4098d22` is the implementation
baseline. All six local stories (41 ACs), the PRD, inventory, design, profile,
ADR-0079 and SOLUTION-PATTERNS were inspected. There is no requirements change.

## Scope and dependencies

The five assembly steps sequence offline bundle admission, value aliases,
generated Python/AJV/OpenAPI consumers, existing consumer adoption, and installed
build/CI proof. Backend owns the generator/runtime/adapters; Frontend owns
headless JavaScript; QE owns independent case/transaction/coverage proof; DevOps
owns runtime, locks, packaging and CI. Architect retains shared schema/semantic
ownership. No AI behavior, new screen, route, permission, DDL or reparse is planned.
The required five-role matrix in STATUS.md is reconfirmed for every story.

## Per-resource reconciliation

All 21 resource identities and hashes match their authored sources. All existing
consumer and compatibility-test paths in the 68 mappings exist and Python paths
parse. See `artifacts/diffs/g0-resource-mappings.json` and
`artifacts/diffs/g0-mapping-check.txt`. The mapping is copied to
`scripts/contracts/sources.yaml`; `scripts/contracts/profile.yaml` is an exact
copy of the approved policy. Planned tests remain planned, with no proof claimed.

The v1 manifest class is actually `ArtifactManifest`, rather than the plan's
descriptive name `ArtifactManifestV1`. The runtime entry point remains
`parse_manifest`; its selector does not change. Documentation-only manifest-read
and ProblemDetails boundaries remain explicitly separate from concrete readers.

## Integration checkpoints and controls

1. Reject invalid identities, hashes, unsupported schemas and dormant bad refs
   before constructing a bundle. Generated trees are accepted only as a coherent set.
2. Preserve all nine information states, exact money/identifier strings, nullable
   versus absent properties and native reader acceptance without fallback.
3. Execute common portable cases in real JSON Schema, generated/source-gated
   Pydantic and AJV. Missing, duplicate, crashing or skipped results fail.
4. PR-M1: inventory integration/dev environments at G0; execute full-history
   READ ONLY REPEATABLE READ sweeps against the candidate guard before enabling
   it, and repeat while prior writers are paused for cutover. An unavailable DB
   never counts as empty. DevOps runtime inventory is recorded separately.
5. PR-M2: every per-resource consumer/selector/test/disposition mapping remains
   explicit; fixtures and OpenAPI equality alone cannot substitute for integration.
6. PR-L3: inject an authorized read invariant failure and a denied-source case;
   Security must decide the SUCCEEDED-read-audit/generic-500 meaning at G3.
7. Verify refused writes by querying authoritative state; preserve existing
   domain reasons and source READ checks, with mutation output guards inside
   the same outer unit of work.

## Artifact ownership and knowledge graph

Generated schemas/models/metadata/OpenAPI derive from the allowlisted authored
source. Build inputs use stable scripts paths; runtime has no planning dependency.
The existing planned capabilities `offline-contract-bundle` and
`cross-language-contract-validation` gain real code bindings at G7. Existing
content/assertion/FactSlot/temporal capability bindings are extended only for
delivered files. No generated knowledge-graph YAML is hand-edited.

## Validation limits

This verdict approves the assembly and mapping checkpoint. Runtime readiness,
history compatibility, conformance and all implementation ACs remain unverified
until their later gates. ADR-0079 and ADR-0039 remain Proposed.
