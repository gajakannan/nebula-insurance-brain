# PM Closeout — F0001-repository-and-engineering-foundation run 2026-09-08-b5af1e54

**Date:** 2026-09-10
**PM:** Product Manager (feature-action closeout)

## Final Story Status

| Story | Final Status | Evidence | Notes |
|-------|--------------|----------|-------|
| F0001-S0001 | Done | test-execution-report.md / code-review-report.md | Runtime roots and toolchain skeleton |
| F0001-S0002 | Done | test-execution-report.md / code-review-report.md | Local runtime containers and dependency matrix |
| F0001-S0003 | Done | test-execution-report.md / code-review-report.md | Parse once, reinterpret twice, evidence resolves — ADR-0040 accepted |
| F0001-S0004 | Done | test-execution-report.md / code-review-report.md | Native review round trip — ADR-0044 accepted, ADR-0058 accepted as amended |
| F0001-S0005 | Done | test-execution-report.md / code-review-report.md | Bitemporal commit — ADR-0041 accepted |
| F0001-S0006 | Done | test-execution-report.md / security-review-report.md | Access boundaries, extension build, restore — ADR-0049/ADR-0050 accepted |
| F0001-S0007 | Done | code-review-report.md / all six ADR files | Proof outcomes recorded, contracts settled |

## Archive Decision

**Done — not archived.** F0001 is the foundation every subsequently planned feature (F0002–F0063, F0065) references by path and by ADR; archiving now would require repointing hand-authored cross-references across the planning tree for a feature whose content stays in continuous active use. This is a deliberate PM judgment call, documented identically in `STATUS.md`'s Archival note. `registry_section` stays `Active`; `status` moves to `done`; `roadmap_section` moves to `Completed` (`completed_date: 2026-09-10`).

## Deferred Follow-ups

Mirrors `STATUS.md`'s Deferred Non-Blocking Follow-ups table — each already carries an owner and a tracking link (F0002, F0015, F0021, or F0026). No additional PM-level deferrals beyond what implementation already recorded.

## Recommendation Acceptances

All findings below are `medium`/`low` severity (no `high`/`critical` findings exist in this run, so no `mitigation:`-prefixed acceptance is required).

- Accepted: `neuron/packages/brain-extraction/src/brain_extraction/docling_graph_adapter.py`'s live-only code paths (95 statements, 25% covered offline) have no offline-mockable unit test — coverage depends on a reachable vLLM endpoint at test time — owner: ai-engineer; follow-up: F0002. — deferred to F0002, tracked in `STATUS.md` and `code-review-report.md`.
- Accepted: The scanned/OCR fixture path in `neuron/tests/integration/test_parse_once_reinterpret.py` is exercised only by a manual, one-off check recorded in ADR-0040, not by an automated assertion — owner: ai-engineer; follow-up: F0002. — deferred to F0002.
- Accepted: `BRAIN_GRANT_CACHE_SECONDS` is documented (S0002 onward) but has no cache implementation behind it — `PrincipalResolver.memberships()` queries Postgres on every request. This is a deliberate, disclosed decision (see `STATUS.md` Deferred Non-Blocking Follow-ups and ADR-0049's Results), not an oversight, but flagged here so a future cache implementation is measured against the 12.41ms baseline already recorded rather than assumed necessary — owner: architect; follow-up: F0002/F0026 if load requires it. — accepted as residual; no cache is a deliberate scope decision, not a gap.
- Accepted: `engine/apps/api/routes/content.py`/`reviews.py`/`facts.py` have lower line coverage (73–87%) than the rest of the API layer, concentrated in infrastructure-failure exception branches — owner: quality-engineer; follow-up: F0021 or F0002, whichever adds broader negative-path API tests. — deferred.
- Accepted: No Playwright E2E coverage for the Review Panel yet (11 Vitest/Testing-Library component tests only) — already tracked in `STATUS.md`; owner: quality-engineer; follow-up: F0021. — deferred to F0021.
- Accepted: `neuron/pyproject.toml` has no `[tool.uv] exclude-newer` dependency cooldown — waived (see Scan Disposition) because the deliberately pinned `docling==2.126.0` was published inside any reasonable cooldown window. Reassess when `neuron/`'s pins age past 7 days — owner: ai-engineer; follow-up: F0002. — accepted as a documented, reasoned waiver (fixing it would break the deliberate `docling==2.126.0` pin).
- Accepted: ZAP's `Storable and Cacheable Content` warning on 404 responses — no data exposure (the API serves no static content); a global `Cache-Control: no-store` on error responses would silence it but is not required for this feature's scope — owner: backend-developer; follow-up: F0021 (whichever feature next touches `errors.py`'s response construction). — accepted as residual, informational severity only.
- Accepted: F0001-S0001 — Code Reviewer's `APPROVED WITH RECOMMENDATIONS` verdict for this story resolves to the medium/low findings accepted above; none blocking.
- Accepted: F0001-S0002 — Code Reviewer's `APPROVED WITH RECOMMENDATIONS` verdict for this story resolves to the medium/low findings accepted above; none blocking.
- Accepted: F0001-S0003 — Code Reviewer's `APPROVED WITH RECOMMENDATIONS` verdict for this story resolves to the medium/low findings accepted above; none blocking.
- Accepted: F0001-S0004 — Code Reviewer's `APPROVED WITH RECOMMENDATIONS` verdict for this story resolves to the medium/low findings accepted above; none blocking.
- Accepted: F0001-S0005 — Code Reviewer's `APPROVED WITH RECOMMENDATIONS` verdict for this story resolves to the medium/low findings accepted above; none blocking.
- Accepted: F0001-S0006 — Code Reviewer's `APPROVED WITH RECOMMENDATIONS` and Security Reviewer's `PASS WITH RECOMMENDATIONS` verdicts for this story both resolve to the medium/low findings accepted above; none blocking.
- Accepted: F0001-S0007 — Code Reviewer's `APPROVED WITH RECOMMENDATIONS` verdict for this story resolves to the medium/low findings accepted above; none blocking.

## Tracker Updates

`REGISTRY.md` (F0001 now shows `Done` in the Active table), `ROADMAP.md` (F0001 moved from "Now" to the "Completed" section), `STORY-INDEX.md` (regenerated via `generate-story-index.py`, 13 stories), and `BLUEPRINT.md` (§2.1/§4.8 already updated at S0007 for the ADR settlement) are all synchronized. `scripts/kg/compile.py` regenerated the tracker fenced regions from `kg-source/features/F0001.yaml`'s `status: done` / `roadmap_section: Completed` fields. `validate-trackers.py --feature F0001 --run-id 2026-09-08-b5af1e54` invocation recorded in `lifecycle-gates.log`.

## Validator Results

| Validator | Command | Result |
|-----------|---------|--------|
| Tracker validation | `validate-trackers.py --product-root ... --feature F0001 --run-id 2026-09-08-b5af1e54` | PASS (recorded per gate, see `lifecycle-gates.log`) |
| Story index | `generate-story-index.py planning-mds/features/` | 13 story files found, regenerated |
| KG integrity | `scripts/kg/validate.py` | PASS — 10 code bindings, 0 uncovered features |
| KG reproducibility | `scripts/kg/validate.py --check-reproducible` | PASS |
| KG drift (post status-change) | `scripts/kg/validate.py --check-drift` | PASS |
| Template/framework validators | CI `framework-validators` job, run `34556444400` | SUCCESS |
| Feature evidence (closeout) | `validate-feature-evidence.py --feature F0001 --run-id 2026-09-08-b5af1e54 --stage closeout` | PASS (this closeout pass) |

See `lifecycle-gates.log` for the full per-gate command/result history (G0 through G8).
