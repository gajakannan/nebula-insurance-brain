# F0004 personas

These are feature-specific applications of existing product personas, not newly researched users or new permission roles.

## Mateo — Document Intelligence Engineer (primary)

**Source:** [Existing persona](../../../examples/personas/document-intelligence-engineer.md). Internal builder with high technical proficiency; owns durable parse reuse and evidence fidelity.

**Job:** when a saved policy needs another interpretation, retrieve the native content and attributable normalized views without conversion. His pain is losing source structure or repeating OCR after a model/profile change.

**Success:** one verified persisted bundle survives restart, two profile runs call no converter/OCR, and each block retains honest origin and precision. S0001, S0002 and S0004 serve this job.

## Ingrid — Persistence Engineer (supporting)

**Source:** [Existing persona](../../../examples/personas/persistence-engineer.md). Internal builder responsible for durable records and ownership integrity.

**Job:** retain source/artifact/run identity, document-date provenance and byte references without rewriting accepted history. Her pain is a database row claiming a complete artifact while bytes are missing, or a migration fabricating historical metadata.

**Success:** metadata and bytes restore together, old contracts stay readable, invalid/cross-owner references fail, and corrections have audit lineage. S0001, S0003 and S0004 serve this job.

## Rosa — Business Reviewer (downstream beneficiary)

**Source:** [Existing persona](../../../examples/personas/business-reviewer.md). Internal commercial-lines analyst with medium technical proficiency; review authority remains scoped.

**Job:** distinguish a source date from receipt time and source text from OCR or a generated description, with an inspectable origin and anchor.

**Success:** S0002/S0003 expose truthful metadata for F0022's review surface. F0004 adds no controls or reviewer grants; Rosa is not a canonical approver merely because she reviews evidence.

## Excluded personas

External brokers/MGAs are outside this v0.1 scope. Ontology stewards, calendar-resolution services and automated deciders do not gain workflows in F0004.
