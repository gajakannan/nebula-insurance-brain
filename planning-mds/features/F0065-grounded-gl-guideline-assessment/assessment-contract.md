# F0065 assessment contract

**Status:** Proposed design contract, 2026-09-07; proof and architecture acceptance tracked by ADR-0056. Vocabulary below is the v0.1 planning baseline; production DTO/schema bindings remain a feature implementation prerequisite.

## Representation boundaries

An ontology concept defines a kind of thing; an entity is a specific policy, coverage, or assessment subject. Assertions state what a source or model claims. Canonical facts state what the Brain has accepted. A rule defines a scoped operation. An assessment records its application to exact inputs. An embedding is a separately versioned retrieval projection. These records link by identifiers; a combined JSON response is a read view, not a second store of truth.

`requiresProof` may denote a requirement, while `supportedBy` links an assertion to actual evidence. Neither edge demonstrates that the requirement has been satisfied. A free-form `logic_rules` string is documentation until parsed into a supported, validated rule definition. Model confidence belongs to a particular interpretation; similarity, extraction confidence, source authority, and assessment status must not share one score.

## Rule definition and release

Required fields: `rule_id`, immutable `version`, `ontology_release`, `guideline_source_ref`, approved `authority_ref`, tenant/knowledge-base scope, effective interval, coverage type, limit basis, currency, operation, and decimal minimum. The only v0.1 operation is `money_gte_minimum`: input amount greater than or equal to the minimum. Required fields and scope checks form fixed preconditions, not a general expression language. Negative or malformed monetary values and empty intervals are rejected; no implicit currency conversion or cross-basis comparison occurs.

The rule release is a reviewed asset installed by an authorized administrator with an audit record. Callers select a rule identity/version; they cannot supply authority, tenant grants, executable strings, or an unapproved threshold in an assessment request. No Ontology Workbench is required. A changed minimum produces a new immutable release. The service verifies that the selected release was available at `known_as_of` and effective at `valid_as_of`; applying a newer rule to an earlier knowledge snapshot is a future scenario operation, not a historical assessment.

## Request and snapshot

The authenticated request identifies the policy term/coverage, rule/version, `valid_as_of`, and `known_as_of`. A “current” request resolves explicit coordinates and a consistent semantic snapshot once at request start and echoes them. Current means that snapshot, not a claim about facts accepted after it. The server resolves tenant, knowledge-base membership, principal, grants, rule authority, and source applicability; client fields never establish permissions.

Read accepted facts, conflict/completeness state, rule release, and provenance from that snapshot. Resolve coverage basis, currency, policy term, and applicability before comparison. No nearest-neighbor subset or model-generated value substitutes for missing canonical data.

## Outcomes and errors

Apply the following order; invalid request/rule definitions and authorization failures occur before any business outcome is disclosed.

| Condition | Outcome | Comparison |
|---|---|---|
| Required request/definition malformed, unsupported operation, or unavailable rule release | Typed request/configuration error | None; no successful assessment |
| Principal lacks permission for the subject, rule, relevant inputs, or evidence lineage | Access error under the existing resource contract | None disclosed; no revealing missingness reason |
| Known subject/scope falls outside the rule, or supplied canonical limit has a different basis/currency | `NOT_APPLICABLE` with an authorized reason | None |
| Relevant unresolved conflict exists at the snapshot | `CONFLICT` | None; do not choose highest confidence |
| Required amount, qualifier, applicability, or evidence is unknown/incomplete; no accepted input exists | `UNKNOWN` | None; missing does not mean false or zero |
| Complete applicable inputs and amount >= minimum | `MEETS_GUIDELINE` | Exact decimal comparison |
| Complete applicable inputs and amount < minimum | `BELOW_GUIDELINE` | Exact decimal comparison |

An explicit negative assertion is knowledge with provenance; it is not an extraction failure. For this monetary rule, an explicitly absent applicable coverage is `NOT_APPLICABLE` with its supported reason. A failed page or unknown coverage presence is `UNKNOWN`. A retracted fact has no usable current value and yields `UNKNOWN` unless another accepted value applies. None of these outcomes approves or rejects the policy itself.

## Assessment record

Persist `assessment_id`, subject/scope, outcome and reason codes, exact input fact-version IDs, rule ID/version and source reference, ontology release, evaluator version, semantic snapshot, valid/known coordinates, creation time, acting principal, audit reference, derivation/evidence references, and the typed comparison for evaluated outcomes. Preserve supporting assertion and interpretation-run links through existing provenance. Unknown/conflict results retain authorized gap/conflict references and snapshot context, not invented input facts.

The record is append-only, tenant/knowledge-base scoped, and outside canonical facts. Its derivation uses exact input versions consistent with ADR-0026. Promoting a result to canonical knowledge would require the canonical commit contract and is outside F0065. Do not describe stored explanations as private model reasoning traces; show values, rule, calculations, evidence, and recorded reasons.

## Freshness, concurrency, and history

v0.1 always recomputes on demand from the requested snapshot; no cross-request assessment-result cache is required. Historical records are shown only with their original coordinates and versions. A current request resolves a new snapshot, including changed inputs and the selected applicable rule release. A concurrent canonical commit cannot mix pre-change and post-change fact versions within one assessment. A failed persistence operation returns an error rather than a successful saved result; retries with the same idempotency key and identical request/snapshot do not duplicate a record. Reusing a key with different content is rejected.

An endorsement accepted July 10 but effective July 1 changes the July 5 assessment when `known_as_of` is July 11, while July 5 as known July 8 retains the earlier value. This is historical reconstruction from stored facts/rules, not re-running the extraction model. General dependency propagation, invalidation workers, arbitrary derivation chains, and the full Decision Ledger remain F0056–F0058.

## Authorization and audit

Use current permissions on every assessment and historical record read. Access to a policy entity alone does not grant access to every supporting document or derived result. For v0.1, require permission to the complete relevant input/evidence lineage before returning an assessment; do not partially disclose an outcome supported by inaccessible evidence. Revocation must cover result, title, count, explanation, citations, and any transport cache. Historical queries never restore historical grants.

Assessment creation records the acting principal, rule release, request/snapshot, and outcome in the existing audit boundary; rule installation and access denials use existing audit controls. An explanation panel and its evidence requests apply the same authorization. No request or model output supplies its own approval authority.

## Proof obligations

Before freezing runtime DTOs, the architect/backend owner demonstrates exact-decimal boundaries, the outcome/error table, immutable lineage, a concurrent snapshot, retroactive endorsement, changed rule release, idempotency, and revocation. QA maps cases in the worked example to executable assertions. Security review checks derived-result visibility. End-to-end extraction and rule integration belongs to F0024/F0025; F0026 owns frozen evaluation and release gates.
