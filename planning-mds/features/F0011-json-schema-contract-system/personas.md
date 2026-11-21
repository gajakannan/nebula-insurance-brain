# F0011 — Personas and jobs

These are feature-scoped uses of existing personas, not new runtime roles.

| Persona | F0011 job | Success evidence | Existing definition |
|---------|-----------|------------------|---------------------|
| Dana the Platform Engineer — primary | Publish a deterministic local contract bundle and detect Python/AJV/OpenAPI drift before release | Clean-package reproduction, zero conformance mismatches, intentional drift refused | [Platform Engineer](../../examples/personas/platform-engineer.md) |
| Ingrid the Persistence Engineer — primary | Integrate strict contracts without changing accepted typed answers, precision or atomic writes | Real consumer acceptance/refusal, unchanged history and no partial mutation | [Persistence Engineer](../../examples/personas/persistence-engineer.md) |
| Mateo the Document Intelligence Engineer — secondary | Consume the pinned content/assertion/result definitions in extraction adapters | Explicit legacy/current version dispatch and schema-valid output | [Document Intelligence Engineer](../../examples/personas/document-intelligence-engineer.md) |

These engineers need structural diagnostics without protected source content.
Underwriters and stewards benefit through later consumers; no schema administration
or business-review UI is added by F0011.
