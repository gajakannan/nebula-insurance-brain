# F0006 G4 Approval Brief

Run: `2026-11-02-5a00b0ff`. NEBULA_PRODUCT_ROOT: `/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain`.
Operator decision: **APPROVED with SEC-01 local-only mitigation**, recorded 2026-11-04T02:37:42.390119+00:00.
G0 through G8 passed; the approved local feature completion is archived and published.

## Delivered Scope

All five stories and 35 acceptance criteria have observed proof. The additive
assertion v2 contracts/storage preserve typed/open claims, independent basis/origin/
mode/confidence and immutable evidence. Structural admission derives locations from
retained content. Current read, review and commit paths enforce source authority and
eligibility. New producers, routes, UI, grants, extraction/default activation and
broader F0016/F0018 orchestration remain outside this approved feature scope.

## Evidence

| Assessment | Current result |
|---|---|
| Product acceptance | 35/35 ACs mapped; 306 engine, 15 importer, ten SQLite/PG recovery and five existing content-worker cases passed (336 unique cases across final lanes) |
| Additional review probes | 25 focused authority/consumer, 17 migration cases overlap final engine suite; two explicit basis-boundary probes also passed |
| Changed-code coverage | 1170/1266 executable changed production lines, 92.4171%; 20 production files, no instrumentation gaps |
| Code review | APPROVED; zero open Code Reviewer findings |
| Architect review | PASS; both implementation findings resolved; independent second review recorded |
| Security review | PASS WITH RECOMMENDATIONS; zero Critical, one High, one Medium, one Low; SEC-05 resolved at G7 |
| Runtime/deployment | Locked non-root images match reviewed sources without source bind mounts; healthy current runtime, migration0011 guard and unchanged defaults verified |
| Scans | Final secrets/SAST clean; dependency findings retained; anonymous OpenAPI ZAP has no failing rules and one Low header warning |

Canonical evidence: [QE](test-execution-report.md), [coverage](coverage-report.md),
[Code Reviewer](code-review-report.md), [Architect](architect-implementation-review.md),
[Security Reviewer](security-review-report.md), [DevOps](deployability-check.md).
The final engine suite is [g3-sec04-regression.xml](artifacts/test-results/g3-sec04-regression.xml).

A-IMPL-01 (High page/bbox carrier integrity) and SEC-04/A-IMPL-02 (Medium
pre-READ payload materialization) are repaired and independently re-reviewed.
Historical failed/retried commands remain in the evidence; they are not described
as passing. The strict global security-planning audit failed and is carried as SEC-02.

## Severity Policy and Original G4 Proposal (historical)

The actual [standard policy result](artifacts/test-results/command-output/g4-severity-policy.log)
is **WARNING**, critical=0/high=1. Allowed options are **fix issues**, **approve with
justification**, or **reject**. Approval requires explicit mitigation justification.

**SEC-01 High, inherited conversion dependency/PDF memory risk.** Accepted PDF input
can reach vulnerable parser paths. Existing deadlines do not provide effective memory
containment. External dependency versions are unchanged by F0006; the risk is retained,
not called clean. Proposed mitigation: accept only the reviewed local, trusted synthetic
fixture feature completion; preserve the existing pipeline/writer defaults and authorize
no broader production/untrusted deployment or new producer activation. Parser/dependency
remediation, resource isolation and qualification are prerequisites to that broader
exposure. Proposed owners: AI Engineer + DevOps, with Security verification; target
2026-11-10 and before production/untrusted shared conversion. This text was the G4 proposal; the operator subsequently approved it, and the PM acceptance is recorded in gate-decisions.md and pm-closeout.md. It remains no dependency waiver or production activation.

Other proposed follow-ups are SEC-02 (Medium global planning security documents;
Security + Architect, target2026-11-10/before production qualification), SEC-03 (Low
nosniff hardening; Backend + DevOps, target2026-11-17), and SEC-05 (Low KG caller-map
coverage; Architect, required G7 reconciliation or precise static-analysis limitation).
Their exact evidence, scope and proposed dispositions remain in the Security report.

## Next Required Gates

All required feature gates G0-G8 have now passed. The PM archive and approved-run pointer are recorded in [pm-closeout.md](pm-closeout.md), evidence-manifest.json and gate-state.json. The original decision package below is historical to G4; accepted recommendations are explicitly mirrored in pm-closeout.md. This completion grants no broader producer/production activation or primary-owner PR/merge acknowledgement.

