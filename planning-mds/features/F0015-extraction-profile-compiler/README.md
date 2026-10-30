# F0015 — Extraction Profile compiler

**Status:** Planned
**Phase:** v0.1A
**Roadmap:** Next

## Overview

Composable extraction profiles compile a shared base with line-of-business extensions; reinterpretation without reparse depends on them (section 8). ADR-0060 targets trusted Docling-Graph templates and explicit pipeline configuration.

Source: `planning-mds/architecture/master-blueprint.md` section 95 (epic roadmap) and section 115.3 (sequencing). Governing ADRs: [ADR-0015](../../architecture/decisions/ADR-0015-extraction-profiles-are-composable.md), [ADR-0016](../../architecture/decisions/ADR-0016-semantic-reinterpretation-is-incremental.md).

## Documents

The [commercial P&C teaching package](../../examples/commercial-pc-account/README.md) illustrates shared/core/GL/property module composition and different GL/property consumer requirements. It supplies planning examples only, not a selected compiler schema or support for additional runtime LOBs. Preserve the source route, package obligations, exact release context and the existing OPEN/TEMPLATE boundary.

Planning prerequisites include F0011's JSON Schema contracts, F0012's foundation ontology, and F0013's GL ontology, alongside the existing F0014, F0005, and F0001 dependencies. The compiler must consume exact releases and preserve constraint execution context, profile requirements, and evidence obligations. Settle the [proposed release contract](../../architecture/decisions/ADR-0045-ontology-release-compatibility.md) before implementation; compilation applies to the TEMPLATE route, with ontology excluded from OPEN prompts under F0066.

Packaged artifacts must preserve the release reference to the versioned predicate-to-projection mapping, including its digest and declared omissions. Graph writing remains the projection consumer's responsibility. The [synthetic interchange examples](../../examples/ontology-interchange/README.md) illustrate that boundary; they are not a compiler schema.

The PRD, STATUS, GETTING-STARTED, and story files are authored by the `plan` action (Phase A and Phase B). Until then this folder is a reserved identifier; the feature shard is `planning-mds/kg-source/features/F0015.yaml`.

## Stories

| ID | Title | Status |
|----|-------|--------|

**Total Stories:** 0

## Docling-Graph scope amendment (2026-09-15)

> **F0005 outcome (2026-10-28) supersedes the scope amendment below.** Graph dense was qualified live and rejected (F0005 run `2026-10-25-4020923b`, PR #30).
> - **Defaults:** `direct-baseline` and the v1 writer stay the defaults.
> - **ADR-0060 status:** stays **Proposed**, with a reopen deadline. **At F0014/F0015 Phase A planning the operator decides** whether to re-plan a Graph candidate (a larger output reservation, another serving model, or Graph direct, each with full re-qualification) or to mark ADR-0060 **Rejected**.
> - **Until then:** plan against the direct baseline and the accepted execution controls in [ADR-0074](../../architecture/decisions/ADR-0074-local-document-job-execution-controls.md). Read the Docling-Graph requirements below as conditional on a re-plan.
> - **A Graph re-plan must also carry** F0005's activation preconditions (SEC-F5-M1 converter isolation, Docling ≥ 2.132 / pillow ≥ 13 requalification, the SEC-F5-L4 residual) and its qualification process fixes: commit the corpus with its generation command, write `commands.log` at execution time, retain predicted values, add a table-aware baseline, and define OCR-count semantics in the AC. Source: the [F0005 PM closeout](../../operations/evidence/runs/2026-10-25-4020923b/pm-closeout.md).

[ADR-0060](../../architecture/decisions/ADR-0060-docling-graph-document-pipeline-orchestration.md) governs this planned work. Carry these requirements into the feature PRD/stories; status remains Planned.

- Compile composed base/LOB profiles into trusted Pydantic templates and explicit pipeline settings while preserving units, qualifiers, ontology mappings, and evidence requirements. Reject unsupported mappings; profile authors cannot select arbitrary Python imports.
- Version and hash the schema, template, prompt, and pipeline configuration. Exercise both fixed F0005 proof templates and compiler-produced templates against the accepted adapter.
- Budget schema/prompt/input and output tokens before every model call, including retries, repair, fill, or reconciliation. A strategy change must not silently truncate or widen scope. Measure the dense-limit case recorded in ADR-0040.

## Statements, time, and governance scope amendment (2026-09-25)

[ADR-0063](../../architecture/decisions/ADR-0063-open-statements-and-signature-alignment.md), [ADR-0065](../../architecture/decisions/ADR-0065-assertion-admission-text-origin-and-mood.md) govern this planned work. Carry these requirements into the feature PRD and stories when the feature is planned; the feature status is unchanged. Examples: [statements, time, and governance](../../examples/statements-time-and-governance.md).

- Template fields remain typed assertions on the template route. Every field that claims span precision passes the admission checks; a field that cannot be located declares coarser precision or `unresolved` (ADR-0065).
- Never place the ontology in an open-extraction prompt. The compiler serves only the template route (ADR-0063).
- **v0.1 scope guard (validate finding P-2):** this feature's Phase A admits only the storage fields, contract checks, and review/display hooks listed here. Alignment, automated deciders, fingerprint-driven scheduling, and time-mention resolution that replaces template fields stay in v0.2+ unless the operator amends the scope (BLUEPRINT §4.11).
