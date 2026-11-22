# Feature Assembly Plan — F0011: JSON Schema contract system

**Created:** 2026-11-20
**Author:** Codex / Architect
**Status:** Phase B revision approved by operator token `approve-phase-b` on 2026-11-22; implementation Not Started
**Plan Run:** 2026-11-21-e4098d22 (B, existing)
**Approved Baseline:** 2026-11-20-ccb1bd39; operator token `approve-phase-b` on 2026-11-20
**Review Input:** 2026-11-21-b4cd07e4 (READY; two Medium, four Low findings)
**Requirements:** Phase A approved by the operator (`approve`, recorded as approve-phase-a).

## Overview

Publish a versioned, offline JSON Schema 2020-12 bundle, generated Pydantic models,
headless AJV conformance and a shared OpenAPI snapshot. Integrate actual existing
consumers while preserving domain guards, current authorization, wire versions and
history. The detailed policy in [contract-design.md](contract-design.md), exact
[inventory](contract-inventory.yaml), [profile](schema-validation-profile.yaml),
six source schemas and synthetic [cases](contract-examples.json) are part of this
plan. All implementation paths below are proposed; this action creates no runtime.

This is a Python/TypeScript infrastructure feature. Generic C# template examples
do not override the product stack. No entity CRUD, new screen or new endpoint.

## Build Order

| Step | Scope | Stories | Integration checkpoint |
|------|-------|---------|------------------------|
| 1 | Explicit source inventory, immutable offline bundle and wire profiles | S0001 | Source closure, keyword/profile checks, hash/identity corruption refusal |
| 2 | Publication aliases and answer/value examples | S0002/S0003 | Nine states, absence failures, exact money and namespace fixtures |
| 3 | Generated Pydantic, AJV, metadata and OpenAPI checks | S0004 | 100% common cases; no lossy round trip or silent missing result |
| 4 | Content/assertion and FactSlot/temporal consumer adoption | S0005 | Per-resource mapping, integration/dev stored-version sweep before guard rollout, native differential and same-UoW guard regressions |
| 5 | Installed package/build/CI proof and developer handoff | S0006 | Clean install outside checkout; deterministic regeneration; drift injection fails |

## Existing Code (Must Be Modified)

Paths are product-root relative and were inspected during this plan.

| Existing file | Current state | Required change |
|---------------|---------------|-----------------|
| engine/packages/brain-contracts/src/brain_contracts/assertions.py | Four local schema names; offline referencing Registry; input/output ContractModel guards | Delegate registry/validation to common runtime, preserving exported functions and AssertionContractError/Unsupported |
| engine/packages/brain-contracts/src/brain_contracts/dispatch.py | Legacy selector-absent reader and explicit v2; no failed-reader downgrade | Retain dispatch and native adapter shape; prove it uses the shared installed resources |
| engine/packages/brain-contracts/src/brain_contracts/result.py | Existing hand-authored legacy Pydantic DTOs with some defaults | Retain external compatibility; source-gated adapter/to_wire and generated counterpart prove conformance; no forced public DTO rewrite |
| engine/packages/brain-content/src/brain_content/contracts.py | Five packaged schemas plus parent-directory planning fallback | Delegate to common installed bundle, remove fallback; preserve error mapping and native decode/format behavior |
| engine/packages/brain-content/src/brain_content/manifest.py, records.py, dates.py, outputs.py | Existing v1/v2 content readers and input/output validation | Preserve callers and selector/activation; use delegating loader, add targeted differential cases |
| engine/packages/brain-factslots/src/brain_factslots/resolution.py | resolve(), canonical key parsing and ResolutionResult.to_json | Validate normalized key/result at existing authorized service boundary before insert/return |
| engine/packages/brain-factslots/src/brain_factslots/answers.py | canonical_value() domain/evidence/member checks; tolerant source_keys() | Add shared canonical envelope check after existing guards, preserving T-08 and legacy bypass |
| engine/packages/brain-temporal/src/brain_temporal/commit.py | _commit_v1(), _remainder(), same-slot lineage and bounded temporal commit | Validate new normalized temporal carriers before writes; retain all old domain reason codes, legacy remainders and atomicity |
| engine/apps/api/src/brain_api/schemas/facts.py | CommitProposalIn, CommitResponseOut, FactVersionOut and validity-unknown DTOs | Preserve API behavior; prove source-schema/output correspondence; no schema guard ahead of protected source checks |
| engine/apps/api/src/brain_api/routes/facts.py | execution.read/mutate with exact additional source READ and attestation checks | Validate commit serialized result inside operation before mutate commits; validate GET only after successful full read authorization |
| engine/apps/api/src/brain_api/app.py | create_app() with existing /openapi.json hook | Install generated OpenAPI snapshot and verify real route parity in tests |
| engine/apps/api/src/brain_api/errors.py | ProblemDetails handlers and existing domain errors | Map unexpected canonical schema invariant failure to generic 500 contract_invariant_failed, no data text |
| engine/packages/brain-contracts/pyproject.toml; brain-content/pyproject.toml; brain-factslots/pyproject.toml; brain-temporal/pyproject.toml | Existing package dependencies and schema package-data globs | Package common resource tree/generated models; content/factslots/temporal may depend on brain-contracts; no reverse dependency cycle |
| engine/pyproject.toml and engine/uv.lock; neuron/uv.lock | Existing workspace/locked dependency graph | Add build-only contract-build group/generator and lock one coherent runtime distribution in both Python workspaces |
| experience/package.json and experience/pnpm-lock.yaml | Current Vite/Vitest host; no AJV | Add locked AJV 2020-12, ajv-formats, jsonc-parser tooling and contracts:check script; no UI code |
| .github/workflows/ci-gates.yml | Existing product checks | Add deterministic contract/check/install/conformance lanes; no conditional skip when the feature changes a selected schema/consumer |

No brain_domain source imports a schema library. Existing Neuron consumers are
tested through their shared package imports; there is no model/prompt/pipeline change.

## New Files and Outputs

| Proposed path | Owner | Purpose |
|---------------|-------|---------|
| scripts/contracts/sources.yaml | Backend + Architect review | Explicit 21-resource source list and native/portable entry-point policy |
| scripts/contracts/generate.py | Backend | Closed local build, code generation, metadata/OpenAPI emission and --check mode |
| scripts/contracts/check.py | Backend/QE | Join expected case results, generated artifacts and OpenAPI/reference coverage |
| scripts/contracts/check_stored_fact_versions.py | Backend/QE | Read-only integration/dev full-history serialization and exact response-guard preflight; safe aggregate report |
| schemas/contracts/v1/*.schema.json and manifest.json | Generated | Root runtime release snapshot and digest manifest |
| engine/packages/brain-contracts/src/brain_contracts/schema_runtime.py | Backend | Immutable bundle registry, profile checks, decode and validate APIs |
| engine/packages/brain-contracts/src/brain_contracts/model_adapter.py | Backend | Source-schema pre/post guards and non-lossy to_wire |
| engine/packages/brain-contracts/src/brain_contracts/generated/contracts_v1.py | Generated | Pydantic v2 models; preserve openness, nullable/optional distinctions and source annotations |
| engine/packages/brain-contracts/src/brain_contracts/resources/v1/* | Generated | Same schema bytes, manifest, ui-metadata.json and brain-api.openapi.json installed in the wheel |
| engine/apps/api/src/brain_api/contract_openapi.py | Backend | Load/cache installed self-contained OpenAPI; no source checkout at runtime |
| experience/scripts/contracts/runtime.mjs | Frontend | Strict portable JSON decode and configured AJV 2020-12 facade |
| experience/scripts/contracts/check.mjs | Frontend | Execute common cases, fail missing/duplicate cases and emit machine results |
| experience/src/generated/contracts/v1/* | Generated | Same selected source schemas, manifest and metadata for JS consumer |
| engine/packages/brain-contracts/tests/test_schema_runtime.py, test_generated_models.py | Backend/QE | Registry/profile/decoder failure and source-gated Pydantic proof |
| engine/tests/integration/test_f0011_consumer_contracts.py | QE | Real content/assertion/FactSlot/temporal boundaries and no partial business writes |
| engine/apps/api/tests/test_contract_openapi.py | Backend/QE | Real route/OpenAPI and existing response fixture compatibility |
| neuron/tests/integration/test_f0011_shared_bundle.py | QE, AI Engineer consultation | Shared bundle installed in Neuron without changing the producer |
| experience/scripts/contracts/runtime.test.mjs | Frontend/QE | AJV/decoder options, formats, duplicate-key and no-mutation tests |
| scripts/contracts/tests/test_artifact_reproducibility.py | QE/DevOps | Clean build/install and intentional stale/hash/identity drift |

The planning files under planning-mds/schemas are authored now; runtime files above
are future feature outputs. Do not bind nonexistent paths into the KG.

## Step 1 — Offline Bundle and Profiles (S0001)

### Interfaces

Implement these public Python interfaces in schema_runtime.py. Names are proposed;
lookup --defines ContractBundle found no existing symbol at plan time.

```python
from dataclasses import dataclass
from typing import Any, Literal, Mapping

WireProfile = Literal["portable-json/v1", "native-compat/v1"]

@dataclass(frozen=True, slots=True)
class ContractRef:
    name: str       # allowlisted resource basename
    version: str    # manifest-selected string, not inferred from payload
    pointer: str = ""  # empty root or JSON Pointer beginning with /

@dataclass(frozen=True, slots=True)
class ContractIssue:
    code: str
    contract_id: str
    schema_pointer: str

class ContractError(ValueError):
    code: str  # constant safe code; never include payload or schema repr

class ContractBundle:
    @classmethod
    def installed(cls) -> "ContractBundle": ...
    def validate(self, ref: ContractRef, value: Any, *, profile: WireProfile) -> None: ...
    def decode(self, raw: bytes | str, *, profile: WireProfile) -> Any: ...
    def schema(self, ref: ContractRef) -> Mapping[str, Any]: ...
    def metadata(self, ref: ContractRef) -> Mapping[str, Any]: ...

def validate_contract(ref: ContractRef, value: Any, *, profile: WireProfile) -> None: ...
```

`schema()` returns a detached view/copy, never a mutable reference that can alter
the cached registry. Any internal validator cache is keyed by bundle digest,
schema identity, pointer and profile; it cannot survive an incompatible bundle.

### Logic

1. Load installed manifest and allowlisted resources using importlib.resources.
   Check manifest shape, unique identities/names, versions and SHA-256 of each
   schema. Strict parsing rejects duplicate keys and malformed UTF-8.
2. Admit only the declared dialect/subset/annotation types. Traverse schema
   locations, check every ref target and reject external/recursive/dynamic refs.
   Register all resources by their actual $id; URI resolution is pure lookup.
3. Construct one immutable bundle and validator cache only after complete success.
   Initialization failure cannot expose a partial bundle or planning fallback.
4. Select wire profile at the caller boundary before parsing. Decode/admit input,
   evaluate the exact schema, return None on acceptance. No normalization,
   coercion, defaults or property deletion occurs in structural validation.
5. Emit only constant code, contract ID and safe schema-pointer diagnostics to
   internal check output; no instance paths/values in public failures.

Closed errors: CONTRACT_BUNDLE_INVALID, CONTRACT_VERSION_UNSUPPORTED,
CONTRACT_SCHEMA_UNSUPPORTED, CONTRACT_REFERENCE_UNRESOLVED,
CONTRACT_JSON_INVALID, CONTRACT_JSON_UNSUPPORTED, CONTRACT_INSTANCE_INVALID,
CONTRACT_MODEL_MISMATCH. All are exceptions, not fact information states.
Bundle integrity errors stop startup; existing adapters translate instance errors
to their existing safe error classes. The new portable facade has no HTTP route.

## Step 2 — State, Money and Identifier Publication (S0002/S0003)

The additive schemas reference existing definition pointers. Do not move the
source definitions or add new members to fact-answer/v1. Copy all source bytes
into the selected runtime snapshot, including reference closure. Alias annotation
metadata is descriptive only. Six design schemas parse and synthetic expectations
can be validated during plan; the feature action must run actual consumers.

Execute every nine-state acceptance and negative case; scope pages/blocks retain
the shipped bounds and mandatory artifact/release. Add format-boundary cases,
duplicate pages/blocks, JSON numbers passed as money, huge decimal exponent
expansion, original currency, unknown currency domain refusal, basis-required
predicate, mismatched normalized identifier and inverted effective interval.
Keep structural and domain outcomes in separate columns. Retain the EX-GL-001
continuing example, EX-OWN-002/003 and F0007 worked/boundary fixtures; all are
synthetic development data, never frozen holdout.

## Step 3 — Typed Models, JavaScript and OpenAPI (S0004)

### Adapter and JS interfaces

```python
from typing import Any, TypeVar
from pydantic import BaseModel

ModelT = TypeVar("ModelT", bound=BaseModel)

def parse_model(ref: ContractRef, raw: bytes | str,
                model: type[ModelT], *, profile: WireProfile) -> ModelT: ...
def to_wire(ref: ContractRef, model: BaseModel, *, profile: WireProfile) -> Any: ...
```

```typescript
type ContractRef = { name: string; version: string; pointer?: string };
type CaseResult = { id: string; accepted: boolean; contract: string;
                    version: string; consumer: "ajv"; code?: string };
function validateContract(ref: ContractRef, value: unknown): void;
function decodePortableJson(raw: Uint8Array | string): unknown;
function runCases(path: string, outputPath: string): Promise<void>;
```

Use build-only datamodel-code-generator with Pydantic v2 output, a fixed model
name mapping and configuration under scripts/contracts/. Omit timestamps and
absolute paths from generated code. Lock versions/config before accepting output.
No runtime schema-driven Python imports or executable templates from documents.
For source constructs the generator cannot express exactly, keep the source guard;
if a source-valid instance cannot be typed/serialized without loss, fail the build.

parse_model decodes/adopts the selected wire profile, validates source schema,
then calls the generated model. to_wire uses exclude_unset=True, preserves explicit
null and permitted extras, and validates again. Roundtrip changed acceptance or
lost amount/identifier/metadata fails CONTRACT_MODEL_MISMATCH.

The JS facade uses the exact options and parser policy in the contract design.
Register schemas up front and compile synchronously, with no loadSchema/network
path. Frozen input snapshots detect mutation. Case output contains IDs and safe
codes only. Duplicate result IDs, missing cases, stderr crashes, unsupported
profiles and skipped tests make the joiner exit nonzero.

Generate a complete self-contained OpenAPI 3.1 snapshot from brain-api.yaml plus
the schema bundle; rewrite refs to deterministic components with a source-ID map.
Keep assertion trees and annotations equal to sources. Do not copy Pydantic's
model_json_schema output over the source. The inline ProblemDetails is checked
against its source assertion tree. Install the snapshot using FastAPI's existing
app.openapi hook/cache and prove route parity, including catch-all file paths.

### Complete shared case inventory

The 74 authored F0011 cases are a seed, not the complete keyword/contract proof.
The feature runner must combine them with the existing F0004, F0006, F0007 and
F0008 contract-examples.json inventories, resolved through those feature shards
(including archived paths), into one uniquely identified execution list. Preserve
the original expectations and record each imported source/case ID. Add positive/
negative branch and format cases for every selected resource that remains
uncovered. A source conditional branch or supported validation behavior without
its required cases makes check.py fail rather than reporting partial conformance.
The cases schema admits resource versions 1, 2 and future positive versions; its
own case-inventory format remains schema-conformance-cases/v1. Native-only
compatibility cases have a separately named fixed profile and are never counted
as portable AJV/Pydantic successes.

## Step 4 — Existing Entry Points and Atomicity (S0005)

### Per-resource adoption (PR-M2)

At feature G0, reconcile all 21 rows in [contract-inventory.yaml](contract-inventory.yaml)
against the actual checkout and copy their consumer entry points, compatibility
tests, version selectors, wire profiles and dispositions into
`scripts/contracts/sources.yaml`. Owner and source identity/hash remain mandatory.
Each entry/test is marked existing, planned, or OpenAPI/doc-only. A planned test
must become executable feature proof; an existing fixture/helper alone is not a
consumer test. G0 records any changed path/selector in the feature evidence before
Step 1; a missing mapping blocks that checkpoint.

Use `delegate` for existing content/assertion schema validators; use `adopt` for
new normalized FactSlot/temporal/response guards and additive aliases; use
`retain-versioned-boundary` for the native commit request and the manifest-read /
ProblemDetails documentation boundaries. The last two have no existing runtime
JSON Schema validator to delegate. Their OpenAPI assertion-tree/union checks and
actual concrete-reader/HTTP response tests are required instead. Never wrap a
nonexistent validator or count OpenAPI reference equality as runtime integration.

### Stored-version rollout preflight (PR-M1)

S0005 AC4 requires real history evidence in addition to fixtures. Backend authors
`scripts/contracts/check_stored_fact_versions.py`; QE executes it for **both**
integration and dev before enabling the new response guard on either existing
environment. DevOps records the environment inventory and coherent bundle digest
at feature G0. No assertion that these databases are fixture-only is made here.

The proposed command contract, executed from the product root by the later feature
run, is:

```bash
uv run --project engine python scripts/contracts/check_stored_fact_versions.py --environment integration --output <FEATURE_RUN_FOLDER>/artifacts/test-results/stored-versions-integration.json
uv run --project engine python scripts/contracts/check_stored_fact_versions.py --environment dev --output <FEATURE_RUN_FOLDER>/artifacts/test-results/stored-versions-dev.json
```

The command selects the named environment using existing local database
configuration; do not log credentials/DSNs or add an exported secret requirement.
It is an operator preflight, not an HTTP endpoint or a new runtime grant. Its
implementation must:

1. Open a PostgreSQL READ ONLY, REPEATABLE READ transaction before selecting data.
   Record a nonsecret environment identifier, snapshot time, code revision and
   candidate bundle digest. Stream **every** `fact_versions` row, including closed
   recorded ranges, historical pilot values, temporal-v1 rows and split/remainder
   versions; do not use a current-only or valid/known-coordinate filter. Count the
   rows in the same snapshot and reconcile selected = checked, with zero skips.
2. Reuse `brain_persistence.repositories._fact_version_from_row` (or an extracted
   equivalent shared with the repository) and
   `FactVersionOut.from_domain(...).model_dump(mode="json")`, including the existing
   absent-temporal serialization. Run the **same** candidate response guard and
   fixed native profile used by GET, including reference/format checks. Exercise
   `FactValidityUnknownOut` separately in the temporal route fixtures; the sweep
   does not bypass authorization or call the HTTP facade and create audit writes.
3. Count mapping/serialization failures, guard failures and legacy/temporal groups.
   Emit only counts, environment label, code/bundle identity and fixed error codes /
   contract IDs. Do not persist values, evidence, row identifiers, exception text
   or credentials in the report. Never rewrite, coerce, delete or repair a row.
4. Exit 0 only for complete, zero-failure coverage. Exit 1 for a data/guard mismatch;
   exit 2 for configuration, unavailable database, incomplete enumeration or other
   execution failure. Empty databases require an explicit zero-row environment
   inventory signed by QE/DevOps; an unavailable database is never an empty pass.
5. QE retains both reports for S0005 AC4 and verifies that the database remained
   read-only. DevOps keeps the previous coherent deployment until both reports
   pass against the release candidate. If a mismatch exists, stop rollout and
   reconcile the guard/version boundary with Architect; no cleanup migration,
   silent validation fallback or historical payload rewrite is authorized.

Repeat the sweep against the final candidate while old-version writers are paused
for the deployment cutover, so writes after the first snapshot cannot escape the
check. Restore service with the coherent new bundle only after success. A changed
guard, bundle, serializer or stored population requires fresh reports. The future
feature tests must include a stored serialization/format mismatch, closed history,
legacy remainders, empty and unavailable databases, incomplete iteration and a
read-only enforcement check. This planning action does not access either database.

### Read audit follow-up (PR-L3)

The existing read facade commits SUCCEEDED after all source READ checks, then GET
serializes/validates the response. An internal invariant failure can therefore
return generic `contract_invariant_failed` 500 after a SUCCEEDED read audit.
Track this Low finding under S0005 AC6; do not claim it is fixed or accepted by
planning. **Owner: Security Reviewer, due at feature G3 before implementation
approval.** Backend/QE inject a response-guard failure and prove: authorized read
audit succeeds, HTTP returns the generic 500 with no payload/pointers, and a denied
source still returns 404 before guard evaluation. Security must record whether
this bounded internal-invariant audit meaning is accepted. If it is not accepted,
Architect must revise the read-finalization design and obtain current tests/review
before the feature advances; the discrepancy cannot silently disappear at closeout.

### Mutation traceability

| Entry point | Action / carrier | Authority / concurrency | Validation failure and audit | Required test |
|-------------|------------------|-------------------------|------------------------------|---------------|
| Maintainer generate command | Publish contract artifacts | Reviewed repo sources; output staged then atomically replaced; no runtime grant | Nonzero exit; no accepted partial output; manifest/check result is artifact audit | Deliberate bad ref/hash leaves previous valid tree intact |
| Existing content/result parsers | Read/admit selected version | Existing consumer principal and native reader chosen first | Preserve CONTENT_CONTRACT_INVALID / assertion safe errors and current worker refusal behavior; no fallback | Real legacy/current callers, outside-checkout package test |
| FactSlot service resolve | Canonical key/result and slot rows | Current AuthorizationExecution mutate, ownership, existing uniqueness/concurrency locks | Existing domain reasons first; unexpected normalized schema mismatch rolls back slot/qualifier writes; current facade audit | DB state re-read after rejection/concurrent resolution |
| Existing POST /facts/{factSlotId}/commits | Typed answer/temporal proposal and serialized result | Current fact_slot:commit AND exact source READ in same UoW; slot lock, expected version, idempotency, exclusion constraint | Preserve domain 422/409, denied 404 and failure audit; unexpected invariant => generic 500 before outer commit | No version/change/outbox partial effect; legacy/current response and retry proof |
| Existing GET /facts/{factSlotId} | Serialized selected historical version/validity-unknown | Current fact_slot:read and exact absence/name/attestation source READ; existing two-coordinate reader | Full authorization completes before validation result is exposed; generic safe 500 on invariant | Denied source remains 404 even if payload would fail validation; old flat response unchanged |

No schema-library import enters brain_domain. Pure domain parsing remains the
first semantic authority at existing application boundaries. In canonical_value,
validate the canonical answer after the current evidence/member checks. In
_commit_v1/_remainder validate only newly constructed normalized carriers, preserving
historical legacy remainder handling. The API's mutate `operation` validates
CommitResponseOut serialization before returning to AuthorizationExecution.mutate,
so a response-contract failure occurs before the transaction commits. Do not add
a second nested facade/unit of work. GET output validation runs after the read
facade has completed all additional source READ checks; it creates no business write.

Review submission/grants and AuthX internals are retained boundaries, not a new
generated review service. Existing review/correction and denied-source regressions
must stay passing because they consume the assertion/value contracts.

### HTTP mapping (existing routes only)

| Status | Body / condition |
|--------|------------------|
| 200 | Existing fact/content/read or validity-unknown response; no changed payload |
| 201 | Existing successful canonical commit with current response fields |
| 401 | Existing ProblemDetails for missing/invalid verified credentials |
| 404 | Existing non-disclosing missing/denied resource/source response |
| 409 | Existing stale/concurrent/temporal conflict and authorized content integrity/version cases |
| 422 | Existing domain/request validation reasons and refusal precedence |
| 500 | Generic ProblemDetails code contract_invariant_failed for an internal normalized-carrier/schema mismatch; no payload/pointer details |
| 503 | Existing authorization/audit or content availability failure |

Resource/action policy remains unchanged: content_artifact:read/interpret,
fact_slot:read/commit and review_task:annotate retain the existing grants. No new
Casbin policy rows, permission catalog entries or copied policy files.

## Step 5 — Reproducibility, Installation and CI (S0006)

Implement the following command contract. These commands describe future feature
tools; they are not claimed to have run during planning.

```bash
uv run --project engine --group contract-build python scripts/contracts/generate.py
uv run --project engine --group contract-build python scripts/contracts/generate.py --check
uv run --project engine --group contract-build python scripts/contracts/check.py --cases planning-mds/features/F0011-json-schema-contract-system/contract-examples.json
pnpm --dir experience contracts:check --cases ../planning-mds/features/F0011-json-schema-contract-system/contract-examples.json
uv run --project engine pytest engine/packages/brain-contracts/tests engine/tests/integration/test_f0011_consumer_contracts.py engine/apps/api/tests/test_contract_openapi.py
uv run --project neuron pytest neuron/tests/integration/test_f0011_shared_bundle.py
```

The case path is an explicit test input, not a production runtime dependency.
After feature archival test discovery follows its feature shard path or a stable
test-fixture copy chosen at feature G0; never hardcode an archived path into runtime.
The generator consumes stable scripts/contracts/sources.yaml, not a feature-folder
path, so archiving the planning folder cannot break packaging.

Generator --check uses a temporary output directory and compares every declared
artifact without changing tracked files. Normal generation validates everything
before atomic replacement. Manifest order/JSON formatting/model names and tool
versions are fixed; exclude timestamps, local paths and network-fetched content.
Build a wheel/sdist, install them in a temporary environment outside the checkout,
and run both native readers and portable source checks with source directories
unavailable and network reference retrieval blocked. JS consumes its generated
copy under the same manifest/digest, not a development absolute path.

CI must fail intentional source/model/metadata/OpenAPI/hash drift and missing
consumer results. Run relevant existing engine/Neuron regressions plus fresh
PostgreSQL tests for affected writes; no live model call, PDF reconversion or
production document is needed. Record Python/Node/tool versions, command exits,
case IDs and AC evidence. Minimum changed executable-line coverage is 80%.
Only the future feature run creates QE/review/security/DevOps role reports.

## Complete AC-to-Implementation/Proof Map

| AC range | Implementation boundary | Required observed proof |
|----------|-------------------------|-------------------------|
| S0001 AC1–AC3 | source manifest, registry and ref admission | Identity/version/reference closure; bad/dormant refs and dialect/keyword refusal |
| S0001 AC4–AC7 | profile/annotations, decoder/cache and package | Unknown metadata/ref failures, no mutation, safe diagnostics and fresh installed process |
| S0002 AC1–AC4 | fact-answer schema alias + actual answer adapter | Nine-state accepts, mismatched value/scope, scope shape/bounds/formats and duplicates |
| S0002 AC5–AC7 | semantic examples + current guard integration | Missing endorsement versus negative, denied source before reason, temporal UNKNOWN separate |
| S0003 AC1–AC3 | money source alias + existing domain parser | Exact decimal/original currency, malformed numbers, predicate basis and unsupported currency |
| S0003 AC4–AC7 | identifier source alias + domain normalization | Required scheme/type/value, equal strings different namespace, effective ordering and normalization mismatch |
| S0004 AC1–AC3 | common case runners/joiner | Real Python/Pydantic/AJV, every keyword/format/branch, 100% expected outputs/no skips |
| S0004 AC4–AC7 | generated model/to_wire, metadata/OpenAPI builder | Non-lossy serialization, exact shared refs/annotations and injected drift failure |
| S0005 AC1–AC3 | per-resource inventory, content/assertion delegates and documented retained boundaries | Every entry point/test/selector/disposition reconciled at G0; actual consumer proof and no reader fallback |
| S0005 AC4–AC7 | FactSlot/temporal/API boundaries and UoW | Both stored-history sweep reports pass before guard rollout; legacy/current history unchanged, no partial mutation, READ/admission guards, G3 PR-L3 disposition, no reparse/DDL |
| S0006 AC1–AC3 | generator --check, install smoke and CI | Clean commands/version inventory, deterministic outputs, outside-checkout offline proof |
| S0006 AC4–AC6 | semantic example ownership, AC ledger and handoff | Definitions/worked/boundary links, observed 41-AC proof with coverage, rollback and ADR status |

## Data Model, Cache and Deployment

The only new carriers are immutable bundle/resource/metadata/check artifacts;
their shape is schema-bundle-manifest-v1 and the case schema. No PostgreSQL table,
entity relationship, retention rule, migration SQL, queue or service is added.
See README for the artifact ER/component views; existing C4 context/container
diagrams remain applicable. Cache immutable compiled validators in-process by
bundle hash/ref/profile only; no mutable tenant data and no external cache.

Root/package snapshots are one deployment unit. Rollback restores the previous
coherent package set and its snapshot, not a mix of schema hashes. Never rewrite
historical payloads or reinterpret content. A future DDL need requires plan
amendment and a migration number after current 0015; none is planned here.

## Ownership and Required Handoffs

| Role | Work / completion evidence |
|------|----------------------------|
| Backend Developer | Bundle/generator/Pydantic and application integration; owns fast package/API tests |
| Frontend Developer | Headless JS adapter/runner, locked tooling and JS unit/conformance results; no screens/themes |
| Quality Engineer | Independent expected-case review, PostgreSQL no-partial-write/guard regressions, case/AC and coverage evidence |
| DevOps | Build/lock/packaging/CI and coherent deployment/rollback proof |
| Security Reviewer | Offline ref/parser/codegen trust, safe errors, current source READ order, native/portable boundary review |
| Architect | Shared contract/source/model/route consistency, generated artifact ownership and ADR proof gate |

Required story signoffs: Quality Engineer, Code Reviewer, Security Reviewer,
DevOps and Architect for all six stories. AI Engineer consultation verifies
unchanged Neuron caller behavior; no AI runtime/model work is authorized.
There is no UI/theme/accessibility/visual proof surface in F0011; JavaScript
contract tests are required. Set actual feature-action booleans from changed
paths at G0 rather than copying this planning run's base-only manifest.

## Risks and Reconciliation

- Existing raw FactVersion OpenAPI used nested ranges; actual shipped DTO is
  flat. Additive fact-version-read-v1 corrects documentation without changing
  the API. Keep a flat legacy response fixture and route-level proof.
- A review decision's internal persisted schema is not its HTTP submission DTO.
  Retain that versioned boundary; do not infer request shape from the wrong schema.
- Numeric/format differences between languages are explicit portable-profile
  limits; current native entry points remain compatible and never fallback.
- Generator approximations cannot replace source validation; missing/lossy typed
  cases block build/feature completion. Pin the actual build tools in the feature
  run dependency matrix before accepting generation output.
- Generic framework reference samples use C#/draft-07 paths. The product's Python,
  2020-12 and OpenAPI 3.1 baselines control; no framework changes are required.
- The approved F0011 assembly baseline is revised explicitly for review findings
  PR-M1/PR-M2/PR-L3 in plan run `2026-11-21-e4098d22`; see its gate-decisions.md
  for reconciliation. No requirement, schema assertion or runtime behavior changes. ADR-0013/0077/0078 remain accepted;
  ADR-0079/0039 remain Proposed. F0012/F0015 vocabulary/compilers and F0014/F0023
  completeness/display stay separately owned.

## Planning Risk Signals and Review Controls

The KG diagnostic reports risk 7/10 (high), chiefly from existing shared hubs,
co-change and concentrated ownership: 14 directly related features, 37 mapped
stories, with 113 resolved existing files. This is a routing/risk signal, not a
runtime security finding or a claim that those files changed. The plan modifies
no runtime code. Mitigations already required here are independent plan-review,
all five story signoffs, actual content/assertion/FactSlot/temporal integration,
current source READ/no-partial-write regressions and at least 80% changed-code
coverage. Architect/QE own the broad regression selection; obtain primary
maintainer acknowledgement and an additional independent reviewer before the
future implementation merge. No message was sent to any maintainer by this run.

The tracked HEAD diff-impact check finds zero changed runtime symbols. It does
not index untracked planning files; the explicit 21-resource/six-schema inventory
and KG source review cover those new artifacts. Orphan validation passes with 14
existing advisory nodes outside F0011; retain those as baseline/future-feature
entries rather than inventing F0011 links. The six new schemas, two capabilities
and ADR-0079 all have real F0011 source/mapping references.

## Exit and Approval State

All six stories remain Not Started (41 ACs). Phase A approval from
`2026-11-20-ccb1bd39` is unchanged; story edits add the missing grammatical "to"
only. The original Phase B approval and review READY decision remain historical
evidence for the baseline. G4 ontology sync and all seven ordered G5 exit
checks passed for this revision. The operator explicitly approved it with
`approve-phase-b` on 2026-11-22 in run `2026-11-21-e4098d22`. Its durable
journal and manifest record the post-approval regeneration, validation and
publication outcome. No runtime proof is inferred. ADR-0079/0039 remain
Proposed. Feature G0 must carry this review/finding map and the later G3 PR-L3
follow-up into its evidence before implementation proceeds.
