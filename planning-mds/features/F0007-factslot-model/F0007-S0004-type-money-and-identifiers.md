# Type money and identifiers

**Story ID:** F0007-S0004
**Feature:** F0007 — FactSlot model
**Title:** Type money and identifiers
**Priority:** Critical
**Phase:** MVP
**Status:** Not Started

## User Story

**As a** Priya the GL Underwriter
**I want** limits held as exact amounts with currency and basis, and identifiers held with the scheme that issued them
**So that** a USD 1,000,000 each-occurrence limit is never confused with an aggregate limit or with another carrier's policy number.

## Context & Background

ADR-0039 decisions 4–5 and master blueprint §107.3. F0011 publishes the JSON Schemas, F0013 applies these types to GL limits, and F0017 resolves on scoped identifiers. Acceptance example (§107.3): two carriers use the same policy number, so the Brain holds two policies.

## Acceptance Criteria

- [ ] **AC1:** A money value is an exact decimal amount, an ISO 4217 alphabetic currency code and, where the predicate requires one, a basis qualifier. A binary floating-point amount is rejected with `MONEY_FLOAT_REJECTED`. An unknown currency code is rejected with `CURRENCY_INVALID`. A missing required basis is rejected with `BASIS_REQUIRED`.
- [ ] **AC2:** `1000000`, `1000000.00` and `1E+6` in USD compare equal and serialize to one canonical form. Round trips through PostgreSQL lose no precision for `0.01`, `999999999999999.99` and an amount above 2^53.
- [ ] **AC3:** F0007 accepts original-currency money only. A value marked as converted is rejected with `CONVERTED_MONEY_UNSUPPORTED` until a feature owns exchange-rate provenance.
- [ ] **AC4:** A scoped identifier is (scheme or issuer, identifier type, value, optional effective interval). Policy number `GL-1001` from carrier A and `GL-1001` from carrier B are two different identifiers. An identifier with no scheme is rejected with `IDENTIFIER_SCHEME_REQUIRED`.
- [ ] **AC5:** Value normalization is declared per identifier type. FEIN `12-3456789` and `123456789` compare equal. No normalization ever makes identifiers from different schemes equal.
- [ ] **AC6:** Money and identifiers used as qualifiers or member keys contribute their canonical encoding to slot identity, so equal values resolve one slot or member (S0001/S0002).
- [ ] **AC7:** An unauthorized caller is denied before any value-validation detail is returned. A rejected value produces no slot, member or fact version. Accepted values are recorded under the existing commit or slot-creation audit.

## Interaction Contract

| Surface / Entry Point | User Action | Editable State | Save / Mutation Result | Reload / Persistence Evidence | Roles / Status Constraints |
|---|---|---|---|---|---|
| Slot resolution and existing commit boundary | Submit a typed value or qualifier | New values only | Canonical value stored, or a named rejection | Reload returns the identical canonical amount, currency, basis and identifier tuple | Existing KB write/commit authority |

No screen or route.

## Data Requirements

Decimal amount, currency code, basis, identifier scheme or issuer, identifier type, identifier value and optional effective interval, each carried in canonical encoding.

## Role-Based Visibility

Typed values inherit the visibility of their slot and KB. No extra exposure is introduced.

## Non-Functional Expectations

No binary floating point in any authoritative path. Encoding is deterministic and locale-independent.

## Dependencies

S0001 identity encoding, S0003 carrier, and the F0001 pilot commit path. F0011, F0013 and F0017 consume these types.

## Out of Scope

Currency conversion and exchange rates, GL basis vocabulary (F0013), exposure units, financial-component formulas, and identity resolution on identifiers (F0017).

## Questions & Assumptions

Assumption (PRD): F0007 accepts original-currency money only. The Architect owns the canonical decimal encoding and the identifier-type normalization table; FEIN is the only normalization fixed here.

## Definition of Done

- [ ] Seven ACs pass with positive, boundary and rejection fixtures.
- [ ] Feature action records tests, coverage and required signoffs.
