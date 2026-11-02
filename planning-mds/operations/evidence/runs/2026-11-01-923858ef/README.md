# Plan Review — F0006 — run 2026-11-01-923858ef

**Verdict: CONDITIONALLY READY** (critical 0, high 1, medium 1, low 2, info 1). See plan-review-report.md.

Open follow-ups (repair owners: plan.md / targeted rework; not this review):

1. AR-1 (High, Architect): define the `interpretation_basis` rule for v2 review corrections. The live code hard-codes EXPLICIT (S0001 AC4). Decide whether the v1 path keeps that as a legacy boundary.
2. AR-2 (Medium, Architect): define the raw/admission hashes and evidence rows for a v2 correction child, and the `subject_type` mapping for the v2 carrier.
3. PR-1 (Low, PM): state that DESCRIBED_EVIDENCE is a reason code carried on a PROVENANCE_CORRECTION item.
4. CR-1 (Low, Code Reviewer): decide at feature G0 whether AI Engineer signoff is required.

Before feature.md: fix AR-1, or record operator risk acceptance with an owner and a target date.
