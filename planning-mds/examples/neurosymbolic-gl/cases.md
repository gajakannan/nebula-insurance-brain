# EX-GL-001 challenge cases

**Status:** Independently authored expected behavior for synthetic variations; no cases below claim observed runtime execution. The main timeline records are in [records.json](records.json). Variations isolate one changed condition unless stated otherwise.

| Case | Given / when | Expected outcome or error | Owner |
|---|---|---|---|
| CASE-01 | Accepted each-occurrence USD 500,000; minimum USD 1,000,000 | BELOW_GUIDELINE, exact input/rule/evidence links | F0065 S0002/S0003; F0024 |
| CASE-02 | Accepted amount equals USD 1,000,000 | MEETS_GUIDELINE; equality is included | F0065 S0002 |
| CASE-03 | Amount USD 999,999.99, then USD 1,000,000.01 | BELOW_GUIDELINE, then MEETS_GUIDELINE; exact decimal comparison | F0065 S0002 |
| CASE-04 | Required amount/qualifier missing or page extraction failed | UNKNOWN; no zero value, explicit negative, or guessed comparison | F0065 S0002; F0006 |
| CASE-05 | Wrong USD 5,000,000 extraction at illustrative confidence 0.99, corrected against USD 500,000 source | Corrected assertion plus review/commit lineage; assessment uses accepted USD 500,000, BELOW_GUIDELINE | F0022/F0024; F0065 S0003 |
| CASE-06 | High-confidence assertion exists but no canonical acceptance | UNKNOWN; confidence grants no commit authority | F0018; F0065 S0002 |
| CASE-07 | Authorized source explicitly states applicable coverage absent, accepted with evidence | NOT_APPLICABLE with supported reason; differs from unknown coverage presence | F0006; F0065 S0002 |
| CASE-08 | Relevant unresolved conflict between source values | CONFLICT; no highest-confidence/newest-source shortcut | F0018; F0065 S0002 |
| CASE-09 | An aggregate canonical limit is deliberately passed at the internal evaluator boundary for an each-occurrence rule | NOT_APPLICABLE for the mismatched input; a public subject lookup with no each-occurrence value is UNKNOWN. Clients never supply arbitrary fact values. | F0007/F0013; F0065 S0002 |
| CASE-10 | EUR amount supplied for a USD guideline | NOT_APPLICABLE; no implicit conversion | F0065 S0002 |
| CASE-11 | July 5 assessed as known July 8 versus July 11 | BELOW_GUIDELINE on EX-F-001, then MEETS_GUIDELINE on EX-F-003 | F0025; F0065 S0004 |
| CASE-12 | June 30 assessed as known July 11 | BELOW_GUIDELINE on EX-F-002; unaffected valid interval preserved | F0025; F0065 S0004 |
| CASE-13 | Accepted fact retracted without replacement | New current assessment UNKNOWN; prior assessment remains historical | F0010; F0065 S0004 |
| CASE-14 | Concurrent canonical commit during assessment | One consistent snapshot; no mixed input versions | F0065 S0003/S0004 |
| CASE-15 | New guideline minimum USD 3,000,000 released July 12; current July 13 on USD 2,000,000 | BELOW_GUIDELINE under v2; historical v1 result unchanged; requesting v2 as known July 11 is an error | F0065 S0001/S0004 |
| CASE-16 | `forall x: ValidPolicy(x) -> Approved(x)` or unsupported operator submitted as executable rule | Definition rejected; no approval inference or assessment success | F0065 S0001 |
| CASE-17 | Duplicate save with identical idempotency key/request/snapshot; then changed request | One assessment/audit effect for duplicate; changed-content reuse rejected | F0065 S0003 |
| CASE-18 | Result evidence permission revoked; policy entity remains visible | Access error; no protected result/title/count/explanation/history/citation or revealing gap reason | F0065 S0005; F0026 |
| CASE-19 | Forged tenant, principal, or rule-authority fields; cross-tenant assessment ID | Denied under verified current grants; no record existence leak | F0002/F0018; F0065 S0003/S0005 |

F0026 maps every case to runtime evidence and adds an independent holdout with sample sizes and measured extraction quality. Cases 01–03 check the evaluator independently of neural extraction; F0024 must also exercise actual model interpretation through governed acceptance to CASE-01. A hand-authored expected record or a mocked model alone cannot satisfy that end-to-end gate.
