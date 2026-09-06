# ADR-0052: Delegated Agents and Review Authority

## Status

- [x] Proposed
- [ ] Accepted
- [ ] Superseded
- [ ] Rejected

**Date:** 2026-09-05 (record created from the master blueprint baseline)
**Deciders:** Pending; Architecture and Security roles confirm during Phase B of the first AuthX-bearing feature
**Source:** `planning-mds/architecture/master-blueprint.md` section 122

## Context

Proposed AuthX decision carried from the CRM reference architecture into the Brain (master blueprint sections 118 to 122). The CRM code establishes the reference contracts; the Brain implements the same contracts in its Python backend behind explicit adapters.

## Decision

Proposed: Bounded acting-user/service grants; reviewer identity verification; all canonical writes through authorized commits.

## Consequences

- Shared behavior fixtures and schema contracts guard against semantic drift between the CRM reference and the Brain implementation.
- Acceptance requires the carryover tests in master blueprint section 121.2 to pass for the affected boundary.

## References

- `planning-mds/architecture/master-blueprint.md` sections 118 to 123
