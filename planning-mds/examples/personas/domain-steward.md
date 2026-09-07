# Persona: Sameer the Domain Steward

**Role/Title:** GL Guideline and Ontology Steward
**Archetype:** Internal governance user — owns what a guideline means and which version is in force
**Priority:** Primary (F0065-S0001); becomes a primary governance persona in F0029, F0030, and F0042

## Demographics & Background

**Experience Level:** 12+ years in commercial lines product and underwriting governance; owns guideline documents and their approvals
**Technical Proficiency:** Medium — reads structured definitions and version histories; does not author code or policy expressions
**Daily Responsibilities:**
- Maintain the written guideline, its authority, and its applicability scope
- Approve a change to a threshold and record who approved it
- Answer "which version applied on this date" for audit and referral

## Goals & Motivations

### Primary Goals
1. Release a guideline as an immutable, reviewed version with an explicit authority reference (F0065-S0001)
2. Change a threshold without rewriting history — the old release stays readable and stays applicable to the period it governed
3. Keep the scope explicit: coverage type, limit basis, currency, tenant, and effective interval

### Success Metrics
- Every release traceable to an approver and a source document; zero assessments attributed to an unversioned or unapproved rule

## Pain Points & Frustrations

1. **A threshold edited in place** — Impact: past decisions can no longer be explained; Frequency: per change under a mutable model; Severity: Critical
2. **A rule expressed as free-form prose that something later "interprets"** — Impact: the meaning is whatever the parser did that day; Frequency: per ambiguous definition; Severity: Critical
3. **A newer release silently applied to an older question** — Impact: hindsight presented as history; Frequency: per historical query; Severity: High
4. **Being asked to approve a threshold with no stated applicability** — Impact: the rule gets used outside the coverage or currency it was written for; Frequency: per release; Severity: High

## Jobs-to-be-Done

1. **When** the guideline changes, **I want to** publish a new immutable version with its authority and effective interval, **so I can** leave the prior version intact and citable.
2. **When** someone asks a question about an earlier date, **I want** the release that was available and effective then to be the one applied, **so I** am not signing off on hindsight.
3. **When** a definition is malformed or uses an unsupported operation, **I want** it rejected at release time, **so I** never discover it through a wrong answer.

## Constraints & Considerations

- Authorization: rule installation requires a separately authorized administrative authority; ordinary read permission and model output confer none (F0065-S0001)
- The v0.1 vocabulary is one operation, `money_gte_minimum` — he cannot express chained or conditional logic, by design (ADR-0056)
- The EX-GL-001 `$1,000,000` minimum is an explicitly fictional fixture; the production authority is an open decision he owns

## Anti-Personas

- **Not:** the underwriter applying the guideline to an account (see [GL underwriter](gl-underwriter.md))
- **Not:** an ontology engineer authoring the foundation or insurance-core ontology (F0012, F0013)
- **Not:** a rule-authoring workbench user — no workbench exists in v0.1 (F0030)

## Related Personas

- Releases the rules Priya's assessments cite; his scope decisions determine when a result is `NOT_APPLICABLE`
