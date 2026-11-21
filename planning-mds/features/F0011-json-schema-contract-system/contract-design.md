# F0011 — Structural contract design

**Status:** Phase A and Phase B approved by the operator on 2026-11-20; runtime implementation Not Started.
**Decision:** [ADR-0079](../../architecture/decisions/ADR-0079-offline-schema-bundle-and-cross-language-conformance.md).

## Authority and inventory

[contract-inventory.yaml](contract-inventory.yaml) enumerates 21 runtime payload
resources: 17 existing definitions, three additive publication aliases and a
description of the shipped flat fact-read response. Their exact design source
hashes are recorded there. Two additional schemas describe the generated bundle
manifest and the authored conformance cases; they are tooling contracts rather
than business payloads. Existing definitions are not moved or semantically edited
by this plan. The aliases reference their original definitions by JSON Pointer.

The feature run authors `scripts/contracts/sources.yaml` from this inventory and
implements one deterministic generator. `planning-mds/schemas/*.schema.json` is
the authored definition. `schemas/contracts/v1/` is the generated runtime release
snapshot, satisfying the blueprint's root schemas convention. Package resources,
AJV inputs, Pydantic models, UI metadata and OpenAPI components are derived outputs,
checked against that snapshot. No output is a second hand-authored schema source.
Runtime loading never traverses parent directories or reads planning files.

Existing package copies become generated outputs or are removed after callers
delegate to `brain_contracts`. A released schema identity is immutable after its
F0011 baseline is frozen: changing accepted instances requires a new identity and
versioned selector. Metadata-only changes are tracked by release digest and must
not affect acceptance. Generated identity conflicts fail the build; no overwrite.

## Supported schema profile

[schema-validation-profile.yaml](schema-validation-profile.yaml) is the exact
keyword/annotation/option inventory. It covers every validation keyword currently
used by the selected 17 schemas, including contains/minContains/maxContains,
propertyNames, maxProperties, conditional branches and JSON Pointer references.
Unsupported keywords, formats, dialects and nondeclared x-nebula names fail schema
admission before any instance runs. Schema-position traversal must distinguish a
keyword from a property name under properties/$defs: a property called `default`
is data, not an unknown schema instruction.

Only registered resource identities and fragments resolve. Build-time file paths
are allowlisted under the declared source directory; runtime references are looked
up in an immutable in-memory registry with a retrieval function that always fails.
No network request, filesystem URI, dynamic reference, recursive schema or user
plugin is supported. Every ref is checked for a real target even in an otherwise
untaken conditional branch. Bundles with missing hashes/resources fail startup.

Python uses Draft202012Validator with an explicitly populated format checker.
JavaScript uses `ajv/dist/2020.js`, registered known annotations and `ajv-formats`;
all options are explicit in the profile. strictTypes/strictRequired are false
because existing valid schemas use nullable unions and type guards across
conditional/composition branches. strictSchema stays true and the independent
keyword scanner rejects unknown validation instructions. Defaults, coercion and
removeAdditional stay false. Annotation values are preserved, never executed.

## Wire portability and native compatibility

The new reusable facade selects `portable-json/v1` explicitly. It accepts UTF-8
JSON with unique object keys, paired Unicode surrogates, finite binary64 numbers,
and exact integral numbers only in the range ±(2^53−1). Monetary amounts and
identifiers remain strings, so their precision and identity do not depend on
JavaScript numbers. Maximum new-facade instance size is 16 MiB, nesting depth 128,
one million nodes; the bundle is limited to 256 resources. These are the
resource/interoperability limits approved with the Phase B design, not measured
latency claims. Large content is checked per existing JSONL record, not by loading
an entire corpus. A limit/precision failure is explicit `CONTRACT_JSON_UNSUPPORTED`.

Existing entry points are pinned to `native-compat/v1` before input is inspected.
They retain the old parser/domain format, numeric, size and acceptance semantics
while delegating schema lookup and evaluation to the same source bundle. A
native-only number/date/UUID case is tested on that boundary, not misreported as
portable conformance. No failed portable validation can trigger native fallback.
Future consumers select the portable facade by contract; migration of an existing
boundary to it requires a new explicit reader version and differential approval.
This is S0005's documented retained-version boundary, not a silent tightening.

For portable formats, UUID is the case-insensitive 8-4-4-4-12 hexadecimal shape;
date is a real proleptic Gregorian YYYY-MM-DD in 0001–9999; date-time is an RFC3339
instant with an explicit offset, seconds 00–59, optional fractional seconds and
case-insensitive T/Z (no leap-second input); URI-reference is RFC3986 ASCII syntax
with valid percent escapes, including relative and empty references. Tests bind
the same acceptance in both languages; explicit format implementations/checkers
must be present rather than silently accepting a missing optional dependency.
Native existing format behavior stays native. No format check verifies an IANA
zone, source existence, ISO currency support or temporal truncation.

Python rejects malformed JSON before jsonschema. Node uses `jsonc-parser` visitor/
scanner with comments/trailing commas/empty input disabled; every parser error
fails, duplicate property names are checked per object, unpaired surrogates and
nonfinite/unsafe numbers fail before AJV. No repair or best-effort parse is used.
Input objects are never mutated. Opaque property keys are data; no prototype
merging, eval, schema-provided imports or template code executes at runtime.

## Pydantic generation and metadata

Use build-only `datamodel-code-generator` for Pydantic v2 output. Pin its actual
version and configuration in the feature run's Python lock before accepting the
first generated artifact; keep existing Pydantic/jsonschema/referencing versions
locked. Generated code is reviewed and committed, never downloaded or generated
from untrusted documents at runtime. The base adapter validates the original wire
payload against its source schema first and validates serialized output again.
This gate enforces conditions/composition even if type generation approximates
them. Unsupported generation is a build failure, never an Any-only replacement.

Object models retain open-object extra fields where the source allows them and
forbid extras only where closed. Absence differs from explicit null: emit with
`exclude_unset=True`, retain explicitly supplied nulls, and revalidate the result.
No generated default is added to the returned wire payload. Known Python UUID/
datetime domain values may serialize to strings in existing internal adapters;
that does not permit a wire string-to-number coercion before structural checks.
Money and identifier values stay strings. A source-valid instance rejected or
lossily serialized by its Pydantic adapter blocks publication.

Emit `ui-metadata.json` keyed by contract URI and JSON Pointer. It copies only the
eight declared x-nebula annotations and title/description; evidence/security
annotations are descriptive hints, not decision services. Annotations in generated
Pydantic `json_schema_extra`, the AJV source and the OpenAPI component must retain
the same metadata. This feature adds no form renderer or editable UI.

## Existing consumer integration

| Consumer entry point | Integration and compatibility boundary |
|----------------------|----------------------------------------|
| brain_content.contracts.schema / validate_contract; parse_manifest; content record/date/output adapters | Delegate to the shared installed bundle; retain existing native parser/error mapping. Delete parent-directory planning fallback. Content v1/v2 selectors and v2 writer activation stay unchanged. |
| brain_contracts.assertions.validate_contract, ContractModel; dispatch.parse_result / parse_interpretation_result | Delegate schema access; retain AssertionContractError/Unsupported, v1 absence-of-selector and explicit v2 behavior. No failed reader downgrade. |
| brain_factslots.resolution.FactSlotResolver.resolve | After current authority, domain parsing and reference checks, validate canonical key/result before insert/return. Domain remains I/O-free and does not import the schema package. |
| brain_factslots.answers.FactAnswerPolicy.canonical_value | Run existing domain parse/normalization and evidence checks inside the authorized UoW, then validate canonical fact-answer/v1. Source READ key discovery stays tolerant and occurs before protected reasons. |
| brain_temporal.commit.CanonicalCommitService._commit_v1 / _remainder | Validate normalized version_temporal/serialized answer before repository writes. Preserve reason precedence, attestation disclosure checks, row locking, idempotency and two-range constraints. Do not revalidate/rewrite historical legacy remainders as new identity-v1 payloads. |
| brain_api.schemas.facts and routes.facts | Keep current DTO/domain mapping. Check source-owned response shapes and generated model conformance; shared serialized-response checks run inside the existing authorized UoW, before a write commits. Never discover a response-shape failure only after committing effects. |
| Existing Neuron callers of shared content/interpretation contracts | Install the same brain-contracts resource bundle. Existing imports delegate; no Neuron prompt, producer, model or extraction activation changes. Smoke both native readers. |

For domain-invalid input preserve its existing reason and HTTP mapping. A schema
failure after successful canonicalization indicates an internal invariant/build
failure, not a new public answer-state reason. Fail the operation, roll back all
business mutations, audit through the current facade, and expose a generic
ProblemDetails 500 `contract_invariant_failed` without schema pointers/input.
Startup bundle corruption stops startup. No path may serve a stale or alternate
bundle as a recovery fallback.

## OpenAPI and HTTP reconciliation

The design-time OpenAPI stays 3.1.0 and references the same JSON Schema resources.
F0011 adds components for the three value aliases and fact-answer and replaces
the inaccurate nested FactVersion definition with `fact-version-read-v1`, matching
the already shipped flat timestamps. No route, grant or payload is added.
The existing inline ProblemDetails remains because the framework validator
requires it; generation/checking verifies its assertion tree against its shared
source rather than trusting an independent edited copy.

Build a self-contained OpenAPI snapshot by resolving external schema references
into deterministic components and rewriting refs, retaining annotations. Install
that snapshot in brain_contracts resources and use the existing FastAPI openapi
hook/cache in create_app; `/openapi.json` already exists. CI compares normalized
route methods/path parameters/statuses with app.routes. The snapshot must not
claim paths the application lacks or omit a protected application path.
Request/response input checks retain established 401/404/409/422/503 behavior.
The legacy HTTP commit request DTO remains a native compatibility boundary;
do not add schema validation ahead of authorization that changes protected reason
precedence. Reconcile observed request-schema differences through the explicit
inventory and fixture matrix, not by automatically changing a public DTO.

## Proof and release

`contract-examples.json` contains synthetic design expectations. Planning executes
local Python schema/fixture validation only; it does not prove AJV, generated
Pydantic, package installation, consumer integration or runtime outcomes.
The feature run must expand the matrix to cover every supported keyword/format
with accepting and rejecting cases and all source conditional branches. It must
also run bundle/profile corruption, duplicate identity, missing ref in a dormant
branch, unknown dialect/keyword, artifact drift and no-network tests. No skips.

Freeze a reviewed bundle only after all 41 ACs are observed, Python/Pydantic/AJV
agree on every portable case, native differential regressions pass, generated
OpenAPI matches the real routes, installed packages work without the checkout,
and changed executable-line coverage is at least 80%. Publish normal repository
artifacts, with no database registry or mutable latest-schema pointer. Rollback
redeploys the prior coherent package/bundle set; never mixes resource hashes or
rewrites source evidence. No database migration is needed. If scope later needs
DDL, number it after 0015 and amend the plan before implementation.

## Primary technical sources checked 2026-11-20

- [Ajv JSON Schema versions](https://ajv.js.org/json-schema.html) documents the
  separate 2020-12 class; [options](https://ajv.js.org/options.html) and
  [data modification](https://ajv.js.org/guide/modifying-data.html) define the
  switches explicitly disabled here; [formats](https://ajv.js.org/guide/formats.html)
  explains the separate format plugin.
- [Python jsonschema referencing](https://python-jsonschema.readthedocs.io/en/stable/referencing/)
  describes explicit immutable registries/resources; the no-retrieval policy is
  Nebula's design choice, not a claim about a library default.
- [Pydantic code generation](https://pydantic.dev/docs/validation/latest/integrations/dev-tools/datamodel_code_generator/),
  the [generator's JSON Schema documentation](https://datamodel-code-generator.koxudaxi.dev/jsonschema/)
  and [Pydantic serialization](https://pydantic.dev/docs/validation/latest/concepts/serialization/)
  support code generation and excluding unset fields. Source-schema gates and
  native compatibility are Nebula decisions, not inferred generator guarantees.
- [OpenAPI 3.1.0](https://spec.openapis.org/oas/v3.1.0.html) and the
  [FastAPI OpenAPI hook](https://fastapi.tiangolo.com/how-to/extending-openapi/)
  support the shared-definition snapshot integration.
- [Microsoft jsonc-parser](https://github.com/microsoft/node-jsonc-parser)
  documents scanner/visitor callbacks and strict parser options. Rejecting every
  parser error, duplicate key and unsupported numeric token is Nebula's policy.
