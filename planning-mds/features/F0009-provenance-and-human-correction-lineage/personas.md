# F0009 personas

These are existing product personas, reused without inventing research or runtime roles.

| Persona | Job in F0009 | Pain / required outcome | Story ownership |
|---|---|---|---|
| [Rosa — Business Reviewer](../../examples/personas/business-reviewer.md) | Correct an extraction against immutable evidence and retain attributable history | An edit must not erase the machine value or imply canonical approval; stale/duplicate outcomes must stay explicit | S0002, S0004, S0005 |
| [Ingrid — Persistence Engineer](../../examples/personas/persistence-engineer.md) | Explain exact versions and deploy durable lineage | A split remainder must retain its source, and failure must leave no partial correction/reservation | S0001, S0003, S0006 |
| [Mateo — Document Intelligence Engineer](../../examples/personas/document-intelligence-engineer.md) | Supply and preserve evidence/interpretation metadata | Stored parser/model/run identity and evidence precision cannot be replaced with current defaults | Contributor to S0001/S0002 |

Success means every planned acceptance criterion later has observed proof, original source/history remains unchanged and unauthorized callers receive no protected lineage. Rosa's new review UI remains F0022; these requirements use existing entry points. No persona grants annotation, adjudication or canonical authority.
