# Persona: Ingrid the Persistence Engineer

**Role/Title:** Persistence Engineer, Nebula Insurance Brain
**Archetype:** Internal builder — owns the PostgreSQL schema, bitemporal commit algorithm, constraints, and outbox
**Priority:** Primary (F0001, F0003, F0007, F0008, F0018)

## Demographics & Background

**Experience Level:** 7+ years designing transactional schemas with range types, exclusion constraints, and outbox patterns
**Technical Proficiency:** High
**Daily Responsibilities:**
- Implement and test the two-range bitemporal commit (section 109.2)
- Keep facts, audit, and outbox in one transaction (section 109.3)
- Prove concurrency behavior at the database, not only in application code

## Goals & Motivations

### Primary Goals
1. Unambiguous accepted state under retroactive and concurrent change (ADR-0007, ADR-0008)
2. Every ended fact records why (ADR-0009)
3. Recorded time means canonical acceptance, distinct from receipt (section 109.2)

### Success Metrics
- Section 87 questions answered at every coordinate; concurrency test leaves exactly one winner

## Pain Points & Frustrations

1. **Single-range temporal keys that do not express two overlap conditions** (reference R6) — Impact: ambiguous history; Frequency: at design time; Severity: Critical
2. **Silent updates to period endpoints while claiming immutability** — Impact: audit contradictions; Frequency: per correction; Severity: High
3. **Projections updated outside the commit transaction** — Impact: lost edges after crashes; Frequency: per failure; Severity: High

## Jobs-to-be-Done

1. **When** an endorsement is accepted after review, **I want to** split intervals and close superseded beliefs in one transaction, **so I can** answer "what did we know on June 5" correctly.
2. **When** two commits race, **I want to** rely on an exclusion constraint, **so I can** guarantee one winner.
3. **When** a worker dies after commit, **I want to** replay the outbox idempotently, **so I can** repair projections without duplicates.

## Anti-Personas

- **Not:** the graph or vector projection owner (F0033, F0034)
- **Not:** the process or Temporal engineer (F0048 to F0050)

## Related Personas

- Receives corrected assertions from Rosa's decisions; depends on Dana for the database build
