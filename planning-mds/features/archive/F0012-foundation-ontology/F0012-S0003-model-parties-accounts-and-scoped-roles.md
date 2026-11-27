# F0012-S0003 — Model parties, accounts and scoped roles

**Story ID:** F0012-S0003
**Feature:** F0012 — Foundation ontology
**Title:** Model parties, accounts and scoped roles
**Priority:** Critical
**Phase:** MVP — v0.1A
**Status:** Done

## User Story

**As a** domain steward (Sameer)
**I want** the foundation module to define the base classes and the account, party, ownership and role vocabulary with explicit time behavior and constraints
**So that** insurance modules, identity resolution and Entity 360 build on one agreed meaning of account, owner and role.

## Context & Background

Master blueprint §22 lists the foundation classes. Proposed ADR-0070 (direction authorized 2026-10-10) defines parties, one account per insured organization, a designated parent, ownership interests and scoped role assignments; its proof gate 1 requires F0012 to author them with `temporal_kind`, definitions and regression cases. Operator decision D2 (G1, 2026-11-25) keeps Policy, PolicyTerm, Submission and Program in F0013. The [data model](../../../architecture/data-model.md#proposed-party-account-and-role-records-adr-0070) lists the temporal kinds.

## Acceptance Criteria

- [x] **AC1:** The foundation module defines the §22 classes Thing, Party, Person, Organization, Account, Place, Document, Agreement, Event, Process, Decision, Role, TimeInterval, Amount, Measurement and Identifier, each passing S0001. Person and Organization are subclasses of Party. Broker, carrier, MGA and insured are not subclasses of Organization.
- [x] **AC2:** It defines organization hierarchy (parent organization, no fixed depth), operating location and employment as `STATE`; account organization as `ETERNAL`; account status (`CURRENT`, `CLOSED`) as `STATE`; designated parent account as `STATE`; ownership owner and owned organization as `ETERNAL` and ownership percentage as `STATE`; role-assignment party and acted-for organization as `STATE`, and role kind and scope as `ETERNAL`.
- [x] **AC3:** Role kinds are an open vocabulary that contains at least FirstNamedInsured, AdditionalNamedInsured, AdditionalInsured, BrokerOfRecord, PlacementBroker, BrokerContact, RiskManager, AccountContact, OrganizationContact, Underwriter, UnderwritingAssistant, DistributionContact, MarketingRepresentative and OperationsContact. FirstNamedInsured, AdditionalNamedInsured and AdditionalInsured are distinct. Each kind maps to a canonical `PartyRoleTypeCode` value or is marked unmapped.
- [x] **AC4:** A role assignment's scope ranges over a foundation scope class, of which Account is a member; F0013 adds policy-term and submission scopes as subclasses. A role assignment may carry an optional coverage-part qualifier and an authoritative-source marker. A scope that is not a scope-class member is rejected at validation.
- [x] **AC5:** The module declares, with consumer and stage, these constraints: at most one designated parent; no self-parent or parent cycle; ownership percentage greater than 0 and at most 100; recorded percentages for one organization total at most 100 at one valid/known coordinate; at most one `CURRENT` account per organization per tenant at one coordinate; a missing or unknown status cannot satisfy that check. Majority ownership is not a stored property.
- [x] **AC6:** No vocabulary term grants access: role assignments and the authoritative-source marker are data only. Authorization decisions, Casbin policy rows and authorization audit records are identical before and after the foundation release is installed (EX-PC-011).
- [x] **AC7:** EX-PC-001, EX-PC-011, EX-PC-015, the account-scoped rows of EX-PC-017 and EX-PC-021, re-expressed on production foundation IRIs, pass the `semantic_examples` and `semantic_rdf` gates with exact expected and forbidden rows. The self-parent, parent-cycle, ownership-over-100, two-parent-accounts and duplicate-organization-account boundaries fail and the close/reopen boundary conforms, as the cases document.

## Edge Cases & Error Scenarios

A joint venture with recorded owners totaling 60 percent conforms because owners can be unknown (EX-PC-015). A 40/30/30 venture designated under the 40 percent owner conforms. A same-day replacement account after a closure on that day conforms because the end bound is exclusive (EX-PC-021). A person holding two roles on two accounts is two assignments (EX-PC-017).

## Interaction Contract

N/A for runtime mutation: this story authors vocabulary files and example fixtures that pass offline validation and example gates. Enforcing the constraints at canonical admission is F0017/F0018 (PRD assumption A2). No editable state or save action is introduced.

## Data Requirements

Class and property definitions, labels, temporal kinds, cardinality, role-kind codes and their `PartyRoleTypeCode` mapping, scope class hierarchy, constraint execution context, and Cedar Bridge fixtures moved to production IRIs. The exact local names and predicate keys are Phase B decisions.

## Role-Based Visibility

No runtime principal is involved; authored content is validated offline. The vocabulary itself creates no grant. See the [PRD role matrix](PRD.md#role-based-access).

## Non-Functional Expectations

Example gates are deterministic and run in CI; `semantic_rdf` runs with `--require` in CI. Zero parses or model calls.

## Dependencies

S0001 and S0002 validation; existing `semantic_examples` and `semantic_rdf` gates; Cedar Bridge fixtures. F0013 supplies the policy-dependent cases EX-PC-016, EX-PC-018, EX-PC-019 and EX-PC-020.

## Out of Scope

Policy, PolicyTerm, Submission, Program and their account/program links (F0013); identity resolution and merge (F0017); admission-time enforcement (F0017/F0018); access reach from roles (F0002-successor amendment); broker-of-record change workflow.

## Questions & Assumptions

No open business-rule question: ADR-0070's operator direction supplies the rules. PM assumptions A2 and A4 are in the [PRD](PRD.md#risks--assumptions). Role-kind codes beyond the listed minimum are open vocabulary added through later releases.

## Definition of Done

- [x] Every AC above has a concrete observed proof in the later feature run.
- [x] Vocabulary validates; example and RDF gates pass with exact expected/forbidden rows; each boundary fixture fails or conforms as stated.
- [x] No change to authorization policy or behavior is observed.
- [x] Documentation and tracker state reflect observed results.
- [x] Required story-level review provenance is appended to STATUS.md in the feature action.

## Review Provenance

Feature run `2026-11-26-54387a08`: Quality Engineer, Code Reviewer, Security Reviewer, DevOps and Architect signoffs are recorded in [STATUS.md](STATUS.md#story-signoff-provenance) and the run's signoff ledger.
