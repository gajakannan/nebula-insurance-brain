# F0012 personas

These are existing product personas, reused without inventing research or runtime roles.

| Persona | Job in F0012 | Pain / required outcome | Story ownership |
|---|---|---|---|
| [Sameer — Domain Steward](../../examples/personas/domain-steward.md) | Owns what a foundation term means; reviews a release's impact before it is activated | A definition edited in place or a newer release silently applied to old work; needs explicit change classes and a reviewed report before activation | S0001, S0002, S0003, S0006 |
| [Ingrid — Persistence Engineer](../../examples/personas/persistence-engineer.md) | Installs immutable releases and keeps predicate contracts and temporal kinds consistent with the kernel | A mutated release or floating dependency makes history irreproducible; a failed install must leave no partial rows | S0004, S0005, S0007 |
| [Mateo — Document Intelligence Engineer](../../examples/personas/document-intelligence-engineer.md) | Consumes predicate contracts and the release a future interpretation run pins | Needs registered predicates with exact cardinality, value type and temporal kind; unregistered keys must stay refused | Contributor to S0005, S0007 |

Success means every planned acceptance criterion later has observed proof, no published term or release changes meaning silently, and no persona gains install or activation authority implicitly. Sameer's workbench remains F0030; these requirements use command-line and service entry points.
