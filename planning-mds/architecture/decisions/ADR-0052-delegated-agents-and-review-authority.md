# ADR-0052: Delegated Agents and Review Authority

## Status

- [x] Proposed
- [ ] Accepted
- [ ] Superseded
- [ ] Rejected

**Date:** 2026-09-05 (record created from the master blueprint baseline)
**Decision recorded:** 2026-11-08 by the operator (blueprint requirement-ownership amendment). Features plan against the decision below. The status stays Proposed until the carryover tests below pass.
**Owner:** Architect + Security Reviewer
**Proving features:** F0022 (review authority, v0.1), F0018 (commit path), F0047/F0059 (agent delegation, v0.2+)
**Formal acceptance:** section 121.2 item 7 (review authority) passes in F0022; item 10 (delegation) passes when the first agent-acting feature (F0047) ships.
**Source:** `planning-mds/architecture/master-blueprint.md` sections 120.4 and 122

## Context

ADR-0057 moved review into the authenticated Nebula session, so the reviewer is the session principal. ADR-0044 (Accepted) separates annotation and adjudication from business approval. What remains is the authority model for reviewers and future agents.

## Decision

1. **Reviewers act as themselves.** The reviewer identity is the verified session principal (ADR-0049). Payload-supplied identity is ignored.
2. **Review is adjudication, not approval.** A submitted review decision records what the evidence says. Promotion to canonical truth goes through the F0018 commit service, which re-authorizes it and checks current assertion and ontology revisions.
3. **Current grants at assembly and submission.** A review batch shows only evidence the reviewer is entitled to now, and is checked again on submission. A stale task fails closed.
4. **No agent delegation in v0.1.** v0.1 workers run as service principals with no human delegate and no canonical write path except the commit service. Their credentials cannot perform business writes.
5. **Bounded delegation from v0.2.** When agents act for users (F0047 onward), the record keeps `acting_user_id`, `agent_principal_id`, delegation ID, allowed actions and resources, expiry and policy version. Effective authority is the intersection of the user's current grant and the delegation ceiling. Agents never write canonical tables directly.

## Consequences

- F0022 owns reviewer authority and stale-task handling; F0018 owns re-authorization at commit.
- F0047 and F0059 inherit rule 5; nothing in v0.1 issues delegations.

## References

- `planning-mds/architecture/master-blueprint.md` sections 118 to 123; ADR-0044, ADR-0049, ADR-0057
