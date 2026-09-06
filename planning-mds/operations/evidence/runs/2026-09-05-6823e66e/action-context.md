# Action Context — Init Run 2026-09-05-6823e66e

> Init action (`agents/actions/init.md`) under the Feature Evidence Contract, scope `base-run-only`, policy `2026-07-11`. Produces a §8 base run package only; no feature evidence package, no `latest-run.json`.

## Run Identity

| Field | Value |
|-------|-------|
| `INIT_RUN_ID` | `2026-09-05-6823e66e` |
| `PRODUCT_ROOT` | `/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain` (source: `NEBULA_PRODUCT_ROOT`) |
| `INIT_RUN_FOLDER` | `{PRODUCT_ROOT}/planning-mds/operations/evidence/runs/2026-09-05-6823e66e` |
| Session working dir | `/home/gajap/uSandbox/repos/nebula/nebula-agents` (nebula-agents @ `4eaf7b3abef84687f6fda622c61a95d378a50888`) |
| Run-id generation | `date +%F` + `secrets.token_hex(4)` (NOT uuid4) |
| Lifecycle Stage | Init |
| Scope Boundaries | Bootstrap only |

## Project Inputs (I0)

| Input | Value |
|-------|-------|
| `PROJECT_NAME` | Nebula Insurance Brain |
| `DOMAIN_DESCRIPTION` | A continuously evolving enterprise semantic system for commercial Property & Casualty insurance: parse documents once, preserve evidence, separate what sources claim from what the enterprise accepts, and expose governed bitemporal knowledge through 360 views, search, graph, APIs, agents, and conversation. |
| `TARGET_USERS` | [insurance knowledge workers (underwriters, account and claims analysts), human reviewers and annotators (Label Studio), ontology and knowledge-governance stewards, agents and integrations (semantic API, MCP), platform operators and security administrators] |
| `CORE_ENTITIES` | [Tenant, Workspace, KnowledgeBase, Principal, SourceDocument, DocumentVersion, ContentArtifact, ContentBlock, DocumentProfile, ExtractionProfile, SemanticInterpretationRun, Assertion, Entity, FactSlot, CanonicalFactVersion, CanonicalRelationshipVersion, Derivation, ReviewItem, ReviewDecision, LearningCandidate, Conversation, AuditEvent, OutboxEvent; insurance core: Account, Insured, Policy, PolicyTerm, Endorsement, Coverage, CoverageForm, Limit, Deductible] |
| Stack preference | Python 3.13 / FastAPI / SQLAlchemy / PostgreSQL (pgvector, AGE); React + TypeScript; Docling, Docling-Graph, Label Studio (see `planning-mds/BLUEPRINT.md` §2) |

## Pre-existing State (I1 non-empty root confirmation)

`{PRODUCT_ROOT}` was NOT empty at init: it held `LICENSE`, the restructured planning tree (`planning-mds/BLUEPRINT.md`, `architecture/master-blueprint.md`, 53 ADRs, data-model, security and testing indexes), the copied KG toolchain (`scripts/kg/`), shard schemas and ontology seed, and repo hygiene files. The operator confirmed scaffolding into the non-empty root ("go ahead and run step 4", 2026-09-05). Init is idempotent: existing files are preserved, only missing scaffold files are created.

## Scope Boundaries

- Bootstrap only: directory structure, framework product files, trackers, evidence and KG infrastructure, validator sanity.
- No feature folders, no stories, no personas, no kg-source feature shards (those are the seeding step and the plan action).
- Writes only under `{PRODUCT_ROOT}`; `nebula-agents` is not modified.
