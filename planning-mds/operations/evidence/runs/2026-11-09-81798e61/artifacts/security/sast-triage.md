# SAST disposition — F0007 remediation

Reviewer: Codex / independent Security Reviewer. Date: 2026-11-10.
Raw artifact: `artifacts/security/sast.sarif`; review extraction: `artifacts/security-review-raw-scans.txt`.

The scanner emitted exactly two results for `python.sqlalchemy.security.audit.avoid-sqlalchemy-text.avoid-sqlalchemy-text`, at `engine/migrations/versions/0013_f0007_identity_guard.py:70` and `:73`.

**Disposition for both results: false positive, no request-controlled SQL input.**

- Both SQL strings interpolate only the local variable `invalid`.
- `invalid` is defined at line69 as a fixed suffix around module constant `IDENTITY_SHAPE`.
- `IDENTITY_SHAPE` is a literal SQL identity predicate frozen in the migration source (lines43–61). It contains no request, environment, database value or command-line interpolation.
- The statement at line70 counts existing rows matching that fixed predicate; line73 returns at most10 sorted slot IDs for an operator refusal message. Returned values do not become SQL text.
- A table lock is held during inventory and constraint replacement. Any malformed rows abort upgrade rather than triggering deletion or automated repair.

The rule's message itself states its SQL-injection concern is conditional on user input reaching `text()`. No such input route exists here. Using static SQL for an immutable PostgreSQL migration is consistent with this repository's migration pattern. No inline suppression was added and the raw scanner output remains unchanged.

This is not a risk waiver or deferred recommendation. Preserve the manifest SAST result as `findings` to describe the raw scanner result, with this artifact as the accountable Security disposition. There are zero actionable security findings from these two results.
