# Persona: Rosa the Business Reviewer

**Role/Title:** Senior Commercial Lines Analyst acting as Business Reviewer
**Archetype:** Internal insurance user — adjudicates extracted evidence in the Nebula Review Panel
**Priority:** Primary (F0001, F0022, F0026); becomes a primary end-user persona for Document 360

## Demographics & Background

**Experience Level:** 10+ years reading GL policies, endorsements, and loss runs; comfortable with review tools, not with code
**Technical Proficiency:** Medium
**Daily Responsibilities:**
- Confirm or correct extracted limits, dates, and coverage terms against the source page
- Flag documents that need specialist adjudication
- Build the labeled examples that become the Golden Corpus

## Goals & Motivations

### Primary Goals
1. See the exact source region and the predicted value side by side (section 75)
2. Correct once and trust the correction is recorded with lineage (ADR-0037)
3. Never be blamed for a value the system changed after her review (stale-version handling)

### Success Metrics
- Review time per task; correction agreement rate; zero duplicate decisions from replayed callbacks

## Pain Points & Frustrations

1. **Reviewing a value without the page region** — Impact: slow, error-prone review; Frequency: per task; Severity: High
2. **Corrections that overwrite the machine value with no trace** — Impact: no way to audit disagreements; Frequency: per correction; Severity: Critical
3. **Being treated as the approver of canonical truth** when the role is annotation (section 111.2) — Impact: unclear accountability; Frequency: per governance question; Severity: Medium

## Jobs-to-be-Done

1. **When** a low-confidence limit is routed to me, **I want to** see the rendered page, bounding box, and predicted value, **so I can** decide in seconds.
2. **When** I correct a value, **I want to** submit once and see the decision recorded, **so I can** move to the next task without re-checking.
3. **When** the document changed under me, **I want to** be told the task is stale, **so I can** review the current version instead.

## Constraints & Considerations

- Authorization: annotate tasks in her knowledge base; no canonical approval authority (section 111.2)
- Compliance: her identity is verified through the Nebula principal registry, not trusted from the tool

## Anti-Personas

- **Not:** an ontology steward or knowledge-governance approver (F0042)
- **Not:** an external broker or MGA user (out of v0.1 scope)

## Related Personas

- Receives tasks generated from Mateo's assertions; her decisions feed Ingrid's commits in F0018
