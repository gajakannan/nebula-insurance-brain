# Architect implementation review — F0004 run 2026-10-17-8a6cc79f

Reviewer: Codex, Architect role. Date: 2026-10-21. G4 was explicitly approved by
the user; the ordered G4 validator passed before these G5 signoffs.

## Scope and source precedence

Reviewed the approved assembly plan, four stories and frozen contracts against
the as-built changes and final independent Code/Security reports. The product's
Python/FastAPI/SQLAlchemy boundary governs the illustrative framework examples.
The changed-file inventory is artifacts/diffs/changed-files.txt.

## Story assessment

| Story | Architectural result | Concrete evidence |
|---|---|---|
| F0004-S0001 | PASS: strict shared verification, immutable manifest-last publication, exact retry and source reuse; existing queue fence and current-authority transaction retained | test-execution-report.md; code-review-report.md |
| F0004-S0002 | PASS: positive producer observations and native hierarchy; origin/geometry/table constraints; persisted table/cell/continuation ownership | step1a-provenance-spike.md; test-execution-report.md; code-review-report.md |
| F0004-S0003 | PASS: candidates outside parse hashes; trusted source/human ports default deny; explicit selection/clear/CAS/history and shared-lock read consistency | test-execution-report.md; code-review-report.md |
| F0004-S0004 | PASS: trusted owner plus current authority before payload, strict legacy/v2 dispatch, explicit operator repair, versioned consumer output and isolated restore | security-review-report.md; deployability-check.md; test-execution-report.md |

## Boundary and refinement review

Shared content models and verification do not import Docling, FastAPI or
SQLAlchemy. Only the neuron adapter projects the pinned native document.
Persistence participates in caller-owned transactions. Revision 0008 preserves
0001–0007 and nullable legacy metadata; global cardinality reconciliation is an
explicit quiesced operator action, not an implicit read or migration side effect.

The fenced worker keeps the original lease resource for fallback, independently
authorizes the deterministic actual artifact, verifies both identities and
stores a hash-bound private diagnostic intent before marker/readiness recovery.
That receipt supplies no authorization. Concurrent source submissions serialize
in a submitter-only namespace without changing the worker lock order.

The date facade protects every command with current authority. Producer
receipts bind exact source/version/value/precision; a schema-valid DTO or SHA
cannot stand in for human authority. Reads hold the version FOR SHARE through
audit commit; writers use FOR UPDATE in the same order. Processing timestamps
remain separate, and the June example does not create canonical intervals.

The initial PDF signature check closes the independently reproduced archive
pre-detection path before either parser in both modes. It retains the approved
PDF-only surface and positive native/OCR provenance proofs. Observed engine and
package version with paired null model fields meet Step 1a; exact OCR weight
identity remains an explicit future qualification recommendation.

Quiesced local backup is an inventory-checked DB/bytes snapshot, not a
cross-store distributed transaction. Restore owns fresh targets and verifies
all required bytes/index/date/audit/citation lineage before reporting success.
No production promotion occurs. The actual direct Graph ledger remains
partial/unresolved when it omits native references; a controlled ledger proves
exact-span translation without changing that observed limitation.

## Validation and acceptance limits

Final runtime evidence: engine 229 pass, neuron 93 pass with four optional live
inference/tokenizer skips, actual restore four pass. All 25 ACs are mapped and
assessed in test-plan.md and code-review-report.md. Current changed runtime
coverage is 2371/2617 = 90.60%, all layers above 80%. No High/Critical code or
security finding remains after independently verified corrections.

G5 covers this implementation/contract review. Authored runtime KG bindings,
symbols/callers and decision reconciliation remain the ordered G7 obligation;
they are not claimed complete here. The default-false v2 writer, default-deny
human/source verifiers and production Graph limits remain. ADR-0073 and broader
Proposed ADRs remain Proposed; G4 is not their acceptance or production rollout.

## Result

PASS

Architect signs off all four stories for the bounded approved implementation.
The Security and Code Reviewer recommendations remain owned and are carried to
PM closeout; graph reconciliation must pass G7 before closeout.
