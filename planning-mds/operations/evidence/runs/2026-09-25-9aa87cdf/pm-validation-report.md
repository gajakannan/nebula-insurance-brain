# PM Validation Report — validate run 2026-09-25-9aa87cdf

**Scope:** `all` (requirements lane). **Subject:** branch `docs/utopia-evolution` at `b1f4357` against `main` at `93cc8c1`.
**Role:** Product Manager. **Framework:** `nebula-agents` at the pinned commit `c218bf1`.

This lane checks that the requirement-side changes keep the trackers, feature folders, and blueprint consistent. The changes are feature README scope amendments, the F0066 reservation, the BLUEPRINT §3.3/§4.7/§4.11/§5 edits, the glossary, and the examples. It also checks that the changes introduce no unowned or untestable requirements.

## Completeness

- **BLUEPRINT.md Section 3.** §3.3 lists F0066 under v0.2B with its ADR. The inventory sentence now names F0065 and F0066 as additions to the section 95 roadmap. §3.4, §3.4.1 and §3.5 are unchanged and still accurate.
- **Section 4.** §4.7 now covers the ADR range through 0069. §4.11 records the amendment, its v0.1 impact, and the F0002 non-change.
- **F0066.** The folder exists with a README of overview, scope, out of scope, documents, and stories. There is no PRD, STATUS, GETTING-STARTED, or story, which matches the other reserved features: the `plan` action authors those in Phase A/B.
- **Placeholders.** No TODO or placeholder text was introduced (checked over `artifacts/diffs/added-markdown-lines.md`).

## Vision & Non-Goals

- **Vision is unchanged.** The amendment refines how the Brain reads, dates, and governs knowledge. It does not change what the Brain is (master blueprint §0–§2).
- **Non-goals are strengthened, not weakened:**
  - no ontology in extraction prompts;
  - no model-computed dates;
  - no automation on by default;
  - no exactly-once external execution claimed.
- **Success measures** are stated per ADR as proof gates, and are aggregated in `testing/evaluation-strategy.md`.

## Personas

- No persona file changed.
- **F0066's README does not name its primary persona.** Likely candidates are underwriter and ontology steward. See P-3.
- The amended v0.1 features keep their existing persona context.

## Feature Traceability

| Change | Traces to | Status |
|---|---|---|
| ADR-0063 open statements, alignment | Operator decision 2026-09-25 (accepted direction); F0006 storage (v0.1A), F0014 route (v0.1A), F0066 (v0.2B), F0029/F0030/F0032/F0043 | Traceable |
| ADR-0064 time interpretation | Section 87 endorsement acceptance; F0004/F0008/F0012/F0013/F0016/F0019/F0022/F0025/F0026 | Traceable; see P-1 |
| ADR-0065 admission, origin, mood | Section 107.4 missingness; section 108.2 precision; F0004/F0006/F0015/F0016/F0022/F0026/F0052 | Traceable; F0005 gap noted in architect A-4 |
| ADR-0066 names | Section 53; F0007/F0013/F0017/F0023/F0027 | Traceable |
| ADR-0067 automation | Sections 64, 75; F0022/F0027/F0037/F0043/F0057/F0059 | Traceable |
| ADR-0068 basis | Sections 29, 56; F0016/F0027/F0032/F0056/F0065/F0066 | Traceable; F0065 contract gap noted in architect A-3 |
| ADR-0069 action attempts | Sections 62, 64; F0047/F0050/F0059 | Traceable |

Trackers:

- **REGISTRY.md and ROADMAP.md** generated regions include F0066 (Planned, Later, v0.2B). ROADMAP's authored "Last Reviewed" line is updated.
- **STORY-INDEX.md** is unchanged; the `v1-story-index` operation made no diff.
- **`validate-trackers.py`** reports 0 errors and 0 warnings (`artifacts/test-results/validate-trackers.txt`).

## Story Testability

- **No story was added or changed.** Every new requirement is in feature README scope amendments, to be converted to stories by each feature's `plan` run. Carrying amendments forward this way is the pattern the 2026-09-07 (F0065) and 2026-09-15 (ADR-0060) amendments set.
- **Existing stories:** 23 pass. The 10 with warnings are all pre-existing and outside this change: archived F0001 stories, F0002-S0003/S0006, and F0065-S0001. See `artifacts/test-results/validate-stories.txt`.

## Acceptance Criteria

- Each ADR has explicit proof gates with fixtures.
- Measurable thresholds are stated where the domain allows:
  - open-statement not-stated rate ≤ 2%;
  - time normalization starting points of 95% (absolute) and 85% (anchored);
  - a revert fuse of 2 reverts in 7 days.
- Thresholds that need named reviewers and baselines are explicitly routed to F0026 rather than invented.
- **Vague-language lint** over all added markdown lines (`artifacts/test-results/vague-language-added-lines.txt`, exit 1) found two uses of "should", both in ADR Context prose describing the current state: ADR-0065 line 20 and ADR-0067 line 17. Neither is a requirement. See P-4.

## Findings

| ID | Severity | Artifact | Finding | Owner / action |
|---|---|---|---|---|
| P-1 | Medium | `features/F0025-endorsement-bitemporal-slice/README.md` amendment | v0.1B acceptance (F0025) now requires ADR-0064 behaviour: time mentions, grade-C handling, unknown ends. ADR-0064 is still Proposed, so v0.1 acceptance depends on a Proposed decision. | PM + Architect: either get ADR-0064 through its proof gates before F0025's plan run, or record in F0025's plan a fallback where valid time comes from the template's effective-date field while time-mention storage lands. The operator decides at V3 or at F0025 planning. |
| P-2 | Medium | BLUEPRINT §4.11; amendments to v0.1A features | The v0.1A scope grows in F0004, F0006, F0007, F0008, F0014, F0016, F0017, F0019, F0022, F0025, and F0026. The additions are storage and contract changes the operator authorized; they are recorded, not hidden. They still widen v0.1 after two earlier amendments. | PM: confirm at each feature's Phase A that only the storage and contract hooks enter v0.1, and that behavioural work (alignment, automation, fingerprint-driven scheduling) stays in v0.2+. |
| P-3 | Low | `features/F0066-open-statement-extraction-and-signature-alignment/README.md` | No primary persona or user outcome statement. | PM: add at F0066 Phase A. |
| P-4 | Low | ADR-0065 line 20, ADR-0067 line 17 | Two uses of "should" in Context prose. They are not requirements, but the contract lint flags them. | Architect: reword to "must not be able to" and "is meant to consult", or add a `vague-ok` marker. |
| P-5 | Info | `features/ROADMAP.md` | The authored "Last Reviewed" line was edited by hand. That is authored prose outside the generated region, which is allowed. | None. |

No Critical or High findings.

## Result

**PASS WITH RECOMMENDATIONS.** The trackers are fresh, the feature inventory and blueprint agree, and every new requirement is owned and traceable. P-1 is the one decision the operator is asked to make.
