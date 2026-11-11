# F0007 delivery follow-up — 2026-11-10-d49d1afa

Validation and delivery follow-up to plan review `2026-11-10-47612099` and feature review `2026-11-10-86ee5ef7`. This base validation run preserves the approved remediation run `2026-11-09-81798e61` and its immutable historical reports. It does not replace the feature's latest-run pointer.

The prior feature completion verdict described a local working tree. FR-H1 correctly identifies that source delivery is a separate requirement: F0007 must not be treated as delivered to dependent features until the remediation is committed, CI passes, and the PR merges to main.

## Changes and finding dispositions

- FR-H1: delivery pending. The contributor branch contains all earlier repairs and their evidence, including migration 0013. Commit, PR, CI, and merge evidence will be recorded separately; local tests alone do not close this finding.
- FR-L1: resolved. Removed the unused FactAnswerReader.scope_read_keys method. The existing unit test now exercises scope_keys_for_value with the selected payload while the store holds a different scope. HTTP and service authorization still derive permissions from the returned payload in one unit of work.
- PR-L1: resolved. Story S0002 AC3 explicitly requires the PRESENT value to match the immutable canonical member key, rejects MEMBER_VALUE_MISMATCH with zero writes, and accepts equivalent spellings.
- PR-M1: rules folded into ADR-0077 decisions D4, D5, D7 and D8. The current proof run and the reason for retaining Proposed status are explicit. Formal ADR acceptance remains an operator decision before F0008 Phase B. ADR-0039/0066 retain their broader independent acceptance gates.

## Verification

- Container-based combined domain, factslots, security and CI F0007 PostgreSQL selection: 369 passed, zero skips; brain_factslots coverage 98.60% (429 statements, 6 missed). See artifacts/tests.xml and artifacts/tests-final-retry.txt.
- Ruff check and format: clean (189 files). Mypy: clean (98 sources).
- Knowledge graph projections regenerated from sources; symbol index regenerated after removing the helper. Reproducibility, trackers, selected-run closeout evidence and framework template validation pass. The pre-existing commands-log absolute-cwd advisory is retained.
- Independent incremental Code Reviewer found no blocking implementation findings and ran the selected-payload unit regression. Independent PM/Architect review confirmed the operative ADR rules, AC3 and preserved operator acceptance boundary; its two wording clarifications were applied.
- Earlier comprehensive engine (868 passed), affected Neuron (27 passed), security and authorization-race proofs remain in the approved remediation run. They are historical evidence; the current cleanup is covered by this run and forthcoming PR CI.

## Evidence index

- action-context.md — scope and inputs.
- artifact-trace.md — raw sources, changes, environment.
- commands.log — exact invocations and exit codes, including initial Docker sandbox denials and successful escalated retries.
- artifacts/ — raw test, static, graph and lifecycle validation outputs.
- gate-decisions.md — validation decision and delivery boundary.
