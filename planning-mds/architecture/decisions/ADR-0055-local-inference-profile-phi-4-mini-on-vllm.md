# ADR-0055: Local Inference Profile — Phi-4-mini-instruct on vLLM

## Status

- [ ] Proposed
- [x] Accepted
- [ ] Superseded
- [ ] Rejected

**Date:** 2026-09-06
**Deciders:** Operator (F0001 clarification gate G1), Architect (F0001 Phase B)
**Source:** F0001 plan run `2026-09-06-cdb5d8cb` gate-decisions G1; nebula-insurance-crm ADR-035 and `neuron/config/models.yaml` profile `local_phi`

## Context

The F0001 parse-once proof (S0003) drives Docling-Graph extraction through a language model. Master blueprint section 117.1 leaves the model provider and data policy open. The operator asked at the clarification gate that the Brain use the same local model the CRM validated. Verification of the CRM showed one validated local profile: `microsoft/Phi-4-mini-instruct` served by vLLM 0.25.1 as an OpenAI-compatible endpoint on the WSL2 host GPU with `--max-model-len 4096`, bearer auth, and secrets sourced outside the repository. Mistral is not used in the CRM; Ollama exists there only as an unwired seam.

## Decision Drivers

- No fixture or customer text leaves the machine during proofs; no data-policy dependency.
- Reuse the CRM's validated runbook, provenance pinning, and fail-closed conventions rather than a second local stack.
- Keep the model replaceable behind the OpenAI-compatible boundary (ADR-0001: engines around the semantic core).

## Decision

1. Model: `microsoft/Phi-4-mini-instruct`, pinned by Hugging Face revision in `docker/DEPENDENCY-MATRIX.md`.
2. Runtime: vLLM (version pinned in the matrix) serving the OpenAI-compatible API on the host GPU at `BRAIN_INFERENCE_BASE_URL`, started per `docker/local-inference-runbook.md` (adapted from the CRM runbook), with `--max-model-len 4096`, `--dtype auto`, `--gpu-memory-utilization 0.90`, and `--api-key` from a gitignored secrets file.
3. Client conventions (from ADR-035): the context limit is enforced client-side before every call so over-long requests fail closed rather than returning truncated output; every run records model id, revision, endpoint hash, prompt hash, schema hash, and token counts; the model receives chunk text only, never a user token, principal id, or tenant identifier; the server must not persist prompts; model self-reported confidence is a signal, not an authorization.
4. Adequacy is a recorded proof result, not an assumption: the CRM validated this model for short structured intent calls; S0003 measures whether 4,096 tokens hold Docling-Graph chunks plus the extraction schema and records the outcome in ADR-0040. If the model cannot produce schema-valid `InterpretationResult` output for the GL fixture, the Architect proposes an alternative backend at Phase B of F0005 rather than widening the proof.

## Options Considered

1. **Phi-4-mini-instruct on vLLM (chosen):** already validated in the sibling product; shared runbook and conventions.
2. **A larger open-weights model on the same vLLM runtime:** better context, but a second validation effort and more VRAM than the validated host has.
3. **Cloud API provider:** fastest setup, but requires a written data policy for fixture text and diverges from the CRM.

## Consequences

- Docling-Graph must be configured for an OpenAI-compatible backend; the adapter lives in `neuron/packages/brain-extraction`.
- CI without a GPU runs S0003 against recorded fixtures; the live proof runs on the developer host and its outputs are captured as evidence.
- Extraction quality and context adequacy for insurance documents remain open until S0003 reports; the decision is about runtime and policy, not about extraction accuracy.

## Security & Compliance Notes

- The inference key lives in `~/.brain-secrets` (0600) or CI secrets; never in the repository.
- No PII or credentials in prompts; prompts are not persisted by the server; token counts and latency are the only telemetry retained.

## References

- nebula-insurance-crm: ADR-035, `neuron/config/models.yaml` (`local_phi`), `neuron/neuron-local-phi-vllm-wsl2-runbook.md`
- F0001 stories S0002 and S0003; proposed ADR-0040

## Refinement — 2026-09-15

[ADR-0060](ADR-0060-docling-graph-document-pipeline-orchestration.md) proposes Docling-Graph document pipeline orchestration. The model/provider policy continues to apply through Docling-Graph. F0001 actually executed the direct-vLLM adapter, despite the original plan naming Docling-Graph. F0005 must revalidate context adequacy, structured output, and per-call guards for the new templates and any multi-call extraction strategy.
