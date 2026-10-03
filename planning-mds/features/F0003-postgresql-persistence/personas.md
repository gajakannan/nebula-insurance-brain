# F0003 personas

F0003 reuses an established engineering persona; it introduces no new business role.

| Persona | Priority | Job in F0003 | Success / boundary |
|---|---|---|---|
| [Ingrid the Persistence Engineer](../../examples/personas/persistence-engineer.md) | Primary | Keep the relational model, migration history, and database-enforced invariants reliable as feature-owned records are added | Existing identifiers and history survive migrations; owner and temporal constraints reject invalid state; PostgreSQL-only behavior is proven on PostgreSQL |

The engineering persona is not an authorization role. End users do not connect directly to the database.
