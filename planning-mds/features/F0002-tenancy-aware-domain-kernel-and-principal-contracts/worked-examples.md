# F0002 — EX-AUTHX contract examples

**Provenance:** Synthetic development examples, authored expected outcomes; no production data.
**Delivery:** v0.1A; all outputs below are illustrative, not observed runtime evidence.
**Contract:** [PRD](PRD.md#data-requirements), its exact pilot role table, and the six linked story acceptance contracts. Phase B adds machine-readable contracts where needed; these prose cases do not claim schema validation.

## Continuing insurance case

Reuse [EX-GL-001](../../examples/neurosymbolic-gl/README.md): an account/policy may be referenced by two KBs within one tenant. Its tenant-scoped identity does not make all policy facts, source documents or assessment evidence visible in both KBs. An underwriter with access only to the first KB cannot read a restricted loss-note-derived result through the shared account. F0065 owns actual assessment behavior; F0002 supplies the authorization contract and bounded synthetic dependency fixture.

Tenant A/B, workspace A/B, KB A1/A2 and issuer X/Y are fixture labels. Every positive operation also needs the exact applicable pilot role grant; no persona name implies a grant.

## Cases

| ID | Owning F0002 story | Setup / action | Expected outcome | Boundary / failure |
|---|---|---|---|---|
| EX-AUTHX-001 | S0001 | Tenant A / workspace A / KB A1; valid owned record | Accept the association; reload preserves ownership and audit reference | Swap parent to tenant B: reject, no partial write |
| EX-AUTHX-002 | S0001/S0003 | One tenant entity E referenced by KB A1 and A2; actor has only A1 access | Resolve E within permitted A1 context | A2 reference gives no A2 membership, evidence, count or existence disclosure |
| EX-AUTHX-003 | S0001 | Same external account identifier in tenants A and B | Distinct tenant identity spaces | A’s reference cannot select B’s entity |
| EX-AUTHX-004 | S0002 | Verified issuer X / subject U resolved repeatedly and concurrently | One durable principal ID, preserved across restart | Same subject at issuer Y is distinct absent approved identity link |
| EX-AUTHX-005 | S0002 | Malformed, expired, not-yet-valid, invalid-signature, wrong-issuer/audience/type credentials | Generic unauthenticated outcome; safe authentication audit | No principal provisioning, membership or protected resource lookup |
| EX-AUTHX-006 | S0002 | Disabled principal, forged kind/roles, or unapproved identity migration | Deny access or require explicit identity reconciliation | No email-based auto-link or rewritten historical actor |
| EX-AUTHX-007 | S0003 | Two permitted grant slices and a request filter within one | Union authority, then intersection with filter | Filter for an ungranted broker/account/KB never adds it |
| EX-AUTHX-008 | S0003 | Membership revoked or expired after a prior successful request | Next protected operation denies under current revision | Past business valid/known time does not reinstate authority |
| EX-AUTHX-009 | S0003 | Reviewer role in A1, read-only membership in A2 | Role permissions apply only in the granting scope | A1 role cannot authorize annotation in A2; unavailable grants fail closed |
| EX-AUTHX-010 | S0004 | Membership/action/parent allow; classification denies | Deny without protected content; internal reason auditable | Also invert parent/classification; a passing dimension cannot override a deny |
| EX-AUTHX-011 | S0004 | Permitted classification, denied source ACL; forged request attributes | Deny using trusted resource attributes | Missing required parent/classification/source state does not mean unrestricted |
| EX-AUTHX-012 | S0004 | Derived-resource fixture uses two evidence dependencies; actor may access one | Deny the derived resource; visible entity is insufficient | All dependencies permitted enables only the independently permitted action |
| EX-AUTHX-013 | S0004 | Reviewer annotates an authorized current task | Annotation persists with authenticated reviewer | Revoked access before submit denies; annotation never grants fact_slot:commit |
| EX-AUTHX-014 | S0005 | Agent acts for user under valid action/resource/expiry ceiling | Allow only intersection of user’s current authority and delegation | One-sided allow, forged delegate, unregistered action or onward delegation denies |
| EX-AUTHX-015 | S0005 | Grant or delegation revoked/expired between job operations | Next protected operation denies | Earlier success and cached context confer no continuing authority |
| EX-AUTHX-016 | S0005 | Autonomous ServicePrincipal has explicit permitted pilot grant | Allow bounded operation and audit service identity without fictitious human | No default tenant-wide privilege or direct canonical-write bypass |
| EX-AUTHX-017 | S0006 | Allowed and denied calls through existing content/fact/review consumers | Outcome and audit agree; policy/grant versions and trace recorded | Tokens/protected payload absent; denied mutations leave no state |
| EX-AUTHX-018 | S0006 | Audit persistence fails during a protected operation | No unaudited successful protected operation | No success response or committed mutation without required durable decision evidence |

## Definitions and ownership

Tenant, Workspace, Knowledge Base and Principal use the existing [glossary](../../domain/glossary.md). Membership is a current trusted scope association; ResourceScope is permitted resources; delegation is an explicit expiring authority ceiling; all are requirements in the PRD data table pending Phase B schema/glossary completion. Entity identity is separate from visibility. Authorization time is current enforcement time; business valid/known time selects business history and cannot restore grants.

## Runtime reproduction obligation

S0006 must map each case to executable consumer tests, independently maintained expectations, actual results and an exact command in implementation evidence. Reject attempts to count an example or schema pass as observed runtime proof. Keep these development examples outside the frozen evaluation holdout.
