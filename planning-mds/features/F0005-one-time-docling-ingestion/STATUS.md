# F0005 — One-time document ingestion — Status

**Overall Status:** Candidate implementation in progress; production delivery incomplete. ADR-0060 is Proposed. The exact pin and six contract tests are recorded in [compatibility evidence](compatibility-evidence.md). No live-model acceptance, runtime activation, or reviewer signoff claimed.
**Last Updated:** 2026-09-17

## Story Checklist

| Story | Title | Status |
|---|---|---|
| [F0005-S0001](F0005-S0001-pin-and-process-source-documents.md) | Pin and process source documents | In Progress |
| [F0005-S0002](F0005-S0002-persist-artifacts-and-recover-jobs.md) | Persist artifacts and recover jobs | In Progress |
| [F0005-S0003](F0005-S0003-reinterpret-saved-json-and-map-evidence.md) | Reinterpret saved JSON and map evidence | In Progress |
| [F0005-S0004](F0005-S0004-evaluate-and-activate-proven-pipeline.md) | Evaluate and activate the proven pipeline | Not Started |

## Recommendation Audit

| Recommendation | Planning state | Delivery / proof still required |
|---|---|---|
| New orchestration ADR | ADR-0060 Proposed; acceptance gates explicit | Complete all four proof gates and obtain actual reviewer verdicts |
| Existing ADR invariants | Dated links preserve ADR-0003/0004/0040/0055/0058/0059 and F0001 results | Demonstrate compatibility with those contracts |
| Consistent blueprints, C4, article | Proposed target distinguished from current runtime | Update actual runtime descriptions after activation |
| Artifact and run identity | F0004/F0016 specify separate parser/pipeline/recipe/profile metadata and run-owned provenance | Versioned DTO/schema changes and persistence |
| F0004/F0005 feature planning | Neutral F0005 title; four stories; F0004 dependency explicit | S0001–S0004 execution |
| Profiles and interpretation | F0014/F0015/F0016 scope updated | Compiler and production run service implementation |
| Targeted evolution | F0032 now owns affected-content-only scheduling proof | Demonstrate bounded input, original refs, zero reparse |
| Review and release | F0022/F0026 evidence and failure/quality cases specified | Panel mapping and measured corpus results |
| Runtime, dependency lock, misleading adapter name | Candidate adapter, shared ParseResult, explicit direct baseline, pyproject/uv.lock pin, package/schema/input metadata implemented and tested | Production composition, model/run metadata, evidence translation, durable services, activation |
| Full-document versus chunked extraction | F0001 one-call baseline retained; candidate tests use direct mode | Comparative schema/quality/cost/latency/review results |
| Local inference and operations | Secrets, bounded concurrency, tenant access/retention included | Observed failure/security/resource tests |
| Temporal and archive | v0.1 jobs / v0.3 Temporal retained; F0001 unchanged | No architecture replacement or reopened archive required |

## Proof Gates

- [ ] Exact-version native/scanned conversion, checkpoint, restart, and saved-JSON reuse.
- [ ] Insurer-critical property/relationship evidence, table and multi-region cases.
- [ ] Corpus comparison and timeout/partial/invalid-output/retry/restart cases.
- [ ] Local vLLM, secrets, concurrency, tenant access, and retention.

## Required Signoff Roles

Architecture reviews the checkpoint and invariants; QA reviews independent results; security reviews boundaries and resource/retention controls; code review covers runtime integration. Named reviewers and their actual verdicts remain pending.

## Story Signoff Provenance

| Story | Role | Reviewer | Verdict | Evidence | Date | Notes |
|---|---|---|---|---|---|---|

No verdicts recorded. Planning checks do not satisfy any proof gate.
