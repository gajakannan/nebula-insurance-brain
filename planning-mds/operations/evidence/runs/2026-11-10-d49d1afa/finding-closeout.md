# F0007 follow-up finding disposition

Current source commit: `4c4e37ec92c602e9eb9584bf0aa1b9634ec6625e`. Delivery PR: [#44](https://github.com/gajakannan/nebula-insurance-brain/pull/44). All PR CI jobs passed, including the expanded PostgreSQL suite. The operator subsequently instructed: "dont do the pr merge yet... finish the rest of the findings". The PR remains open and unmerged; no mainline delivery is claimed.

| Finding | Disposition | Evidence |
|---|---|---|
| FR-H1 | Commit, push, PR and CI complete; merge intentionally held by operator | Commit `4c4e37e`; PR #44; CI run `42948384156`; graph reproducibility run `42948384070` |
| FR-L1 | Resolved | Removed `FactAnswerReader.scope_read_keys`; no current source, plan or generated-symbol references remain. The replacement regression passes a selected payload whose scope differs from the store's current answer. |
| PR-L1 | Resolved | S0002 AC3 explicitly requires canonical member-key agreement, `MEMBER_VALUE_MISMATCH` with zero writes, and accepted equivalent spellings. All six stories validate. |
| PR-M1 | Operative rules and broader-ADR deferral rationale complete; ADR-0077 formal decision pending | ADR-0077 D4/D5/D7/D8; ADR-0039/0066 status sections identify unfulfilled broader proofs and owners; `adr-acceptance-proposal.md` maps all five ADR-0077 proof gates to passing tests. |

The earlier remediation and review reports are retained as historical snapshots. This record distinguishes source correctness, formal ADR acceptance, and delivery to main so that a local or branch-only Done verdict cannot be mistaken for merged delivery.
