# nebula-insurance-brain

Nebula Insurance Brain — a continuously evolving enterprise semantic system for commercial Property & Casualty insurance. It ingests documents once, preserves evidence, separates what sources claim from what the enterprise accepts, and exposes governed bitemporal knowledge through 360 views, search, graph, APIs, agents, and conversation.

## Status

F0001 runtime proofs are implemented. F0005's synthetic development scope is complete: its opt-in Docling-Graph candidate has durable jobs, engine integration, PostgreSQL recovery proof, and a recorded-response dense comparison with multi-region review evidence. Production qualification and activation are future work. The architecture baseline is `planning-mds/architecture/master-blueprint.md`; the framework entry point is `planning-mds/BLUEPRINT.md`.

## How this repo is built

This product is driven by the sibling [`nebula-agents`](https://github.com/gajakannan/nebula-agents) framework. Sessions run inside `nebula-agents/` with this repository as `{PRODUCT_ROOT}`:

```bash
export NEBULA_PRODUCT_ROOT=/absolute/path/to/nebula-insurance-brain
cd ../nebula-agents
python3 agents/scripts/run-gate.py --action init --list
```

The framework pin and the layout convention are recorded in `planning-mds/BLUEPRINT.md` section 0.

Repo-specific agent guidance and planning checks live in [`.nebula-project.yaml`](.nebula-project.yaml), [agent instructions](docs/agent-instructions.md), and [the review checklist](docs/plan-review-checklist.md). See [CONTRIBUTING.md](CONTRIBUTING.md) for local validation and [adoption status](docs/framework-adoption.md) for the required framework release/pin coordination.

Open this repository directly for Git/source control. The parent `nebula/` is a collection of independent repositories, not their Git root. Editors supporting VS Code workspace files can open [nebula.code-workspace](nebula.code-workspace) to show both Brain and the sibling framework as separate repositories.

## Layout

| Path | Purpose | Owning role |
| --- | --- | --- |
| `planning-mds/` | Blueprint, features, architecture, ADRs, kg-source, evidence | product-manager, architect |
| `engine/` | Python backend: FastAPI API, worker, semantic kernel packages, Alembic migrations | backend-developer |
| `neuron/` | Python AI runtime: Docling-Graph document pipeline (planned, ADR-0060), interpretation, conversation, learning, MCP tools | ai-engineer |
| `experience/` | React and TypeScript web app, including the Nebula Review Panel | frontend-developer |
| `ontology/`, `profiles/`, `schemas/`, `knowledge-packs/` | Authored semantic assets compiled into the runtime | architect |
| `golden-corpus/` | Version-controlled evaluation fixtures | quality-engineer |
| `scripts/kg/` | Knowledge-graph toolchain (product-owned copy of the framework tooling) | architect |

Full tree: `planning-mds/architecture/master-blueprint.md` section 77.

## Knowledge graph

`planning-mds/kg-source/**` is authored; `planning-mds/knowledge-graph/*.yaml` and the REGISTRY and ROADMAP tables are compiled by `scripts/kg/compile.py`. Activate the local reproducibility hook once per clone:

```bash
git config core.hooksPath .githooks
```

## License

See [LICENSE](LICENSE).

## Start with an example

Read [EX-GL-001: from policy evidence to guideline assessment](planning-mds/examples/neurosymbolic-gl/README.md) and the [concept coverage map](planning-mds/examples/README.md). The v0.1 roadmap now includes [F0065](planning-mds/features/F0065-grounded-gl-guideline-assessment/README.md), a bounded neurosymbolic assessment with six planned stories. All example outputs are synthetic; F0065 remains planned; F0001 has runtime proofs and F0005 has an unactivated candidate pipeline.

## Document pipeline direction

[ADR-0060](planning-mds/architecture/decisions/ADR-0060-docling-graph-document-pipeline-orchestration.md) proposes Docling-Graph to coordinate conversion through Docling and extraction over saved native content. F0005 must prove the pinned integration and durable parse checkpoint before activation; the current F0001 runtime still uses Docling and a direct vLLM adapter.
