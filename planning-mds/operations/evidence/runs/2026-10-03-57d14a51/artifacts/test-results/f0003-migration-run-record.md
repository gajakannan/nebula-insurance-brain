# F0003 Migration Run Record

- Feature: F0003 — PostgreSQL persistence
- Run: 2026-10-03-57d14a51
- Database: disposable local PostgreSQL database `brain_f0003_g2`
- Operator account: `gajap` (local OS account for the shell session that supplied the migration output; `id -un` returned `gajap`)
- Timestamp source: `commands.log`, recorded in ISO 8601 with the local UTC offset

| Attempt | Timestamp | Revision / operation | Outcome |
|---|---|---|---|
| 1 | 2026-10-04T22:20:06-04:00 | Alembic `upgrade head`; stopped at revision `0003` | Failed with exit code 1 because `btree_gist` was not installed in this database. |
| 2 | 2026-10-04T22:20:06-04:00 | Alembic `upgrade head`; applied revisions `0001` through `0007` | Passed with exit code 0 after the database-local extension was installed. Final revision: `0007`. |

The operator-supplied terminal output records PostgreSQL transactional DDL and the successful upgrade through `0007`. The command timestamps and exit codes are retained in `commands.log`; the database name and migration result are corroborated by the PostgreSQL test evidence. Passwords are redacted from the command log.
