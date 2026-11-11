# Independent Code Reviewer notes — F0007 remediation

Reviewer: Codex `/root/remediation_code_review`, 2026-11-10. No implementation files were edited by this reviewer. Raw source/test and schema/contract inspection, not implementer summaries, determined the result.

No additional correctness finding was established. Main checks:

- `fact_values.py:163` through169 calculates complete canonical size, including sign; the `<1` expansion formula `2 - exponent` is correct for its branch. Zero returns canonical `0`; accepted output remains a valid <=64-character input. No Decimal precision context is used.
- `answers.py:102` through110 enforces member equality only for PRESENT values and MEMBER rows after existing evidence/entity-owner checks. It reuses the exact resolver domain key rule and leaves SINGLE rename behavior unchanged.
- `execution.py:356` through419 authorizes the primary before private load, derives scope from the returned object, authorizes/rechecks dependencies in the same store transaction, audits every decision and commits once. Discovery failure cannot release payload; denial re-audits primary as FAILED with the denied scope. Existing callers without callback retain prior semantics.
- HTTP uses the actual `FactVersion.value` rather than a separately reselected answer. Legacy slot JSON bypass remains explicit. The internal reader derives scope from the typed returned answer.
- `0013` freezes the previous CHECK for rollback, locks before inventory, rejects anything not TRUE under the strict complete expression, and replaces it atomically. It never rewrites prior identities, versions or0012 history. Direct-SQL tests exercise the original NULL loopholes and every mandatory field.
- Exact raw combined evidence:319pass/0fail/0skip; selected-scope line coverage2176/2263=96.1555%. Final raw full-engine JUnit confirms868pass/0fail/0skip after the missing Docker CLI runtime dependency was restored. The initial execution remains a recorded environment failure. Final Ruff checks189 files and mypy checks72 source files successfully.

Final routing refresh was checked: authored bindings include new0013 and regression tests; helper symbols/WHY regeneration and validation pass. Existing F0006 dangling-symbol warnings remain visible. Integration owner-concentration acknowledgement is a routing reminder; score3 is routine. No speculative duplicate helper, missing implementation site, or new broad dependency was found.

The report `../code-review-report.md` records the implementation approval and explicitly separates that verdict from the final lifecycle/evidence/deployability decisions. A later source change requires corresponding review refresh; coordinator artifact-only/format updates do not alter the inspected semantics.
