# Errata for superseded run 2026-11-18-bce4909b

- Recorded by: Claude (Opus 5.5) / Product Manager
- Date: 2026-11-19
- Basis: review `2026-11-19-b21ec2de`
- Result: PASS

The superseded run's files are not rewritten; these corrections apply when reading them.

| ID | Prior statement | Correction |
|---|---|---|
| SEC-F8-NEW-01 | `security-review-report.md` judged the commit-response disclosure PASS: remainders repeat their predecessor's attestation and "belong to the same slot, under the same commit authorization" | Incorrect. Commit authority is not READ authority over the predecessor's documents, so a committer could learn the date of a document it could not read. Fixed in run `2026-11-19-8cfcd0ff`. |
| PM2-L1 | `evidence-manifest.json` `changed_paths` | Whitespace-splitting broke the four filenames containing a space (`command-output/ci-nodb-gate-brain_* <package>/tests.txt`) into nonexistent entries. The real files exist and are the superseded, mislabeled no-DB gate runs. |
| QE2-L1 | `g1-runtime-preflight.md` probes support the regression | The probe (`commands.log` line 4) was recorded after `full-engine-regression.txt` had started. The runtime was healthy throughout, but the recorded order is preflight-after-start. This run records the preflight first. |
| R2-ARCH-L1 | The assembly plan (lines 48 and 343) and the `commit.py` docstring said remainders copy "four timestamps" | They copy the three source timestamps and take the new `canonical_accepted_at`. Corrected in this run. |
| PM2-L2 | STATUS `**Feature Run:**` and BLUEPRINT section 3.3 F0008 entry | They still named the first run and "Planned". Corrected in this run. |
