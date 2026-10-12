# Quality Engineer report

Verdict: PASS for the two planning-example defects.

## Reproduction and regression mapping

| Case | Evidence | Result |
|---|---|---|
| EX-PC-020: owned GL, missing/expired insured role | focused-regressions.txt, validation-tests.txt | Retained as owner with empty role, exact other rows preserved |
| EX-PC-020: non-owned auto, missing/expired insured role | same | Excluded; no ownership or insured status invented |
| EX-PC-021: closed account plus replacement | same, strict-rdf.txt | Conforms; both identity links and old policy ownership preserved |
| EX-PC-021: two current accounts | same | Rejected by OneAccountPerOrganizationShape |
| EX-PC-021: missing/unknown/conflicting status | same | Rejected at accountStatus |
| EX-PC-021: before/at closure, before/after recorded closure | temporal-final.txt | Old status and replacement selected by both timelines; post-closure graph conforms |

Artifacts above live in artifacts/test-results/. reproduction.txt captures the original three failures and two passing controls. focused-regressions.txt contains 12 passes. validation-tests.txt contains all 63 validation tests passing (51 prior tests plus 12 added cases). temporal-final.txt rechecks the four temporal cases after strengthening replacement-slot identity and retained-link assertions.

## Validation matrix

- Strict RDF: PASS, Python 3.12.13, rdflib 7.1.4, pyshacl 0.30.1, owlrl 7.1.4.
- Full product lifecycle: all four gates PASS in lifecycle-venv.txt: KG integrity, KG reproducibility, semantic examples, semantic RDF. An initial lifecycle command used system Python for its child commands and skipped optional RDF; lifecycle.txt preserves that attempt. The repeat explicitly prepended the product virtual environment and executed RDF successfully.
- Project and F0001 planning readiness: PASS with no findings; commands.log records invocations.
- Trackers: PASS with zero errors/warnings (trackers.txt).
- Stories: PASS (stories.txt); heuristics warn on existing unchanged story independence/value wording.
- KG drift/freshness: PASS; generated coverage metadata refreshed. Existing unused-edge and compile name-similarity warnings remain outside the changed semantics.
- git diff --check: PASS.

## Scope limits

These are synthetic development examples outside the frozen holdout. No production application, database, UI, authorization code or deployment changes were made, so runtime integration/E2E, security scans and runtime coverage measurement are not applicable (QE scope decision). No coverage percentage, independent-agent signoff, feature completion, production readiness or ADR acceptance is claimed. Python dependency deprecation warnings do not fail the executed tests.
