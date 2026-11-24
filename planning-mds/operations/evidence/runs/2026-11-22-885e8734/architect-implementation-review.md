# Architect Implementation Review — F0011 JSON Schema contract system (run 2026-11-22-885e8734)

- Role: Architect
- Reviewer: Claude (Opus 5.5) / Architect
- Date: 2026-11-23

Result: PASS

## Conformance To The Approved Assembly Plan

| Plan item | As built | Conforms |
|---|---|---|
| 21 existing payload definitions published as one offline, hash-admitted bundle | `schemas/contracts/v1/` + `brain_contracts/resources/v1/`; manifest/hash/ref closure admitted before any instance; 86 generated artifacts reproduce exactly | Yes |
| No authored business-schema assertion, grant, route or migration change | Source schemas untouched; the review-decision resource is an OpenAPI documentation dependency, separate from the 21-resource runtime inventory | Yes |
| Generated Pydantic is typed code, not the final structural authority | Source validation runs before parse and after exact serialization; lossy or coerced output refuses (`CONTRACT_MODEL_MISMATCH`) | Yes |
| Native readers frozen; portable profile explicit; no fallback | Profile selected by static resource ref before input; native UUID/date behaviour preserved; portable exact-end patterns, depth/size/node bounds and admitted fragment positions (CR-F0011-01..04) | Yes |
| Response guards after authorization; commit guard inside the mutation | `contract_guards.py`; GET guard after source READ and read audit (PR-L3 accepted by Security); commit guard rolls back versions, changes and outbox | Yes |
| Dependency direction inward; no schema library enters `brain_domain` | Verified by Code Review; `brain-contracts` already owned the dependency | Yes |
| Stored-history sweep before guard activation (PR-M1) | Signed READ ONLY sweeps of integration and dev pass against the guard code before activation; both histories are empty, with explicit zero-row inventories; non-empty history proven in owned fixtures | Yes |

## ADR-0079 Required Proof Before Acceptance

| # | Proof | Evidence | Met |
|---|---|---|---|
| 1 | All 41 ACs observed; every keyword/format has positive and negative cases; every conditional branch exercised | `artifacts/test-results/ac-evidence.md` (41/41); conformance behaviour coverage: 21 conditionals, 79 witnesses executed, 29 keywords, 4 formats | Yes |
| 2 | Python JSON Schema, generated Pydantic and AJV agree on 100% of portable cases, no skips; round trips keep metadata, money precision, identifier identity, absence vs null | `artifacts/test-results/canonical-node-conformance.json`: 443 cases, 1329 results, 0 mismatches | Yes |
| 3 | Native readers preserve acceptance/refusal codes, F0006 dispatch, F0007 READ order, F0008 attestation; refused writes leave no partial mutation | Native baseline/candidate differential matched; PostgreSQL consumer lane 83/83 including rollback and READ-order tests | Yes |
| 4 | Installed packages work offline; missing refs, duplicate identities, bad hashes, unknown profiles and drift fail closed | `artifacts/install-final/installed-distribution-results.json` (wheel + sdist, checkout hidden, network none); bundle-integrity unit tests | Yes |
| 5 | OpenAPI/route/payload checks and clean reproducible builds pass; changed-line coverage ≥ 80%; required reviewers sign every story | `test_contract_openapi.py`; clean canonical images match current source; coverage 86.4% Python / 98.5% JS; signoffs at G5 (`signoff-ledger.md`) | Yes (signoff at G5) |

ADR-0079 stays **Proposed**. Its text requires "a later explicit operator decision
citing those proofs". This review documents that the proofs are met; it does not
accept the ADR. ADR-0039 also stays Proposed, because its F0023
incomplete-package display condition is outside F0011.

## G4 Follow-up Changes

The user chose at G4 to fix all three Lows before approval. The architect confirms none
changes shared semantics: 500-handler logging (observability only), two direct
`facts.py` tests, and a single-package Neuron lock upgrade (SoupSieve 2.9.2 → 4.1.3)
with the full Neuron suite passing.

## Knowledge Graph

New source surfaces (`brain_contracts` runtime, `scripts/contracts/`,
`experience/scripts/contracts/`, `schemas/contracts/v1/`, `docker/contracts/`) are
bound or confirmed at G7 in `kg-reconciliation.md`. That gate also decides whether
any new canonical node is needed.
