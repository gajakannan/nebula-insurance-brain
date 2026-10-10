# ADR-0070: Account, Party and Role Model for Commercial P&C

## Status

- [x] Proposed
- [ ] Accepted
- [ ] Superseded
- [ ] Rejected

**Date:** 2026-10-10
**Direction authorized by:** Operator, 2026-10-10, as the domain owner's answer to the account decision in [BLUEPRINT section 4.8](../../BLUEPRINT.md#48-open-decisions). Formal acceptance waits for the proof gates below.
**Would refine:** [ADR-0011](ADR-0011-ontology-is-versioned-and-modular.md) (shared account and party concepts in the foundation module) and the account scope inside [ADR-0062](ADR-0062-current-authorization-and-durable-decisions.md)'s ResourceScope. It does not change ADR-0062's accepted F0002 boundary.
**Aligns with:** the canonical contracts in `nebula-insurance-data-contracts` (`Party`, `PartyRelationship`, `Account`, `AccountRelationship`, `AccountPartyRole`, `PolicyPartyRole`); see [Cross-repository alignment](#cross-repository-alignment).

## Context

The glossary defined Account as the business entity seeking or holding coverage and the root of Entity 360. The Cedar Bridge teaching example instead modeled one account grouping several legal organizations. Under that model, an account-scoped grant would reach every grouped organization. Section 4.8 left four questions open: is Account a party or a grouping; what does account scope reach; what is the Entity 360 root; and how does account identity relate to organization identity.

The operator answered them from commercial P&C practice:

- **One account per organization.** An insured is usually an organization. A corporate family such as ACME Technologies has a separate account for each organization (ACME AI, ACME China, ACME India, ACME Robots). Each account links to its parent's account.
- **Ownership is not always simple.** A subsidiary can be wholly owned, majority owned or a joint venture.
- **Policies span accounts.** A property policy can cover a parent and all its subsidiaries, while GL covers only some of them.
- **People and organizations play scoped roles:**
  - insured side: organization contact, account contact, risk manager;
  - carrier side: distribution contact, marketing representative, underwriter, underwriting assistant, operations contact;
  - broker side: a broker contact, who works for neither the insured nor the carrier.
  The same person or different people can fill a role for each organization.
- **Brokers follow the party model.** A broker is an organization with its own hierarchy, branches, offices and people.
- **Broker of record can differ by line.** It is uncommon, but each line of business can come through a different broker.
- **Roles are not access.** Carrier employees are not restricted to their own accounts or lines. A property underwriter makes property decisions and a GL underwriter makes GL decisions. These assignments show who does what (Account 360); they do not decide what someone can see.

## Proposed Decision

### 1. Parties

- **Party** is a person or an organization. Insureds, brokers, carriers, MGAs and joint-venture partners are all organizations. "Broker" or "carrier" is a role an organization plays in a scope, not a kind of organization.
- **Organization hierarchy.** An organization can have a parent organization: a branch under a brokerage, or a division under a company. The hierarchy is effective-dated and has no fixed depth.
- **Locations.** An organization operates at locations (offices, premises, yards). Operating at a location does not make it insured property.
- **Employment.** A person can be employed by an organization or one of its branches. Employment is separate from any role the person plays.

### 2. Accounts

- **One account per organization.** An account is the customer relationship with exactly one organization (`Account.primary_party_uid` in the canonical contracts). No organization has two accounts in one tenant. Account identity and organization identity resolve separately (F0017), and an account merge follows the survivor rules of the owning system.
- **Designated parent account.** Each account has at most one parent account. The parent is designated, not computed. It drives roll-up and the Account 360 hierarchy. A root account has no parent. Further relationships, such as a billing parent, can be added later as typed account relationships; they never replace the single designated parent.
- **Ownership is separate.** Ownership is a relationship between organizations. It carries the owner, the owned organization, a percentage and valid time. An organization can have several owners.
  - *Majority owner* is computed (more than 50 percent), not stored.
  - A 50/50 joint venture has no majority owner, but its account still has one designated parent.
  - The owners' percentages do not need to agree with the account hierarchy. A minority owner can have its own account without being the account parent.

### 3. Policies and accounts

- **No single owning account.** A policy term names its insureds through named-insured role assignments. Each named insured's account sees the policy, so one policy can appear under several accounts.
- **Roll-up.** An account's portfolio is the set of policies naming its organization. A parent's roll-up adds its descendants' portfolios, each policy counted once.
- **Not inferred.** Being under a parent account, or being owned by another organization, never makes an organization a named insured.
- **Submissions** belong to the account they were submitted for.

### 4. Scoped role assignments

A role assignment records:

- **the party** in the role;
- **the role kind** (named insured, servicing broker, placement broker, broker contact, risk manager, account contact, underwriter, …);
- **the scope:** an account, a submission or a policy term. A policy term implies its line of business;
- **who the party acts for**, when it is a person: the organization or branch they represent in that role;
- **valid time,** following [ADR-0064](ADR-0064-time-interpretation-and-valid-time-precision.md): the party in a role is a `STATE` fact.

Rules:

- **Broker of record** is a placement-broker assignment scoped to a policy term, so it can differ by line and term. A servicing broker is scoped to an account.
- **Duplicates are expected.** Each organization's account can have its own contacts. One person can hold roles on several accounts, and two people can hold the same role kind on different accounts.
- **Role kinds are open vocabulary,** owned by F0012/F0013. The canonical `PartyRoleTypeCode` codeset is the external reference.

### 5. Roles and access

- **Domain roles never grant access.** Authorization stays with ADR-0050/ADR-0062 grants. A broker contact, risk manager or underwriter assignment creates no membership, grant or delegation.
- **Carrier staff.** In a carrier tenant, internal staff hold tenant- or knowledge-base-wide grants. Underwriter and other carrier role assignments are used for Account 360, work routing and decision attribution, not visibility.
- **Account-scoped grants**, where a deployment uses them (for example for an external principal), reach exactly the granted account:
  - its organization's records;
  - its submissions;
  - policy terms naming its organization.

  A grant does not expand to descendant or sibling accounts. Seeing a whole hierarchy needs a grant on each account, or a future explicit hierarchy grant designed under F0002's successor scope.
- **Shared policies.** A policy that also names an organization outside the grant is visible because of the granted named insured. Any restriction of the other insureds' details inside that policy is a classification concern under ADR-0062, not an account-model rule.

### 6. Entity 360

- **Root.** The Account 360 root is one account: its organization, its portfolio, its role assignments, and links to its parent and children.
- **Roll-up view.** The hierarchy view rolls portfolios up without merging them. Each policy appears once, with the accounts whose organizations it names.

## Cross-repository alignment

- **nebula-insurance-data-contracts.** This model maps onto the canonical contracts:
  - `Account.parent_account_uid` is the designated parent;
  - `Account.primary_party_uid` is the account's organization;
  - `AccountPartyRole` and `PolicyPartyRole` are the scoped roles;
  - `PartyRelationship` holds organization hierarchy and ownership.

  Gaps to raise there, not decided here:
  - an ownership percentage on `PartyRelationship`;
  - a line-of-business or policy-term qualifier for account-level broker roles;
  - an acting-for organization (branch) on role contracts;
  - a uniqueness rule of one account per organization.
- **nebula-insurance-crm.** The CRM's account module says an account "belongs to broker" (one broker per account), and its ADR-026 models the distribution tree as hierarchy nodes. Per-line brokers of record and broker branches as organizations need reconciling there. The Brain does not change CRM contracts.

## Consequences

- **Glossary.** The glossary's Account definition becomes one organization's customer relationship, and the open decision in section 4.8 closes.
- **Cedar Bridge example.** It is re-expressed as:
  - one account each for Holdings, Workshop, Contracting and the joint-venture partner;
  - designated parent accounts;
  - a 60/40 joint venture;
  - a broker branch with a contact person;
  - a second broker for the auto line;
  - per-line carrier underwriters.
- **Downstream features:**
  - F0012 adds these classes and properties to the foundation module;
  - F0017 resolves account and organization identity separately;
  - F0023 roots Entity 360 on one account with a hierarchy roll-up.
- **Authorization.** F0002 is archived, so implementing account-scoped grants as written above needs its own scope amendment; nothing here changes delivered behavior.
- **Data model.** The proposed records are listed in [data-model.md](../data-model.md#proposed-party-account-and-role-records-adr-0070).

## Proof gates

Before acceptance:

1. F0012 Phase B authors these classes and properties with `temporal_kind`, definitions and regression cases (ADR-0063, ADR-0064).
2. The Cedar Bridge cases EX-PC-001 and EX-PC-015 to EX-PC-017 pass the `semantic_examples` and `semantic_rdf` gates.
3. F0017 states how account identity and organization identity resolve and merge.
4. The account-scoped grant reach in section 5 is either accepted in an F0002-successor scope amendment or replaced there.

## References

- [BLUEPRINT section 4.8](../../BLUEPRINT.md#48-open-decisions)
- [Cedar Bridge walkthrough](../../examples/commercial-pc-account/README.md) and [cases](../../examples/commercial-pc-account/cases.md)
- [Commercial P&C handoff](../commercial-pc-example-handoff.md)
- `nebula-insurance-data-contracts/references/patterns/pc/account-pattern.md` and `party-role-pattern.md`
- `nebula-insurance-crm/planning-mds/architecture/decisions/ADR-026-broker-mga-hierarchy-producer-ownership-and-territory.md`
