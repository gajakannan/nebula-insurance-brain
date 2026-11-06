# F0006 personas

These existing personas explain the feature's users; they grant no permissions.

| Persona | Need in F0006 | Observable success |
|---|---|---|
| [Mateo — Document Intelligence Engineer](../../../examples/personas/document-intelligence-engineer.md) | Retain each source claim and its actual grounding, origin, and interpretation basis | A claim reloads with the same evidence; a fabricated quote produces an explicit rejection reason |
| [Ingrid — Persistence Engineer](../../../examples/personas/persistence-engineer.md) | Preserve scoped assertion identity and history as contracts evolve | Conflicting claims coexist, invalid ownership references fail, legacy correction chains survive migration |
| [Rosa — Business Reviewer](../../../examples/personas/business-reviewer.md) | Distinguish what a source says from what has been accepted | Mood and described evidence cannot become facts silently; the original claim remains after a correction |

Rosa's new display affordances belong to F0022. Her existing correction authority remains separate from canonical approval. Internal service principals act under F0002's verified scope; no external persona is admitted.
