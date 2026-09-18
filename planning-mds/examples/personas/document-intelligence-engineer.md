# Persona: Mateo the Document Intelligence Engineer

**Role/Title:** Document Intelligence Engineer, Nebula Insurance Brain
**Archetype:** Internal builder — owns the Docling-Graph document pipeline, durable parse reuse, and evidence contracts
**Priority:** Primary (F0001, F0004, F0005, F0016)

## Demographics & Background

**Experience Level:** 5+ years in document extraction pipelines; has shipped OCR and layout-analysis systems for insurance and financial documents
**Technical Proficiency:** High
**Daily Responsibilities:**
- Persist parse-once content artifacts with complete manifests
- Run and compare semantic interpretations over persisted content
- Keep evidence locators honest about their precision

## Goals & Motivations

### Primary Goals
1. Never re-parse a document version to add a field (ADR-0003, ADR-0016)
2. Every extracted value carries a locator that resolves to an immutable block with declared precision (section 108.2)
3. Failed or partial parses are visible, never silent negatives (section 108.3)

### Success Metrics
- Second-interpretation conversion and OCR calls equal zero; citation resolution rate on the fixture package

## Pain Points & Frustrations

1. **Pipelines that flatten the document and lose the native representation** — Impact: reinterpretation forces reparse; Frequency: every schema change; Severity: Critical
2. **Bounding boxes invented from page-level grounding** — Impact: reviewers lose trust; Frequency: scanned documents; Severity: High
3. **Model confidence treated as calibrated probability** — Impact: wrong facts committed; Frequency: daily; Severity: High

## Jobs-to-be-Done

1. **When** a policy package arrives, **I want to** parse it once into a bundle with the native DoclingDocument JSON, **so I can** reinterpret it forever without conversion.
2. **When** a new extraction profile is added, **I want to** run it on persisted content only, **so I can** prove reuse with counters.
3. **When** a page fails, **I want to** record partial status and a review item, **so I can** keep an empty extraction from becoming a negative fact.

## Anti-Personas

- **Not:** the ontology steward who decides what a coverage means
- **Not:** the business reviewer who corrects values

## Related Personas

- Hands off low-confidence assertions to Rosa; depends on Dana for the stack and Ingrid for commits
