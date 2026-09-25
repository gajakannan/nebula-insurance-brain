# F0002 personas

These are scoped uses of existing product personas, not newly invented job roles or permissions.

| Persona | Priority | Job in F0002 | Success / boundary |
|---|---|---|---|
| [Dana the Platform Engineer](../../examples/personas/platform-engineer.md) | Primary | Verify identity, provision trusted grants and reproduce scope/delegation/audit decisions | Invalid credentials never select protected records; current-grant and delegation cases have zero unauthorized results |
| [Ingrid the Persistence Engineer](../../examples/personas/persistence-engineer.md) | Primary | Preserve ownership and stable identity across records and migration | No cross-tenant/KB parent association; existing identifiers retained; failed writes leave no partial ownership |
| [Rosa the Business Reviewer](../../examples/personas/business-reviewer.md) | Secondary | Annotate only authorized review evidence under current grants | A review annotation never confers canonical business approval; changed authority blocks submission |

## Jobs-to-be-Done

- When a protected operation arrives, Dana wants trusted identity and current scope so every consumer uses the same access boundary.
- When a semantic record references a parent, Ingrid wants structural ownership checked so the relationship cannot bypass tenancy.
- When evidence access changes during review, Rosa wants submission to respect the new grants so she cannot unknowingly act with revoked authority.

## Anti-personas and constraints

External brokers/MGAs and new business administrators are out of this pilot. Engineering responsibility is not an authorization role. Existing profile background, motivations and working context remain authoritative at the linked persona files.
