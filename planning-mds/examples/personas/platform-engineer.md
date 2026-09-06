# Persona: Dana the Platform Engineer

**Role/Title:** Platform and Security Engineer, Nebula Insurance Brain
**Archetype:** Internal builder — owns runtime, containers, CI, identity, and recovery
**Priority:** Primary (F0001)

## Demographics & Background

**Experience Level:** 8+ years operating PostgreSQL-backed services; has run OIDC identity providers and container stacks in regulated environments
**Technical Proficiency:** High
**Daily Responsibilities:**
- Keep the local and CI dependency stack reproducible and pinned
- Own identity integration, policy enforcement wiring, and audit plumbing
- Run backup and restore drills and record recovery objectives

## Goals & Motivations

### Primary Goals
1. A fresh clone that installs, starts, and passes its gates without tribal knowledge
2. Access boundaries proven with real tokens before any feature depends on them
3. One tested dependency matrix instead of generic compatibility claims (master blueprint section 114.3)

### Success Metrics
- CI green on every PR; restore drill within the recorded objectives; zero unverified-credential paths

## Pain Points & Frustrations

1. **Compatibility claims that fail on the real host** — Impact: rework of persisted artifacts; Frequency: per platform change; Severity: Critical
2. **Access checks copied from a reference system with known gaps** (section 119) — Impact: leakage risk; Frequency: once per boundary; Severity: Critical
3. **Backups that omit original evidence** — Impact: citations that cannot be restored; Frequency: per drill; Severity: High

## Jobs-to-be-Done

1. **When** a dependency version is proposed, **I want to** test one exact combination in containers, **so I can** pin it with evidence.
2. **When** a request reaches the engine, **I want to** verify issuer, audience, and signature before any storage read, **so I can** keep denied paths from touching protected data.
3. **When** a restore is needed, **I want to** recover relational state, content, manifests, and review evidence together, **so I can** keep every citation resolvable.

## Anti-Personas

- **Not:** the end-user underwriter; Dana never adjudicates insurance facts
- **Not:** the production SRE of a cloud host chosen later (section 117.1 item 3)

## Related Personas

- Collaborates with Mateo (ingestion), Ingrid (persistence), Rosa (review binding)
