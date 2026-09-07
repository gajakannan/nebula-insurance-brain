# Persona: Priya the GL Underwriter

**Role/Title:** Commercial General Liability Underwriter
**Archetype:** Internal insurance user — decides whether a submission's coverage meets written guidelines
**Priority:** Primary (F0065, F0024, F0025); the primary reader of the Entity 360 assessment panel

## Demographics & Background

**Experience Level:** 8+ years underwriting GL for middle-market accounts; fluent in limits, bases, and endorsements
**Technical Proficiency:** Medium — lives in underwriting systems and spreadsheets, not in code or query languages
**Daily Responsibilities:**
- Compare an account's applicable each-occurrence limit against the guideline in force for that program
- Reconcile late endorsements against what was known when a decision was made
- Escalate accounts where the documentation does not support an answer

## Goals & Motivations

### Primary Goals
1. See whether the applicable limit meets the specified guideline, with the two compared values in view (F0065-S0002)
2. See which document and which page the limit came from before relying on it (F0065-S0005)
3. Get a different, correct answer after a retroactive endorsement without losing the earlier record (F0065-S0004)

### Success Metrics
- Time from opening an account to a supported answer; rate of answers she has to re-derive by hand; zero cases where she cites a value the system cannot evidence

## Pain Points & Frustrations

1. **A confident-looking answer with no visible inputs** — Impact: she cannot defend it in an audit or a referral; Frequency: per account; Severity: Critical
2. **"No answer" and "does not meet the guideline" rendered the same way** — Impact: she treats a documentation gap as a declination; Frequency: per incomplete submission; Severity: Critical
3. **An answer that silently changed after an endorsement was keyed** — Impact: the file no longer explains the decision that was made; Frequency: per retroactive change; Severity: High
4. **An aggregate limit compared against an each-occurrence guideline** — Impact: a wrong answer that looks right; Frequency: occasional but severe; Severity: High

## Jobs-to-be-Done

1. **When** I open an account in Entity 360, **I want to** see the guideline result with its rule version, time basis, and the two amounts, **so I can** accept it or go to the document.
2. **When** the system cannot answer, **I want to** be told whether the input is missing, conflicting, or out of scope, **so I can** request the right thing instead of guessing.
3. **When** an endorsement lands after the fact, **I want to** ask the question at a chosen effective and known time, **so I can** show what was true then and what is true now.
4. **When** I lack access to a supporting document, **I want to** be denied cleanly, **so I** never build a decision on evidence I cannot open.

## Constraints & Considerations

- Authorization: reads assessments and evidence only within her tenant and knowledge base, and only when she has permission to the complete relevant lineage (assessment contract, Authorization and audit)
- She has no authority to install or amend a guideline rule release; that is a separately authorized administrative act (F0065-S0001)
- An assessment is not an approval — it never issues, binds, or declines the policy

## Anti-Personas

- **Not:** the domain steward who defines and releases the guideline (see [domain steward](domain-steward.md))
- **Not:** a claims adjuster, broker, or external insured (out of v0.1 scope)
- **Not:** a reviewer adjudicating extractions in Label Studio — that is Rosa (see [business reviewer](business-reviewer.md))

## Related Personas

- Consumes canonical facts that Rosa reviewed and that were committed through Ingrid's commit path
- Depends on the guideline releases Sameer stewards
