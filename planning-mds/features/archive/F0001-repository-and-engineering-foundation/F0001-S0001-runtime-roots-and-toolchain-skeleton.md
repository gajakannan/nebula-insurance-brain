## Story Header

**Story ID:** F0001-S0001
**Feature:** F0001 — Repository and engineering foundation
**Title:** Runtime roots and toolchain skeleton
**Priority:** Critical
**Phase:** Infrastructure

## User Story

**As a** Dana the Platform Engineer
**I want** the `engine/` and `neuron/` runtime roots scaffolded as uv workspaces with a FastAPI application skeleton, Alembic, lint, type-check, and test configuration, and the CI product-gates job extended to run them
**So that** every later feature lands in a repository whose build, test, and knowledge-graph gates already run on each pull request

## Context & Background

The repository holds only planning content. BLUEPRINT section 2.3 fixes the runtime roots and their owning roles; section 2.1 fixes the stack (Python 3.13, FastAPI, Pydantic v2, SQLAlchemy 2, asyncpg, Alembic, pytest, uv). This story creates the skeleton those decisions imply so the proof stories S0003 to S0006 have a home and a gate.

## Acceptance Criteria

**Happy Path:**
- **Given** a fresh clone with Python 3.13 and uv installed
- **When** `uv sync` runs inside `engine/` and inside `neuron/`
- **Then** both workspaces install from committed lockfiles with exit code 0 and no network access beyond the package index

- **Given** the engine application
- **When** `uv run --directory engine pytest` runs
- **Then** the health-endpoint test passes and a coverage report is written under `engine/coverage/`

- **Given** the running API
- **When** `GET /health` is called without credentials
- **Then** the response is HTTP 200 with the git commit sha and the pinned versions of the web framework, SQLAlchemy, and Docling in the body

- **Given** the lint and type configuration
- **When** `uv run ruff check`, `uv run ruff format --check`, and `uv run mypy` run in each workspace
- **Then** each exits 0

- **Given** a pull request
- **When** the CI product-gates job runs
- **Then** it executes the knowledge-graph gates, both pytest suites, ruff, and mypy, and a failure in any of them marks the job failed

**Alternative Flows / Edge Cases:**
- Python older than 3.13 present → `uv sync` fails with a message naming the required version (uv `requires-python` enforced)
- Lockfile drift (pyproject changed without `uv lock`) → CI fails with the uv lock-check error, not a silent install
- `engine/` symbol extraction: `python3 scripts/kg/validate.py --regenerate-symbols --check-symbols` exits 0 with the new Python files walked

## Interaction Contract

N/A — infrastructure story; no user-facing mutation of business data.

## Data Requirements

**Required Fields:**
- `engine/pyproject.toml`, `neuron/pyproject.toml`: workspace definitions with `requires-python = ">=3.13"`
- `engine/uv.lock`, `neuron/uv.lock`: committed lockfiles
- `engine/apps/api/`: FastAPI application module with the `/health` route
- `engine/migrations/`: Alembic environment (no migrations yet)
- Shared `ruff.toml` and `mypy` configuration per workspace
- `.github/workflows/ci-gates.yml`: product-gates job extended with the runtime suites

**Optional Fields:**
- `experience/`: not created here (F0021)

**Validation Rules:**
- Package prefix `brain_` for importable packages (BLUEPRINT section 2.2)
- No dependency pinned to a floating branch; releases or commits only (section 117 note)

## Role-Based Visibility

**Roles that can execute:**
- Developer — runs locally
- CI runner — runs on pull requests and pushes to main

**Data Visibility:**
- InternalOnly content: none; no business data involved
- ExternalVisible content: none

## Non-Functional Expectations

- Performance: the CI product-gates job completes within 10 minutes on the default GitHub-hosted runner; cold `uv sync` per workspace completes within 5 minutes
- Security: no secrets in the repository; committed local configuration contains non-secret defaults only, and future secret-bearing integrations use external secret management
- Reliability: CI is deterministic across two consecutive runs on the same commit

## Dependencies

**Depends On:**
- None (first story)

**Related Stories:**
- F0001-S0002 — containers the tests will need from S0003 onward

## Business Rules

1. Toolchain ownership: `engine/` is owned by the backend-developer role and `neuron/` by the ai-engineer role (BLUEPRINT section 2.3); the skeleton must not blur that boundary with shared source packages outside `engine/packages/` and `neuron/packages/`.

## Out of Scope

- Frontend scaffold and session transport (F0021)
- Any domain model, endpoint beyond `/health`, or migration (F0002 onward)
- Temporal workers (F0050)

## UI/UX Notes

- N/A

## Questions & Assumptions

**Open Questions:**
- [ ] None blocking; see F0001-S0002 for the dependency matrix questions

**Assumptions (to be validated):**
- One uv workspace per runtime root (`engine/`, `neuron/`), each with its own lockfile (BLUEPRINT section 2.2)
- Coverage floor of 80% applies to `engine/` and `neuron/` lines from the first feature run (framework evidence contract)

## Definition of Done

- [x] Acceptance criteria met
- [x] Edge cases handled
- [x] Permissions enforced (N/A — infrastructure story)
- [x] Audit/timeline logged (N/A — no business mutation)
- [x] Tests pass
- [x] Documentation updated (root README, GETTING-STARTED)
- [x] Story filename matches `Story ID` prefix
- [x] Story index regenerated

## Review Provenance

Recorded in `STATUS.md` (Required Signoff Roles, Story Signoff Provenance).
