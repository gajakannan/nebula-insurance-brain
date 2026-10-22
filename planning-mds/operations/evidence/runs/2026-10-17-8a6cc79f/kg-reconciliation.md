# Knowledge-Graph Reconciliation — F0004 run 2026-10-17-8a6cc79f

## Scope

Feature F0004; 2026-10-21; Codex, Architect role, after passing G5 and G6.
Baseline: assembly-plan Knowledge-Graph Binding Plan from G0. The Architect
skill and authored KG source contract govern this pass. No runtime code changed.

## Binding Delta

| Capability / node | Binding | G0-declared? | Action |
|---|---|---|---|
| versioned-content-contracts | brain-content package directory, content persistence/worker families, neuron content/provenance/submission/operator modules, revision 0008 and tests | yes | added f0004 shard; cohesive families use globs |
| document-date-provenance | dates contract, document_dates service, SQL tables, date/history/restore tests | yes | added |
| content artifact/block/table/cell and date candidate/selection entities | shared record/table/repository implementation files | yes | added; heterogeneous shared packages do not get an unrelated directory-wide entity binding |
| both content GET endpoints | existing content routes and API tests | yes | added |
| packaged manifest/records/date/output schemas | exact deployed schema assets; outputs service | yes | added; authored planning schema paths retained |
| parse-once-content-artifact | existing full brain-content/brain-ingestion/job package globs | yes | confirmed existing source coverage; added relevant test families |
| backup-and-restore | existing scripts/ops/** | yes | confirmed existing source coverage; added current runbook/restore tests |
| runtime composition / interpretation benchmark | API deps, existing comparison entry point | integration delta | added to existing capabilities |
| migration:f0004-content-contract | revision 0008 Python/SQL plus actual migration tests | concrete revision emerged | added canonical migration and binding |

Authored files: f0004.yaml plus the existing f0001 binding shard. Existing
versioned/date/entity node notes now describe observed implementation, explicit
activation limits, date locking and retained producer-identity limits. No new
capability or business rule was invented. ADR-0073 remains Proposed.

## Canonical Nodes

One new canonical migration node for revision 0008; capability/entity/endpoint/
schema nodes already existed and were affirmed/refined. Inline WHY markers were
regenerated from source, with two resolved markers. No generated projection was
hand-edited. New source/test files were registered with git intent-to-add so the
KG tooling's tracked-file inventory sees the worktree; no commit was made.

## Validator Results

| Check | Result / evidence |
|---|---|
| compile + symbols/decisions regen/check + drift | PASS; artifacts/test-results/g7-final-binding-validation.txt |
| current generated layers | PASS; 985 symbols on bound nodes, 35 bindings, two resolved WHY markers; artifacts/test-results/g7-final-generated-layers.txt |
| reproducibility | PASS; artifacts/test-results/g7-final-reproducibility.txt |
| source routing | DocumentDateService and AuthorizedContentPublisher each resolve once; g7-date-service-routing.txt and g7-publisher-routing.txt in test-results |
| diff impact and risk | full g7-as-built-diff-impact.json; per-node g7-risk JSON and summary; scores 1–4, no high/critical band |

The first pass could not resolve untracked source globs; intent-to-add corrected
the source inventory and the entire ordered G7 pass then succeeded. No validator
waiver or silent source omission. Pre-existing unused edge-type warnings remain.
Coverage-report.yaml was NOT regenerated at this gate; G8 owns that after archive.

## Authorization caller reconciliation and routing limit

The actual API, date service, worker publisher/reader and operator source paths
are now bound and their public symbols are regenerated. Exact source callers
are retained in artifacts/test-results/g7-authorization-source-callers.txt:
API content reads at 73/102; date candidate/selection mutations at 332/484 and
read at 541; publisher decide/recheck at 167/216/233; content access at 53/70/95;
operator units at 109/126/135. These match the independently reviewed authority
boundaries and current runtime tests.

The static Python call projection still omits injected-instance read/mutate
edges and resolves only one of the ambiguous decide call sites. Raw caller-only
outputs are retained, not edited to invent edges. This is an extractor routing
limit after source binding, not an authorization omission or a complete
call-graph claim. The source ledger supplies the exact review route. Broader
extractor resolution can be qualified under F0026; do not treat an empty caller
list as absence of a consumer. Other coverage-gap warnings are baseline fixture/
unrelated consumers; no project-wide graph completion is claimed.

The heuristic test-file ratio is supplemented by actual 90.60% changed-runtime
coverage and the inspected tests; it is not a reason to create mirror tests.
Existing parse-once hotspot second-review evidence is the independent Code
Reviewer report. Owner acknowledgement remains required on a future PR.

## Handoff to Closeout

PASS. Semantic graph, generated symbols/decisions and drift are green. PM may
verify these projections, archive and compile the feature path/state change,
then regenerate the path-sensitive coverage layer. Route any new semantic gap
back to Architect rather than hand-editing generated files. SEC-L3's binding
and regeneration obligation is complete; static caller-resolution limits remain
explicitly carried as a low routing follow-up.
