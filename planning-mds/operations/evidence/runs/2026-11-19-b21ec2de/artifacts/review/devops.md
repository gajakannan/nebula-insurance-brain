### Deployability — DevOps

Reviewer: Codex, independent DevOps lane. Product root `/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain`; canonical feature run `2026-11-18-bce4909b`; HEAD `3290d17750b62d70b9130ac9010d096a584eead5`. DevOps is required because remediation adds migration 0015 and full F0008 still includes migration 0014 and CI changes.

**Deployability result: PASS for the declared local-development runtime. No new critical/high/medium/low DevOps finding.** The framework pin update below is an explicit pending follow-up, not evidence of failure in the current closeout. Security owns the new commit-response disclosure concern.

#### Current evidence checks

| Check | Disposition and raw evidence |
|---|---|
| Current preflight | Raw `planning-mds/operations/evidence/runs/2026-11-18-bce4909b/artifacts/test-results/g1-runtime-probe.txt` records `brain-postgres:18-pgvector-age` healthy, PostgreSQL 18.6, schema 0015 and btree_gist 1.8. The cited preflight keeps the original locked engine/Python plus Compose PostgreSQL topology and explicitly leaves shared development DB at 0010. |
| Fresh database upgrade | Read raw `.../artifacts/test-results/command-output/fresh-db-upgrade-head.txt`: transactional DDL applies 0001 through 0015 and logs the installed same-slot guard. This is actual execution output, not only the deployability verdict. |
| Migration 0015 behavior | `engine/migrations/versions/0015_f0008_split_lineage_same_slot.py:23` declares revision 0015/down_revision 0014. `:35` is SECURITY INVOKER with pinned search_path; `:38` checks same-slot ancestry; `:54` locks then refuses existing cross-slot rows, naming samples. `:77` drops only its added trigger and function. No table, new privilege, new secret or data rewrite is introduced. |
| Migration-cycle and refusal proof | Read source `engine/tests/integration/test_temporal_migration.py:273`: install refusal leaves snapshot and revision 0014 unchanged; after test-only fixture cleanup, upgrade/downgrade/upgrade removes only the 0015 trigger and retains 0014's insert guard. The raw new-run JUnit marks this test passing. Migration 0014's original guarded rollback policy is retained. |
| Full regression | The current raw `.../artifacts/test-results/full-engine-regression.xml` contains 1085 tests with no failure/error/skip, including the same-slot direct-insert negative and 0015 preflight/cycle case. `artifacts/review/architect-remediation-runtime.json` records the exact parsed suite and selected outcomes. No current HTTP mixed-authority predecessor-response test is present; that is Security's newly identified gap. |
| CI scope | Existing `.github/workflows/ci-gates.yml:214` already runs the changed temporal unit, commit, immutability, concurrency, read and migration files against owned PostgreSQL databases with a >=80% brain_temporal floor. Runtime setup still applies fresh migrations to head. The remediation adds no unrelated workflow, dependency, environment variable, service, port or container. |
| Prior DevOps findings | The prior independent DevOps lane had no feature-blocking finding. Fresh 0015 and current raw runtime evidence were checked independently, rather than carrying forward the old PASS. |

#### Framework pin follow-up — owner: DevOps

The product still pins framework `d90bbb6fc70dffcfa6d70379d42015e895a49fa0` in `planning-mds/BLUEPRINT.md:33` and `.github/workflows/ci-gates.yml:323`. Current closeout `pm-closeout.md:24` explicitly defers a coordinated update until framework PR #101 merges. During this audit a logged local framework read observed merged commit `840e724` (`fix(validator): accept G6/G7 reentry candidates while latest-run names the prior approval (#101)`), following d90. The parent records the exact revision used by fresh FR2 validation; this lane did not update or merge framework code.

Inspected the actual d90→840e724 validator diff. The change adds reentry-candidate recognition only in the `resolve_run` branch for **G6/G7**; closeout behavior is unchanged. Product CI at `.github/workflows/ci-gates.yml:334` invokes registry-wide feature validation with its default **closeout** stage. Therefore the old pin does not by itself make this completed feature's current closeout/CI invalid. It does lack the corrected pre-G8 reentry-candidate behavior for future remediation. The explicit remaining task is to advance BLUEPRINT and CI pins together through DevOps ownership. No remote merge or product repair is required to finish this read-only audit.

#### Other pending, bounded follow-ups

- F0011 must number its future migration after 0015; current `pm-closeout.md:23` and the remediation assembly plan record that coordination.
- The local superuser application role remains SEC-F8-02, an explicitly accepted low boundary assigned to F0018, now present in F0018's README/KG handoff. Its production qualification is not established by this feature.
- PostgreSQL/Python timezone-data pinning remains the prior documented follow-up (`pm-closeout.md:25`); the current preflight explicitly cites the unchanged recorded versions from the original proof rather than claiming newly pinned data.
- Production hosting remains F0026 scope. No production deployment or rollout approval is inferred from local deployability.

#### FR3 self-review and limits

Checked the exact migration/workflow source and manifest-cited raw preflight/upgrade/JUnit artifacts. No runtime restart, database mutation, new test suite execution or publication was performed. No canonical evidence, implementation, tests, feature docs, trackers, config or KG was changed. No new frontend/model-runtime lane is needed because remediation introduces no such surface. All shell reads used this review's telemetry wrapper. Fresh validator outcomes and substantive security findings must be combined by the parent before the overall done verdict.
