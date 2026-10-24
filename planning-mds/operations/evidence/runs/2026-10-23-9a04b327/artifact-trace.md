# Artifact Trace — F0005-one-time-docling-ingestion run 2026-10-23-9a04b327

## Artifacts Read

- `planning-mds/BLUEPRINT.md`, `docs/agent-instructions.md` (via `project_context.py --action plan`)
- `planning-mds/features/F0005-one-time-docling-ingestion/**` (PRD, four stories, STATUS, README, GETTING-STARTED, assembly plan, compatibility evidence, synthetic comparison)
- `planning-mds/architecture/decisions/ADR-0060-docling-graph-document-pipeline-orchestration.md`
- `planning-mds/features/archive/F0004-content-artifact-model/{PRD,STATUS,feature-assembly-plan,F0004-S0001-…}.md`
- `planning-mds/operations/evidence/runs/2026-10-17-8a6cc79f/{gate-decisions,pm-closeout}.md` (F0004 Step 1a PASS; F0005 handoffs)
- `planning-mds/operations/evidence/runs/2026-10-15-bbd8df01/gate-decisions.md` (format reference)
- `planning-mds/kg-source/features/F0005.yaml`; `scripts/kg/lookup.py F0005` output
- `neuron/packages/brain-extraction/src/brain_extraction/profiles.py`; `config/local.yaml`

## Artifacts Created Or Updated

Phase A (Product Manager):

- `planning-mds/features/F0005-one-time-docling-ingestion/PRD.md` — rewritten for local qualification and gated activation; qualification thresholds
- `F0005-S0001` … `F0005-S0004` — rewritten with numbered, live-evidence acceptance criteria
- `F0005-S0005-qualify-text-origin-and-enable-v2-publication.md` — new
- `acceptance-criteria-checklist.md` — new (33 story ACs plus cross-cutting checks)
- `STATUS.md` — planning position, S0005 row, A-4 prerequisite reassigned; story provenance table untouched (append-only, empty)
- `README.md` — status, S0005 row, story count
- `planning-mds/BLUEPRINT.md` — §3.3 S0005 link and S0004 status text; §4.8 date-candidate producer decision
- `planning-mds/features/F0016-semantic-interpretation-runs/README.md` — date-candidate producer assignment
- `planning-mds/features/STORY-INDEX.md` — regenerated (32 stories)

## Generated Evidence

- `commands.log`, `lifecycle-gates.log`, `gate-state.json` — gate runner outputs

## External Or Global Evidence References

Dependency evidence audit (direct dependencies from the PRD, the F0005 shard and KG lookup):

| Dependency | Approved evidence reference | Use |
|---|---|---|
| F0001 | `planning-mds/operations/evidence/runs/2026-09-12-855d2b93/evidence-manifest.json` (via `features/F0001-…/latest-run.json`) | Direct-client baseline, fixtures, ADR-0055 inference profile |
| F0002 | `planning-mds/operations/evidence/runs/2026-09-27-bb7c8d1d/evidence-manifest.json` | Principals, grants, audited authorization |
| F0003 | `planning-mds/operations/evidence/runs/2026-10-03-57d14a51/evidence-manifest.json` | Persistence, migration and restore discipline |
| F0004 | `planning-mds/operations/evidence/runs/2026-10-17-8a6cc79f/evidence-manifest.json` | v1/v2 contracts, verifier, text origin, v2 writer switch, v1 fallback; Step 1a PASS; F0005 handoffs in its `pm-closeout.md` |

Impacted downstream features (audit pending — none has a feature evidence package): F0014, F0015, F0016 (now owns date candidates), F0022, F0024, F0026, F0032.

## Omissions And Waivers

- No repo-wide feature-evidence validation was run (not a plan obligation).
- No feature evidence package is created at the feature index root; the feature action owns it.
- The 2026-09-20 to 2026-09-22 synthetic runtime evidence is cited from the feature folder, not re-executed.
