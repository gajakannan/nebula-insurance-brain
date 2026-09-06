# ADR-0050: Native Policy Evaluation and Resource Scope

## Status

- [x] Proposed
- [ ] Accepted
- [ ] Superseded
- [ ] Rejected

**Date:** 2026-09-05 (record created from the master blueprint baseline)
**Deciders:** Pending; Architecture and Security roles confirm during Phase B of the first AuthX-bearing feature
**Settled by:** F0001-S0006 (access boundaries, extension build, and restore); results recorded by F0001-S0007 (F0001 Phase B, 2026-09-06)
**Source:** `planning-mds/architecture/master-blueprint.md` section 122

## Context

Proposed AuthX decision carried from the CRM reference architecture into the Brain (master blueprint sections 118 to 122). The CRM code establishes the reference contracts; the Brain implements the same contracts in its Python backend behind explicit adapters.

## Decision

Proposed: Casbin adapter plus typed scopes and parent/classification constraints; policy parity across runtimes.

## Consequences

- Shared behavior fixtures and schema contracts guard against semantic drift between the CRM reference and the Brain implementation.
- Acceptance requires the carryover tests in master blueprint section 121.2 to pass for the affected boundary.

## References

- `planning-mds/architecture/master-blueprint.md` sections 118 to 123
