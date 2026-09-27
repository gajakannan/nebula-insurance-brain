# Architect Validation Report — validate run 2026-09-25-9aa87cdf

**Scope:** `all` (architecture lane). **Subject:** branch `docs/utopia-evolution` at `b1f4357` against `main` at `93cc8c1`. The branch has 79 changed paths (`artifacts/diffs/changed-files.txt`).
**Role:** Architect. **Framework:** `nebula-agents` at the pinned commit `c218bf1`.

The branch was authored outside an action. This lane checks that the knowledge graph, the ADRs, and the architecture artifacts are internally consistent and follow framework ownership and compile discipline. The validator outputs below are tools; the findings are judgment.

## Ontology Integrity

| Check | Result | Evidence |
|---|---|---|
| Graph integrity (IDs, references, paths, feature coverage, bindings, coverage freshness) | PASS; 0 errors; two pre-existing warnings (unused edge types `validated_by`, `supersedes`) | `artifacts/test-results/kg-check-drift.txt`, `kg-check-symbols.txt` |
| Drift between the compiled graph and its sources | PASS | `kg-check-drift.txt` |
| Reproducibility (committed projections and tracker regions equal compile(source); generated-paths policy) | PASS | `kg-check-reproducible.txt` |
| Symbol index | 260 symbols, all on bound nodes | `kg-check-symbols.txt` |
| Orphans (release-readiness, warning level) | 27 on the branch, against 30 on `main` | `kg-check-orphans.txt` |
| Dead code (`--safe-only`) | 52 candidates, all in existing F0001 runtime code; the branch changes no code | `kg-dead-code-safe-only.txt` |

**Compile discipline.** Only authored sources were edited:

- `kg-source/nodes/adrs/adrs.yaml`, with seven ADR node records;
- 28 existing feature shards, which gained `governed_by` edges;
- the new `kg-source/features/F0066.yaml`.

The generated projections (`canonical-nodes.yaml`, `feature-mappings.yaml`, `solution-ontology.yaml`, `code-index.yaml`), the `coverage-report.yaml`, and the REGISTRY/ROADMAP tracker regions differ from `main` only as `compile.py` and `validate.py --write-coverage-report` output. `--check-reproducible` confirms this.

**Orphan analysis.** Nine older ADRs stopped being orphans because the new ADR nodes list them in `related_nodes`: 0005, 0006, 0014, 0017, 0025, 0027, 0039, 0045, 0047. Six new ADRs are orphans: 0063, 0064, 0065, 0066, 0067, 0069. Their only incoming edges come from feature shards still under `coverage_excluded`, and edges from excluded features are not counted. ADR-0068 is referenced by F0065, which is mapped, so it is not an orphan. This is the expected state for architecture that runs ahead of feature planning. The orphans clear when each governed feature's `plan` run completes its G4 ontology sync.

## Canonical Nodes

- **ADR nodes.** The seven records have the `id`, `label`, `path` and `related_nodes` fields. Every path resolves, and every `related_nodes` target exists in the canonical nodes. No capability, entity, workflow, schema, or glossary-term node was added.
- **Deferred concepts.** The new concepts (open statement, typed-assertion source, time mention, document time context, interpretation drop, signature binding, automated decision, action attempt) are defined in the glossary, `data-model.md`, and the ADRs. They are not yet canonical nodes.
- **Why that is correct:** under `plan.md` G4, the Architect adds reusable nodes when a feature's Phase B introduces them. Adding them now would create more orphans.

## Feature Mappings

- **Governance edges added** (duplicates are suppressed by the shard edit): F0004, F0006, F0007, F0008, F0012, F0013, F0014, F0015, F0016, F0017, F0019, F0022, F0023, F0025, F0026, F0027, F0029, F0030, F0032, F0037, F0043, F0047, F0050, F0052, F0056, F0057, F0059, F0065. Feature statuses, phases, and roadmap orders are unchanged.
- **F0066 is reserved** under the same `coverage_excluded` convention `init` used for other placeholder features: phase v0.2B, roadmap order 26.5 (after F0031 at 26, before F0032 at 27). It depends on F0001, F0006, F0012, F0014, F0016, and F0030, and is governed by 0063, 0065, 0068, 0011, and 0016.
- **Coverage:** 4 mapped, 62 excluded, 0 uncovered.

## API Contracts

- `api/brain-api.yaml` is unchanged. No ADR on the branch adds or alters an endpoint.
- New surfaces implied by the ADRs are left to the owning feature's Phase B:
  - setting a document date (F0022);
  - alignment and time-anchor queues (F0043/F0066);
  - rule versions;
  - action preview and execution (F0059).

## Schemas

- No schema file changed.
- `schemas/interpretation-result.schema.json` sets `additionalProperties: false`. The new fields for assertion kind, source phrase, quote, time mentions, mood, drops, and basis hash will therefore need a versioned schema addition with compatible readers.
- `data-model.md` already states that rule ("version additions with compatible readers"). F0006/F0016 Phase B carry it. See finding A-5.

## Authorization

- The ADRs keep authorization in its existing layer and add no grants or policy rows. `policy.csv` is unchanged, so no Casbin drift.
- **ADR-0065** keeps drop excerpts access-controlled.
- **ADR-0069** re-authorizes on replay and at the dispatch gate.
- **ADR-0067** lets an impact-hold detail reveal the existence of restricted content. See finding A-1.
- **ADR-0066** does not state the scoping of name facts. See finding A-2.

## Assembly-Plan Alignment

- **F0002's approved assembly plan** is untouched. The branch's §4.11 records Utopia 0048's extra same-knowledge-base safeguards as a follow-up for the F0002 implementation run, not as an amendment.
- **F0065's draft contracts** (`assessment-contract.md`, `feature-assembly-plan.md`, six stories) do not yet contain the `basis_hash` requirement that its README amendment adds. See finding A-3.
- **F0005 (In Progress; ADR-0060 candidate pipeline)** was not amended. Its evidence mapping (F0005-S0003) will feed the admission and text-origin contract of ADR-0065. See finding A-4.
- **ADR status.** ADR-0063 is marked Accepted as direction on operator authority; its implementation proof gates are explicit. ADR-0064 to ADR-0069 are Proposed with proof gates, consistent with `docs/agent-instructions.md`.

## Findings

| ID | Severity | Artifact | Finding | Recommended owner / action |
|---|---|---|---|---|
| A-1 | Medium | `architecture/decisions/ADR-0067-automation-gated-by-unrecallable-impact.md` §1 | The hold reason `IMPACT_HOLD:<kind> <detail>`, for example "3 assessments" or "cited in an answer", can tell a reviewer that restricted derived content or conversations exist. This conflicts with master blueprint §107.4 and ADR-0042/0053, under which a response must not reveal the existence of restricted evidence. | Architect: amend ADR-0067 so the detail is filtered to the viewer's current authorization, with a non-revealing generic reason otherwise. Add a proof gate. |
| A-2 | Medium | `ADR-0066-names-are-time-bounded-claims.md` §1 | ADR-0061 makes entity identity tenant-scoped with KB associations, while semantic content stays KB-owned. ADR-0066 does not say that name facts and the `entity_alias` projection are KB-owned. The risk is that one KB's names become searchable or displayed through another KB of the same tenant. | Architect: state KB ownership of name facts and a per-KB alias projection. Add a cross-KB negative case to the proof gates. |
| A-3 | Medium | `features/F0065-grounded-gl-guideline-assessment/README.md` amendment versus `assessment-contract.md` and stories S0002/S0003 | The README says to add `basis_hash` to assessment records. The feature's own draft contract and stories, which are further along than a placeholder, do not carry it, so the contract and the amendment disagree. | PM + Architect: carry the requirement into F0065's contract and stories through a `plan` (Phase B, existing) update, or mark it as deferred to F0056. |
| A-4 | Medium | F0005 (In Progress) — `F0005-S0003-reinterpret-saved-json-and-map-evidence.md` | F0005 produces the scanned/native bundles and evidence mappings that ADR-0065's `text_origin` and admission checks depend on (OCR versus stated text, server-located quotes). F0005 has no scope amendment, so its candidate pipeline could be activated without recording text origin. | Architect: add an ADR-0065 note to F0005's activation criteria (S0004), or explicitly defer to F0004/F0016 with a recorded rationale. |
| A-5 | Low | `schemas/interpretation-result.schema.json`, `schemas/review-decision.schema.json` | `additionalProperties: false` means the ADR-0063/0064/0065/0067 fields need versioned schema additions. This is not yet listed as a Phase B obligation in the F0006/F0016/F0022 amendments. | Architect: add a one-line schema-version obligation to those amendments at their plan runs. |
| A-6 | Low | `kg-check-orphans.txt` | Six new ADR nodes are orphans until feature planning binds them. | Expected. Each governed feature's `plan` G4 clears them. Re-check at release readiness. |
| A-7 | Low | Master blueprint §28 | The `SemanticInterpretationRun` field list does not include the document time context or `basis_hash`, which ADR-0064/0068 add. §29 and `data-model.md` do include them. | Architect: extend the §28 field list at the F0016 plan run. |
| A-8 | Info | Framework (`nebula-agents` `c218bf1`) | `init-run.py` requires `--feature`, so it cannot initialize a validate run with no feature. The generated validate prompt asks for an `evidence-manifest.json`, while `validate.md` and the spec say validate has none. `exec-and-log.py` does not pass the child's output through for artifact capture. | Framework maintainer: reconcile in `nebula-agents`. This run's workaround is recorded in `action-context.md` and `artifact-trace.md`. |

| A-9 | Info | Framework — `agents/actions/spec/validate.yaml` V3 checkpoint and `agents/scripts/run-gate.py` `attest_checkpoint` | The V3 `requires` entry is prose, but the driver hashes each `requires` entry as a run-folder file. So `--attest-checkpoint validate-approval` always fails with `checkpoint_output_missing`, and no validate run can record V3 in its journal. Observed at V3 of this run. | Framework maintainer: list `pm-validation-report.md`, `architect-validation-report.md`, and `implementation-validation-report.md` in the spec's `requires`. |

No Critical or High findings.

## Result

**PASS WITH RECOMMENDATIONS.** The knowledge graph is intact, reproducible, and drift-free, and the architecture additions are internally consistent. A-1 and A-2 are security-relevant clarifications to Proposed ADRs and should be applied on the branch before integration. A-3 and A-4 route to feature owners. A-5 to A-7 are carried into feature planning.
