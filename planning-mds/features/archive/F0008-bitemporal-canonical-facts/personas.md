# F0008 personas

These existing personas explain who uses the feature. They grant no permissions.

| Persona | What they need from F0008 | How success shows |
|---|---|---|
| [Ingrid — Persistence Engineer](../../../examples/personas/persistence-engineer.md) | Version rows whose overlap and immutability rules the database enforces, not only the service | Concurrent commits leave one state per coordinate. A hand-written UPDATE of a historical payload fails. Pilot rows are unchanged after migration. |
| [Rosa — Business Reviewer](../../../examples/personas/business-reviewer.md) | A correction or retraction never erases what the Brain believed before, and an unknown end is never shown as current | Every superseded belief reads back at its recorded coordinate. The prior-carrier fact reads `UNKNOWN` on 2026-07-15. |
| [Priya — GL Underwriter](../../../examples/personas/gl-underwriter.md) | Ask what a limit was on a date, and what the Brain knew on a date, and get one answer to each | The §87 grid answers $2M, $5M, $2M and $5M. "June 1" is June 1 in the insured's zone. |
| [Mateo — Document Intelligence Engineer](../../../examples/personas/document-intelligence-engineer.md) | Template effective dates land with the precision, zone and basis they were read with | A DAY-granular template date commits with basis `TEMPLATE_FIELD`. A mis-truncated bound is refused, with a reason, before any write. |

Priya and Rosa see these answers through later surfaces (F0020, F0022 and F0023); F0008 gives them no screen. Internal service principals act under F0002's verified scope. No external persona is admitted.
