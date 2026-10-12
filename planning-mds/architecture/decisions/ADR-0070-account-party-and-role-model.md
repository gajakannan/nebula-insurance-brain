# ADR-0070: Account, Party and Role Model for Commercial P&C

## Status

- [x] Proposed
- [ ] Accepted
- [ ] Superseded
- [ ] Rejected

**Date:** 2026-10-10
**Direction authorized by:** Operator, 2026-10-10, as the domain owner's answer to the account decision in [BLUEPRINT section 4.8](../../BLUEPRINT.md#48-open-decisions). Formal acceptance waits for the proof gates below.
**Would refine:** [ADR-0011](ADR-0011-ontology-is-versioned-and-modular.md) (shared account and party concepts in the foundation module). **Would amend:** [ADR-0062](ADR-0062-current-authorization-and-durable-decisions.md) with a role-based reach and decision check (section 5), through an F0002-successor scope amendment. Until then, ADR-0062's accepted F0002 boundary is unchanged.
**Aligns with:** the canonical contracts in `nebula-insurance-data-contracts` (`Party`, `PartyRelationship`, `Account`, `AccountRelationship`, `AccountPartyRole`, `PolicyPartyRole`); see [Cross-repository alignment](#cross-repository-alignment).

## Context

The glossary defined Account as the business entity seeking or holding coverage and the root of Entity 360. The Cedar Bridge teaching example instead modeled one account grouping several legal organizations. Under that model, an account-scoped grant would reach every grouped organization. Section 4.8 left four questions open: is Account a party or a grouping; what does account scope reach; what is the Entity 360 root; and how does account identity relate to organization identity.

The operator answered them from commercial P&C practice on 2026-10-10, then refined the answers the same day:

- **One account per organization.** An insured is usually an organization. A corporate family such as ACME Technologies has a separate account for each organization (ACME AI, ACME China, ACME India, ACME Robots). Each account links to its parent's account.
- **Ownership is not always simple.** A subsidiary can be wholly owned, majority owned or a joint venture: 60/40, 50/50, three or four equal owners.
- **Brokers bring accounts to carriers.** From the carrier's view, each account has a broker of record and a broker contact. Brokers of record change over time; that workflow is not being built, but the link must keep its history.
- **Brokers follow the party model.** A broker is an organization with its own hierarchy, branches, offices and people. Each line of business can, uncommonly, come through a different broker.
- **A policy belongs to one account.** A policy naming several organizations names one first and the rest as additional named insureds. A multinational master program sits under the parent account, with a local policy under each entity's account; the program-to-policy link gives the family view.
- **People and organizations play scoped roles:**
  - insured side: organization contact, account contact, risk manager;
  - carrier side: distribution contact, marketing representative, underwriter, underwriting assistant, operations contact;
  - broker side: a broker contact, who works for neither the insured nor the carrier.
  The same person or different people can fill a role for each organization.
- **External people see only their own accounts.** ACME Technologies' broker contact cannot see ACME India, and ACME India's broker contact cannot see ACME Technologies.
- **Carrier staff can see, but not do.** Carrier employees can see across accounts and lines. Only the property underwriter makes property decisions, and only the GL underwriter makes GL decisions.

## Proposed Decision

### 1. Parties

- **Party** is a person or an organization. Insureds, brokers, carriers, MGAs and joint-venture partners are all organizations. "Broker" or "carrier" is a role an organization plays in a scope, not a kind of organization.
- **Organization hierarchy.** An organization can have a parent organization: a branch under a brokerage, or a division under a company. The hierarchy is effective-dated and has no fixed depth.
- **Locations.** An organization operates at locations (offices, premises, yards). Operating at a location does not make it insured property.
- **Employment.** A person can be employed by an organization or one of its branches. Employment is separate from any role the person plays.

### 2. Accounts

- **One account per insured organization.** An account is the carrier's customer relationship with exactly one insured or prospective insured organization (`Account.primary_party_uid` in the canonical contracts). The uniqueness boundary is the tenant: no organization has two current accounts in one tenant, whichever system recorded them. A CRM or policy-system identifier for the same organization is an alias on the one account, not a second account. A closed account keeps its history and does not block a new one; a merge closes the losing account and moves its aliases to the survivor. Brokers, broker branches, carriers and MGAs are organizations without accounts. Account identity and organization identity resolve separately (F0017).
- **Lifecycle and uniqueness.** The account-to-organization identity link remains `ETERNAL` after closure. Lifecycle is a separate `STATE` fact, selected at explicit valid and known times. The teaching vocabulary uses `accountStatus = CURRENT | CLOSED`: `CURRENT` means non-closed, not a production status-code taxonomy. Count only current accounts for uniqueness in one tenant; preserve closed accounts and their policy history. Closure ends the prior current interval and begins a closed interval; a replacement's current interval may start at that same exclusive end boundary. Missing or unknown lifecycle state is incomplete data, not evidence of closure. The example shape requires one known status for each admitted account. F0012/F0017 must enforce the tenant-wide invariant across knowledge bases and both time dimensions at canonical admission; the example checks only one selected tenant snapshot.
- **Broker of record.** Each account has a broker of record (a broker organization or branch) and one or more broker contacts (people acting for it). Both are dated role assignments: a change of broker closes one assignment and opens another, so history is kept. A policy term can name a different placement broker, which overrides the account's broker for that line. A term that names no placement broker shows its account's broker of record.
- **Designated parent account.** Each account has at most one parent account, and an account is never its own parent or ancestor. The parent is designated, not computed. It drives roll-up and the Account 360 hierarchy. A root account has no parent. Further relationships, such as a billing parent, can be added later as typed account relationships; they never replace the single designated parent.
- **Ownership is separate.** Ownership is a relationship between organizations. It carries the owner, the owned organization, a percentage and valid time. Any number of owners is allowed, so 50/50, 33.33 and 25/25/25/25 joint ventures need no winner. At any one valid and known time, the recorded percentages for one organization total at most 100; less is allowed when some owners are unknown.
  - *Majority owner* is computed (more than 50 percent), not stored.
  - A single parent keeps roll-up honest: a joint venture under two parents would be counted twice.
  - With a majority owner, the joint venture's parent is normally that owner's account. With none, it is a root account unless the business designates a parent, which may be a minority owner's account (for example, a 40/30/30 venture under the 40 percent owner). Parentage is never inferred from ownership; Account 360 shows the designated parent.
  - Every owner's Account 360 lists the joint venture as an ownership interest with its percentage, outside its own roll-up.

### 3. Policies and accounts

- **One owning account.** A policy belongs to exactly one account, normally the first named insured's. Other named insureds are named-insured role assignments on the term. Their accounts show the policy as one they are named on, not one they own.
- **Programs.** A program (the canonical `MASTER_PROGRAM` Agreement) belongs to the parent account. Its master policy belongs to the parent account too; each entity's local policy belongs to that entity's account. Every policy links to the program (`Policy.agreement_uid`), at most one each. The family view is derived from those links, not from a policy belonging to several accounts.
- **Roll-up.** An account's portfolio is the policies it owns. A parent's roll-up adds its descendants' portfolios, so each policy is counted once.
- **Independent ownership selection.** An owned policy appears in Account 360 even when a named-insured assignment is missing or expired; insured roles enrich that row when available. A non-owned policy appears in the named-on section only with a current first or additional named-insured assignment. Ownership never supplies an inferred insured role (EX-PC-020).
- **Not inferred.** Being under a parent account, or being owned by another organization, never makes an organization a named insured.
- **Additional insured is a different role.** An additional named insured has named-insured rights. An additional insured, such as a landlord or a general contractor added by endorsement, is a third party with narrower rights and its own role kind.
- **Submissions** belong to the account they were submitted for.

### 4. Scoped role assignments

A role assignment records:

- **the party** in the role;
- **the role kind** (named insured, broker of record, placement broker, broker contact, risk manager, account contact, underwriter, …);
- **the scope:** an account, a submission or a policy term;
- **a coverage qualifier,** optional on a policy-term role: the coverage parts of that term the role covers, such as the property section of a package. Without it, the role covers the whole term. A policy term does not imply one line of business: a package such as a BOP has several;
- **who the party acts for**, when it is a person: the organization or branch they represent in that role;
- **valid time,** following [ADR-0064](ADR-0064-time-interpretation-and-valid-time-precision.md): the party in a role is a `STATE` fact.

Rules:

- **Broker of record** is scoped to an account. A **placement broker** is scoped to a policy term, so it can differ by line and term.
- **First and additional named insureds are separate role kinds.** Which party is first named is recorded, never recovered from the policy's account.
- **Duplicates are expected.** Each organization's account has its own contacts. One person can hold roles on several accounts, and two people can hold the same role kind on different accounts.
- **Role kinds are open vocabulary,** owned by F0012/F0013. The canonical `PartyRoleTypeCode` codeset is the external reference.

### 5. Roles and access

Role assignments now feed access. This section is a proposed amendment to the F0002 authorization boundary, not a change to delivered behavior.

- **External principals reach what their roles name.** A broker contact, insured contact or other external person reaches exactly the scopes of their current role assignments:
  - an **account** role reaches the account's organization, its submissions and the policies it owns;
  - a **policy-term** role reaches that policy only, not the account it belongs to;
  - a **submission** role reaches that submission only.

  Nothing cascades. Reach never expands to parent, child or sibling accounts, from a program or master policy to its local policies, or from a policy to its account. Being on an organization's account does not reach a policy owned by another account that names that organization; a role on that policy does.
- **Carrier staff see everything and act by role.** Internal staff hold tenant- or knowledge-base-wide read grants. A decision or change also needs a current role assignment of the right kind on that term, submission or account. On a policy term, the role must cover the coverage decided on: a package underwriter decides every section, and a property underwriter narrowed to the property section decides nothing on its liability section.
- **Only authoritative roles count.** A role extracted from a document is a reading, not a grant. A role counts for access only once carrier operations, a broker-of-record letter or another trusted system has confirmed it. Otherwise a forged submission could grant access to itself.
- **Revocation is immediate.** Ending a role assignment ends the reach or decision right it supported, including for historical reads (ADR-0062).
- **Evaluation.** The role check is a typed restriction added to ADR-0062's evaluator, next to membership and classification checks; Casbin policy rows stay as they are. Every allow and deny is audited as ADR-0062 requires.

### 6. Entity 360

- **Root.** The Account 360 root is one account: its organization, its broker of record and contacts, its own policies, the policies it is named on, its role assignments, and links to its parent and children.
- **Roll-up view.** The hierarchy view rolls the owned portfolios up without merging them, so each policy appears once.
- **Ownership interests** appear in their own section with percentages, outside the roll-up.

## Cross-repository alignment

The operator aligns both repositories separately, following the [cross-repository plan](../account-model-cross-repo-plan.md).

- **nebula-insurance-data-contracts.** This model maps onto the canonical contracts:
  - `Account.parent_account_uid` is the designated parent;
  - `Account.primary_party_uid` is the account's organization;
  - `Policy.account_uid` is the one owning account;
  - `Agreement` with type `MASTER_PROGRAM`, linked by `Policy.agreement_uid`, is the program;
  - `AccountPartyRole` and `PolicyPartyRole` are the scoped roles;
  - `PartyRelationship` holds organization hierarchy and ownership.

  Gaps, detailed in the plan:
  - an ownership percentage on `PartyRelationship`;
  - a coverage-part qualifier on policy-term roles, so a role can cover one section of a package;
  - an acting-for organization (branch) on role contracts;
  - a uniqueness rule of one current account per insured organization per tenant, with source identifiers as aliases;
  - distinct first and additional named-insured role codes;
  - an authoritative-source marker on role assignments used for access.
- **nebula-insurance-crm.** The CRM already has a dated broker of record (`Account.BrokerOfRecordId` with relationship history), a per-policy broker and one account per policy. It lacks parent accounts, ownership, account-to-organization links, broker branches as organizations (ADR-026 uses distribution nodes) and per-account or per-policy contact assignments. Its broker users reach their whole broker tenant (ADR-007), wider than section 5 allows. Its `Program` is an MGA program, not an insured's program. The Brain does not change CRM contracts.

## Consequences

- **Glossary.** The glossary's Account definition becomes one organization's customer relationship, and the open decision in section 4.8 closes.
- **Cedar Bridge example.** It is re-expressed as:
  - one account each for Holdings, Workshop, Contracting and the joint-venture partner;
  - designated parent accounts;
  - a 60/40 joint venture;
  - a broker branch with a contact person;
  - a broker of record and a broker contact per account;
  - a second placement broker for the auto line;
  - one owning account per policy, with an additional named insured;
  - a small property program with a master policy and a local policy per subsidiary;
  - broker contacts scoped to an account and to a single policy;
  - per-line carrier underwriters, and a property underwriter narrowed to the BOP's property section.
- **Downstream features:**
  - F0012 adds these classes and properties to the foundation module;
  - F0017 resolves account and organization identity separately;
  - F0023 roots Entity 360 on one account with a hierarchy roll-up.
- **Authorization.** F0002 is archived, so the role-based reach and decision rights in section 5 need an F0002-successor scope amendment; nothing here changes delivered behavior.
- **Data model.** The proposed records are listed in [data-model.md](../data-model.md#proposed-party-account-and-role-records-adr-0070).

## Proof gates

Before acceptance:

1. F0012 Phase B authors these classes and properties with `temporal_kind`, definitions and regression cases (ADR-0063, ADR-0064).
2. The Cedar Bridge cases EX-PC-001, EX-PC-011 and EX-PC-015 to EX-PC-021 pass the `semantic_examples` and `semantic_rdf` gates, with exact expected rows and forbidden rows for every query, plus regression tests for missing/expired insured roles and closed-account replacement at explicit valid/known coordinates.
3. F0017 states how account identity and organization identity resolve and merge.
4. The role-based reach and decision rights in section 5 (cases EX-PC-018 and EX-PC-019) are accepted in an F0002-successor scope amendment, or replaced there, with security review of the authoritative-source rule. That amendment needs a tracked feature identifier and dependencies. Its acceptance criteria bind confirmation to the exact role version and cover expiry, historical reads, renewal terms, and evidence that spans accounts.

## References

- [BLUEPRINT section 4.8](../../BLUEPRINT.md#48-open-decisions)
- [Cedar Bridge walkthrough](../../examples/commercial-pc-account/README.md) and [cases](../../examples/commercial-pc-account/cases.md)
- [Commercial P&C handoff](../commercial-pc-example-handoff.md)
- `nebula-insurance-data-contracts/references/patterns/pc/account-pattern.md` and `party-role-pattern.md`
- `nebula-insurance-crm/planning-mds/architecture/decisions/ADR-026-broker-mga-hierarchy-producer-ownership-and-territory.md`
