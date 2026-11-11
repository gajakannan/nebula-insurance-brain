# F0007 FactSlot model — Plan Review

## Decision

**CONDITIONALLY READY — 0 Critical, 2 High.** Fix both High findings before using this plan for renewed implementation, or record explicit operator risk acceptance with an owner and target date. No such new acceptance was supplied during this audit. No build-critical owner is missing.

Target: current archived package `planning-mds/features/archive/F0007-factslot-model`, at product commit `fa8fc1d`. Approved plan run: `2026-11-09-60865e32`; original planning range `bd10279..ff0a619`. This is a retrospective readiness audit of the archived package, including its as-built annotations. Completion defects are assessed separately in review run `2026-11-09-8b8456df`.

The `review-family` calculation is preserved in `artifacts/readiness-verdict.txt`. PR2 and the required product-local readiness check passed. Structural validation does not establish semantic correctness.

## Findings By Severity

### PR-H1 — High — The member-value invariant lacks an enforceable commit contract

- **Evidence:** `planning-mds/architecture/decisions/ADR-0077-factslot-identity-and-typed-answer-carriers.md:73` defines a MULTI member key from its canonical value/entity; line 117 does the same for normalized names. S0002 AC3, story line 24, requires value-derived member identity. ADR D5 at line 94 and the available assembly plan's “Answer Validation at the Existing Commit” sequence omit equality between a PRESENT answer's canonical member key and the immutable stored key.
- **Why this blocks an unqualified handoff:** The specified validation sequence can accept a new value B on the member identity of A. It neither names a mismatch rejection nor specifies the negative acceptance test. The completed code and even an HTTP acceptance test followed that incomplete sequence; the feature review demonstrates the consequence.
- **Repair:** State that PRESENT answers addressed to MEMBER slots must canonicalize to the stored member key under the pinned predicate contract. Define a named rejection and zero-write behavior, with entity/name/identifier mismatch tests and canonical-equivalence positives.
- **Owner:** Architect for contract/reason; Backend Developer and QE for implementation and proof. Resolve before renewed build/closeout. See `artifacts/code-review.md` and the sibling feature audit's `artifacts/code-member-identity-repro.txt`.

### PR-H2 — High — Planned identity CHECK accepts incomplete rows through SQL NULL semantics

- **Evidence:** available `feature-assembly-plan.md:186` through the identity CHECK, nullable columns at line 172 and unique index at line 201. The same expression is delivered in migration 0012 at line 75.
- **Counterexamples:** a v1 SINGLE SLOT with a NULL fingerprint; or a NULL identity version with populated v1 fields. In both cases the expression evaluates UNKNOWN, which PostgreSQL CHECK accepts. NULL fingerprints do not conflict in the identity index; a NULL version also bypasses the generated subject-KB association key.
- **Repair:** Require the complete legacy-or-v1 expression to be TRUE and explicitly constrain all mandatory v1 fields. Add direct-SQL negative cases for each missing mandatory field and partially populated legacy rows.
- **Owner:** Architect, Backend Developer, QE. Resolve before renewed build. Successful read-only PostgreSQL results and exact queries are in `artifacts/architect-postgres-raw.json`; explanation in `artifacts/architect-postgres-proof.md`.

These are two distinct planning defects. The same defects appearing in the completion review are not additional counts in this action. The assembly plan was inspected because it exists; this review does not require it as a new plan deliverable.

## Product Readiness

All six stories contain 39 concrete ACs, explicit entry points, authorization expectations, persistence evidence, dependencies and exclusions. The PRD explicitly justifies no UI/new route. All nine information states are enumerated: PRESENT plus eight non-value states. Money, scoped identifiers, legacy preservation, downstream ownership and rollback boundaries are stated. No new business rules were invented during review.

The plan explicitly hands temporal close and envelope database enforcement to F0008, schema publication to F0011, real predicates to F0012/F0013, producer adoption to F0016, display precedence to F0017/F0023, RLS and restriction re-derivation to F0018, and isolation proof to F0026. Those decisions are not omissions from F0007. Approval history resolves unambiguously to the approved planning run. The stale post-closeout README/PRD status text is recorded in the feature audit as FR-M4.

## Architecture Readiness

The design specifies slot/member/relationship identity, canonical qualifiers, predicate versioning, audit and authorization actions, absence-scope ownership, legacy behavior and the existing commit/read interfaces. Consequential choices are traceable to ADR-0077 and the governing ADRs. Proposed ADRs remain Proposed; operator design approval is not treated as formal architectural acceptance. The database shape guard needs PR-H2's correction, and the answer identity boundary needs PR-H1.

## Buildability Challenge

Backend, QE, Code Review, Security, DevOps and Architect responsibilities are identifiable; UI and AI exclusions are explicit. Package/file direction, existing interfaces, migration lineage and test layers are available. No missing-owner NOT READY override applies. The important gap is the missing negative member-consistency test; high line coverage would not establish that invariant. See the Code Reviewer and Architect lane notes under `artifacts/`.

### Required Brain review criteria

| Rule | Outcome | Feature-specific planning evidence |
|---|---|---|
| BRAIN-SCOPE | Pass | PRD Feature Statement, Included/Excluded Scope, all six story AC sections |
| BRAIN-AUTHORITY | Pass | PRD Risks & Assumptions; ADR-0077 Status/Design review/Formal acceptance |
| BRAIN-EVIDENCE | Pass | S0003 AC3/AC6; S0005 evidenced-name ACs; ADR-0077 D5/D6 |
| BRAIN-PARSE-ONCE | Not applicable to new parsing | PRD excludes ingestion/producer activation; existing artifact references are consumed, not reparsed |
| BRAIN-TEMPORAL | Pass within stated boundary | S0002 AC2/AC5 and S0006 AC1/AC6; ADR-0077 D4/D5; F0008 owns temporal close |
| BRAIN-AUTHORIZATION | Pass at contract level | PRD Role-Based Access; S0001 AC5/AC7, S0003 AC6, S0006 AC4/AC7; completion race is assessed separately |
| BRAIN-BUILDABILITY | High findings | PR-H1/PR-H2; all implementation/signoff owners otherwise identifiable |
| BRAIN-EXAMPLES | Pass for planning artifacts | worked-examples.md, contract-examples.json, EX-OWN-003 and EX-SEM-008 references; structured example validator passes |

## Validation Evidence

PR2 ran through the framework gate driver, including the required local extension check. All six framework validators passed: approval history, archived story files, trackers, KG integrity, KG drift, and templates. The local `plan-readiness` check passed. Evidence: `artifacts/pr2.txt`, `artifacts/plan-approvals.txt`, `artifacts/story-validation.txt`, `artifacts/tracker-validation.txt`, `artifacts/project-plain-kg.txt`, `artifacts/kg-check.txt`, `artifacts/template-validation.txt`, `artifacts/local-plan-check.txt`, `gate-state.json`, and `lifecycle-gates.log`.

KG emits warnings for unused edge types and dangling references in F0006 assertion symbols. They are not validation failures or proof of a new F0007 regression. No graph repair was made. Semantic example checks pass but expressly do not execute runtime behavior.

PR3 self-review verified exact source/contract references and reconciled duplicate role observations. PR4 uses the severity computation, not the procedural driver's generic PASS. No plan, source, tracker, graph, approval or original feature evidence was edited.

## Artifact Trace

Read: archived F0007 PRD, stories, checklist, examples, STATUS, GETTING-STARTED, existing assembly plan; governing ADR-0077, schemas, blueprint and local review checklist; plan approval index/history; KG routing and raw implementation counterexamples as corroboration. Role notes: `artifacts/architect-review.md`, `artifacts/code-review.md`. Exact query/command evidence is cited above. Full command telemetry is in `commands.log`; the base `artifact-trace.md` records the boundary and created outputs.
