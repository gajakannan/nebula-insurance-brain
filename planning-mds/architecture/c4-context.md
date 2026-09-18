# C4 Level 1 — System Context

Created 2026-09-06 (F0001 Phase B); revised 2026-09-08 for ADR-0057 (native review panel). Updated 2026-09-15 for the planned ADR-0060 document pipeline. Master blueprint sections 100, 125, and 126 are the narrative source.

```mermaid
C4Context
    title Nebula Insurance Brain — System Context
    Person(worker, "Insurance knowledge worker", "Underwriters, analysts; Entity 360, Document 360, chat (from F0021)")
    Person(reviewer, "Business reviewer", "Adjudicates evidence in the Nebula Review Panel")
    Person(engineer, "Platform / document intelligence / persistence engineers", "Build and operate the Brain (F0001)")
    System(brain, "Nebula Insurance Brain", "Owns semantics: evidence, assertions, canonical bitemporal truth, ontology, provenance, audit")
    System_Ext(authentik, "authentik", "OIDC identity provider")
    System_Ext(docling, "Docling-Graph (planned)", "In-process document pipeline; Docling converts underneath; F0005 integration gate")
    System_Ext(vllm, "vLLM inference service", "microsoft/Phi-4-mini-instruct, OpenAI-compatible, host GPU")
    System_Ext(sources, "Enterprise sources", "Policy documents, endorsements, loss runs, systems of record")
    Rel(worker, brain, "Explores, converses, investigates", "HTTPS")
    Rel(reviewer, brain, "Reviews evidence, submits decisions", "HTTPS")
    Rel(brain, authentik, "Verifies tokens (issuer, audience, signature)", "OIDC / JWKS")
    Rel(brain, docling, "Coordinates conversion and extraction; Nebula retains artifact and evidence contracts")
    Rel(brain, vllm, "Chunk text only; no identity data", "OpenAI-compatible HTTP")
    Rel(sources, brain, "Documents parsed once", "ingestion")
    Rel(engineer, brain, "Operates, proves contracts")
```

Boundaries: the Brain owns semantics (ADR-0001); every external system is an engine around it. Human evidence adjudication is not external: the Review Panel is part of the Brain, so evidence never leaves the trust boundary to be reviewed (ADR-0057). Denied paths terminate before protected data enters model context or a canonical mutation occurs (section 118.2).

Docling-Graph is a proposed in-process library, shown here to explain the target dependency boundary. F0001 uses Docling plus a direct vLLM adapter; ADR-0060 does not add an external service. Temporal remains a later durable business-workflow dependency, separate from document-stage coordination.
