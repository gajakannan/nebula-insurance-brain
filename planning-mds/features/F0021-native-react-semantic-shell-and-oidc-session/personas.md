# F0021 personas

Three existing product personas and one new one ([Noor — Security Administrator](../../examples/personas/security-administrator.md), from BLUEPRINT §1.2 "platform operators and security administrators"). No research is invented and no runtime role is added.

| Persona | Job in F0021 | Pain / required outcome | Story ownership |
|---|---|---|---|
| [Rosa — Business Reviewer](../../examples/personas/business-reviewer.md) | Signs in and works in the Review Panel for long sessions | A session that expires mid-review must not lose unsaved input or submit a decision that was not re-confirmed | S0001, S0003, S0004, S0007 |
| [Priya — GL Underwriter](../../examples/personas/gl-underwriter.md) | Daily knowledge worker who will use Entity 360 and Document 360 inside this shell | Needs one sign-in, a clear view of the active tenant and knowledge base, and no stale data after switching | S0001, S0005, S0006 |
| [Noor — Security Administrator](../../examples/personas/security-administrator.md) | Operates authentik, sessions and grants; investigates rejected credentials | No browser-held token; logout that revokes upstream and reports failure; bounded audit growth under attack | S0002, S0005, S0008, S0009 |
| [Dana — Platform Engineer](../../examples/personas/platform-engineer.md) | Runs the local stack and the proof harness; wires later routes into the shell | A route seam that keeps heavy views out of the base bundle; a reproducible real-IdP proof | S0007, S0009 |

Success means every acceptance criterion later has observed proof, no persona's tokens reach browser storage, and no persona gains authority through the shell. Administration screens for Noor are out of scope; their evidence is audit rows and logs.
