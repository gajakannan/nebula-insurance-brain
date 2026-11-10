# F0007 personas

These existing personas explain the feature's users. They grant no permissions.

| Persona | Need in F0007 | Observable success |
|---|---|---|
| [Ingrid — Persistence Engineer](../../../examples/personas/persistence-engineer.md) | One durable, owned identity per semantic question that survives concurrency and migration | Concurrent resolution yields one slot; cross-tenant child rows fail at the database; pilot facts read back unchanged |
| [Mateo — Document Intelligence Engineer](../../../examples/personas/document-intelligence-engineer.md) | Extracted claims land in the slot their predicate and qualifiers name | An each-occurrence and an aggregate limit from one declarations page resolve to two slots |
| [Rosa — Business Reviewer](../../../examples/personas/business-reviewer.md) | Distinguish "not read", "not found here" and "not stated" when reviewing | The three states reload distinctly, each absence naming its scope |
| [Priya — GL Underwriter](../../../examples/personas/gl-underwriter.md) | Trust that a limit is an exact amount with currency and basis, and a policy number belongs to its carrier | USD 1,000,000 each occurrence never equals an aggregate limit; two carriers' identical policy numbers stay distinct |

Priya and Rosa see these values through later surfaces (F0020/F0023). F0007 gives them no screen. Internal service principals act under F0002's verified scope. No external persona is admitted.
