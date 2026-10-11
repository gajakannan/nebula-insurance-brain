# Account model: data-contracts and CRM alignment plan

**Status:** Plan, 2026-10-10. The operator carries it out in the two repositories, separately from this one. The Brain changes no contract or code outside its own repository.
**Source of truth:** [ADR-0070](decisions/ADR-0070-account-party-and-role-model.md) (Proposed) and the [Cedar Bridge example](../examples/commercial-pc-account/README.md), cases EX-PC-015 to EX-PC-019.
**Read at:** `nebula-insurance-data-contracts` 8b11f9b and `nebula-insurance-crm` b9775b2. Re-check file paths and field names before acting on them.

## What the model needs from each system

| ADR-0070 rule | Data contracts today | CRM today |
|---|---|---|
| One current account per insured organization per tenant; other systems' IDs are aliases | `Account.primary_party_uid` required; no uniqueness rule | `Account` has its own name and tax ID; no party link |
| At most one designated parent account | `Account.parent_account_uid`, plus typed `AccountRelationship` | No parent account |
| Ownership with any number of percentage owners | `PartyRelationship` has types but no percentage | None |
| Brokers are organizations with branches, offices and people | `Party` and `PartyRelationship` can express it; no branch or employment codes listed | `Broker` entity, MGA link and distribution nodes (ADR-026); branches are not organizations |
| Dated broker of record per account | `AccountPartyRole` with effective and expiration dates | `Account.BrokerOfRecordId`, with changes in `AccountRelationshipHistory` |
| Per-line placement broker | `PolicyPartyRole` scoped to `policy_term_uid` | `Policy.BrokerId` |
| Broker contacts per account and per policy | Role contracts carry a party but not the organization a person acts for | `Contact` has one `BrokerId` and one `AccountId`; no per-account or per-policy assignment |
| A policy belongs to exactly one account | `Policy.account_uid` | `Policy.AccountId` |
| First named insured, additional named insured and additional insured are distinct | Codes not confirmed | Not modeled |
| A policy-term role can be narrowed to coverage parts (a package section) | No coverage qualifier on `PolicyPartyRole` | No per-coverage roles |
| Program under the parent account; policies link to it | `Agreement` (`MASTER_PROGRAM`) with `account_uid`; `Policy.agreement_uid` | `Program` means an MGA program, not an insured's program |
| External reach follows confirmed role scope; carrier staff act by role | No marker for a confirmed role | Broker users see their whole broker tenant (ADR-007, `broker_tenant_id`) |

## nebula-insurance-data-contracts

The contracts already match most of the model. The work adds fields, codes and rules, in this order:

1. **Ownership** (`references/odcs/pc/core/party-relationship.odcs.yaml`).
   - Add `ownership_percent`: a decimal greater than 0 and at most 100, required when the relationship type is an ownership type.
   - Add a quality rule that current percentages for one owned party sum to at most 100.
2. **Relationship codes** (`reference-data/relationship-type-code.odcs.yaml`): add or confirm ownership, branch or office of, and employed by. Organization hierarchy and employment then use `PartyRelationship`.
3. **One account per organization** (`core/account.odcs.yaml`).
   - Add a rule: one current account per `primary_party_uid` within a tenant, whichever source system recorded it. Source-system account identifiers are aliases on that account, not separate accounts.
   - A closed account keeps its history and does not count toward the rule. A merge closes the losing account and moves its aliases to the survivor.
   - State that `parent_account_uid` is the single designated parent, that it never forms a cycle, and that `AccountRelationship` types never replace it.
4. **Programs.**
   - `Agreement` with `MASTER_PROGRAM` already matches EX-PC-019. Document that `Agreement.account_uid` is the parent account and that master and local policies each keep their own `Policy.account_uid`.
   - Decide whether `AccountTypeCode` `MASTER_PROGRAM` and `AccountRelationshipTypeCode` `MASTER_PROGRAM` stay. Both treat a program as an account, which ADR-0070 does not.
5. **Acting-for organization and coverage qualifier.**
   - Add `acting_for_party_uid` to `AccountPartyRole`, `PolicyPartyRole` and `SubmissionPartyRole`. It records the organization or branch a person represents in the role.
   - Add an optional coverage-part qualifier to `PolicyPartyRole` (for example, a list of coverage or coverage-part identifiers of the same term). Without it, the role covers the whole term.
6. **Confirmed roles.** Add two fields to the same three role contracts:
   - `role_source_code`, with values such as broker-of-record letter, carrier operations or document extraction;
   - `confirmed_datetime`.

   Access may use only confirmed roles (ADR-0070 section 5).
7. **Role codes** (`reference-data/party-role-type-code.odcs.yaml`).
   - Add any of these that are missing: `CARRIER`, `MANAGING_GENERAL_AGENT`, `BROKER_OF_RECORD`, `PLACEMENT_BROKER`, `BROKER_CONTACT`, `RISK_MANAGER`, `ACCOUNT_CONTACT`, `ORGANIZATION_CONTACT`, `FIRST_NAMED_INSURED`, `ADDITIONAL_NAMED_INSURED`, `ADDITIONAL_INSURED`, `UNDERWRITER`, `UNDERWRITING_ASSISTANT`, `DISTRIBUTION_CONTACT`, `MARKETING_REPRESENTATIVE` and `OPERATIONS_CONTACT`.
   - Document that `ADDITIONAL_INSURED` is a third party with narrower rights, not a named insured, and that `FIRST_NAMED_INSURED` and `ADDITIONAL_NAMED_INSURED` are recorded, never derived from `Policy.account_uid`.
   - The Cedar Bridge mapping from role kinds to these codes is in `examples/commercial-pc-account/projection-mapping.yaml` (`role_kind_codes`).
8. **Patterns and targets.**
   - Update `references/patterns/pc/account-pattern.md` and `party-role-pattern.md` with the rules above.
   - Regenerate the Fabric manifests and DDL under `targets/fabric/` for every changed contract, and add a `CHANGELOG.md` entry.

**Done when:** the repository's own contract validation passes, and the Cedar Bridge records can be mapped field by field onto the changed contracts with nothing left over.

## nebula-insurance-crm

The CRM already has a dated broker of record, a per-policy broker and one account per policy. The work brings in the hierarchy and the people. Each step should be its own feature or story with a PRD, so the CRM's planning and gates apply.

1. **Account to organization.** Link each `Account` to one organization party. Enforce one active account per insured organization per tenant; identifiers from other systems are aliases. Account merge (ADR-017) keeps this rule.
2. **Parent account.** Add one optional designated parent account, with self-parent and multi-level cycle prevention, effective dating in `AccountRelationshipHistory`, and a hierarchy roll-up view.
3. **Ownership.** Record owners with percentages, any number per organization, apart from the parent account. Current percentages total at most 100; less is allowed. Show them on the account as ownership interests outside the roll-up, and show the designated parent as recorded, even when it is a minority owner.
4. **Brokers as organizations.**
   - Reconcile ADR-026's distribution nodes with branches and offices as organizations under the broker, each with locations and employed people.
   - Decide whether distribution nodes map onto broker organizations or remain a separate sales-territory structure.
5. **Broker contacts as role assignments.**
   - Replace the single `Contact.BrokerId` and `Contact.AccountId` with role assignments. Each assignment has a person, a role kind, a scope (account, policy term or submission), the organization acted for, and dates.
   - `AccountContact` becomes the insured-side contact roles on the same model.
6. **Named insureds.**
   - Add policy-level named-insured roles: first named insured, then additional named insureds.
   - Keep additional insured as a separate role kind.
   - `Policy.AccountId` stays the owning account, normally the first named insured's.
7. **Programs.**
   - Rename or document the existing MGA `Program` so it is not confused with an insured's master program.
   - Add the insured's program as an agreement owned by the parent account, with the policies linked to it.
8. **External access.**
   - ADR-007 lets a broker user reach their whole broker tenant. ADR-0070 limits each broker contact to the accounts and policies their roles name, with no cascade to parent, sibling or program.
   - Amend ADR-007 and the F0029 external portal plan. Only confirmed roles count, and ending a role revokes access at once.
9. **Internal decision rights.** Internal users keep broad read access. Underwriting and other decisions on a policy, submission or account need a matching role, enforced next to the existing Casbin policy (ADR-008). On a package policy, a role narrowed to one section decides only that section.

**Done when:**
- CRM tests cover each EX-PC-018 reach and decision-rights row, including the forbidden rows in `expected-results.yaml`;
- a broker contact on the parent account cannot open a child account;
- a policy-only contact cannot open the account behind the policy;
- an ended role loses access on the next request.

## Order and dependencies

1. **Data contracts first.** The CRM and the Brain both map onto them.
2. **CRM steps 1 to 3 and 5 to 6** are the data model. They can follow as each contract lands.
3. **CRM steps 8 and 9 wait** for the F0002-successor access amendment in this repository, so all three systems enforce one reach rule.
4. **In this repository:** F0012 Phase B authors the vocabulary, and the F0002-successor amendment takes up ADR-0070 section 5. When a contract changes, update the Cross-repository alignment section of ADR-0070.
