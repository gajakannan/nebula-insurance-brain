# F0003 — PostgreSQL persistence

**Status:** Planned
**Phase:** v0.1A
**Roadmap:** Next

## Overview

PostgreSQL is the authoritative runtime store; the core tables, range types, and exclusion constraints underpin every later feature (section 78).

Source: `planning-mds/architecture/master-blueprint.md` section 95 (epic roadmap) and section 115.3 (sequencing). Governing ADRs: [ADR-0002](../../architecture/decisions/ADR-0002-postgresql-is-the-authoritative-runtime-store.md), [ADR-0008](../../architecture/decisions/ADR-0008-database-level-temporal-integrity.md).

## Documents

| Document | Purpose |
|---|---|
| [PRD.md](./PRD.md) | Phase A requirements and scope |
| [personas.md](./personas.md) | Reused persistence-engineer persona |
| [acceptance-criteria-checklist.md](./acceptance-criteria-checklist.md) | Phase A requirement-quality review |
| [STATUS.md](./STATUS.md) | Planning status and Architect-owned signoff matrix |
| [feature-assembly-plan.md](./feature-assembly-plan.md) | Phase B implementation sequence |
| [GETTING-STARTED.md](./GETTING-STARTED.md) | Phase B implementation entry point |

## Stories

| ID | Title | Status |
|----|-------|--------|
| [F0003-S0001](./F0003-S0001-persistence-inventory-and-ownership.md) | Inventory core persistence ownership and phase boundaries | Not Started |
| [F0003-S0002](./F0003-S0002-persisted-ownership-and-reference-integrity.md) | Enforce persisted ownership and reference integrity | Not Started |
| [F0003-S0003](./F0003-S0003-temporal-and-transaction-integrity.md) | Preserve temporal and transactional integrity | Not Started |
| [F0003-S0004](./F0003-S0004-safe-schema-evolution.md) | Evolve the schema without losing accepted state | Not Started |

**Total Stories:** 4

## Planning Status

Phase A and Phase B are approved in plan run 2026-09-30-6632006b. G4 and ordered G5 validation passed. F0003 owns the full §78 inventory and shared persistence boundary; each feature retains its domain behavior and delivery phase. Runtime implementation has not started.
