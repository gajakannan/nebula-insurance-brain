# AI Engineer Compatibility Self-Review — F0006

- Run: `2026-11-02-5a00b0ff`
- Product root: `/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain`
- Role: AI Engineer
- Reviewer: Codex (`assertion_core`), implementation self-review
- Reviewed on: 2026-11-02
- Result: **PASS**
- Scope: the approved assembly plan's shared DTO, existing result importer and Neuron compatibility handoff. Independent G3 review remains a separate gate.

## Findings

No blocking compatibility finding in this scoped review.

1. `engine/packages/brain-contracts/src/brain_contracts/result.py` and the legacy planning schema are unchanged. New adapters live in `assertions.py` and `dispatch.py`, with packaged local schemas. The default `DocumentResultImporter.run_one` calls `parse_legacy_result` after authorized source loading and before artifact/run/assertion/evidence/review insertion or delivery acknowledgement. An explicit v2 or other unsupported discriminator raises the stable compatibility error instead of stripping new fields or falling back to v1.
2. The strict dispatch tests exercise absent-version legacy results, exact integer v2 dispatch, refusal by the legacy reader, and unsupported explicit null/boolean/string/numeric versions. Legacy schema/Pydantic absence of `provenance_ledger_ref` remains an explicit existing boundary: the new reader does not fill it or reconstruct historical provenance. The test asserts both unchanged successful legacy parsing and refusal of that missing member.
3. `neuron/uv.lock` adds the internal `brain-assertions` package and its shared-package dependency edges. Comparing all external package versions and sources to HEAD yields an empty delta; the full lock diff contains only those internal additions. `neuron/` has no source or prompt change in this feature.
4. `config/local.yaml` is unchanged: `extraction.pipeline: direct-baseline` and `content.v2_writer_enabled: false`. The new v2 application seam does not register a live producer, enable an extraction pipeline, add model calls, or change the existing worker's authorization/import transaction. Durable drop adoption and run lifecycle remain the approved F0016 handoff.

## Executed Evidence Reviewed

These are completed application-container results recorded by the implementation/QE work; this self-review did not rerun them.

| Evidence | Observed result | Compatibility implication |
|---|---|---|
| `artifacts/test-results/g2-complete-assertions.xml` | 141 passed; 0 failures/errors/skips | Includes strict schema/JSON/version dispatch, admission, PostgreSQL persistence and current-consumer safeguards. Contract tests assert legacy parsing and explicit v2 refusal. |
| `artifacts/test-results/g2-neuron-recovery.xml` | 5 passed; 5 PostgreSQL cases skipped in the first invocation | SQLite worker/importer process-crash and replay scenarios pass; this artifact alone does not establish PostgreSQL recovery. |
| `artifacts/test-results/g2-neuron-postgres-second.xml` | 5 passed; 0 failures/errors/skips | The separate configured PostgreSQL invocation passes recovery at bundle publication, run publication, completion, import and imported boundaries. |

The recovery suite uses synthetic stored content and recorded model responses. Its PostgreSQL cases use isolated schemas and prove the existing importer/replay boundary. They are not live-model qualification or permission to activate a new producer.

## Source Trace

- Approved scope and handoff: `planning-mds/features/F0006-assertion-plane-origin-and-interpretation-basis/feature-assembly-plan.md`, Build Order / Wire Contracts and Dispatch.
- Existing consumer: `engine/apps/worker/src/brain_worker/document_delivery.py`, `DocumentResultImporter.run_one`.
- Version seam: `engine/packages/brain-contracts/src/brain_contracts/dispatch.py` and `assertions.py`.
- Contract expectations: `engine/packages/brain-assertions/tests/test_contracts.py`.
- Recovery expectations: `neuron/tests/integration/test_document_process_recovery.py`.
- Default-selection configuration: `config/local.yaml`; dependency resolution: `neuron/uv.lock`.

The command log records the source diff, external-lock comparison and direct JUnit summaries used for this verdict. This report grants no feature approval or production activation.
