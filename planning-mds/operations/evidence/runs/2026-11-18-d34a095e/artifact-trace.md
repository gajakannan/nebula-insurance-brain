# Artifact Trace

## Inputs

- Product context: artifacts/review/product-context.txt.
- Canonical manifest and latest pointer: paths in action-context.md.
- Raw changed files: artifacts/diffs/changed-files.txt.
- Initial protected artifact hashes: artifacts/review/initial-canonical-hashes.json.

## Outputs

This review run only. Individual role reports record exact raw source and evidence paths; commands.log records reads and validator outputs.

## Final review trace

- Role-owned section: artifacts/review/product-manager.md; SHA-256 ce962687845e1ad516ddd919eedc3bdd41749a15a397ab828b01cc8805ab749f. Exact raw paths are in that section and the compiled report.
- Role-owned section: artifacts/review/architect.md; SHA-256 a29f76796cbff5e649ef9c5c61bc54225ffa279678a3e91c6a8ea292042b214e. Exact raw paths are in that section and the compiled report.
- Role-owned section: artifacts/review/quality-engineer.md; SHA-256 d27fb4fa0ae884d9bdbf1222c62ca6232d1c8565890336d4c9775b3440ee8c5d. Exact raw paths are in that section and the compiled report.
- Role-owned section: artifacts/review/code-reviewer.md; SHA-256 af6471d5ed40fdde04248012170ff5bcd5789dddb844bb7ab0e6d0d189d0baad. Exact raw paths are in that section and the compiled report.
- Role-owned section: artifacts/review/security.md; SHA-256 baf2b8ca9c156a7ec2d6121ca33b2c3b5d40ff1fc45f224beb7ffd258e19994a. Exact raw paths are in that section and the compiled report.
- Role-owned section: artifacts/review/devops.md; SHA-256 99c888b14105f0b5e25f8fb62650baa6bb7296927c89d644f421dec4b3a0a74c. Exact raw paths are in that section and the compiled report.

Required validator operation records: artifacts/test-results/fr2-operation-results.json. Story currency and explicit-root tracker output: artifacts/test-results/fr2-story-index-currency.json and fr2-explicit-trackers.txt. Policy: artifacts/test-results/fr4-policy.json. Protected inputs: artifacts/review/initial-canonical-hashes.json and protected-input-check.json. Canonical files unchanged.

Temporary diagnostic/orchestration scripts preserved under artifacts/review/scripts/: f0008_assemble_review_d34a095e.py, f0008_bootstrap_telemetry_d34a095e.py, f0008_close_review_d34a095e.py, f0008_code_routing_d34a095e.py, f0008_finalize_validation_d34a095e.py, f0008_pm_checks_d34a095e.py, f0008_qe_probe_d34a095e.py, f0008_response_probe_d34a095e.py, f0008_review_exec_d34a095e.py, f0008_review_setup_d34a095e.py, f0008_security_probe_d34a095e.py, f0008_story_currency_d34a095e.py.

Framework limitation: run-gate retained operation exit/completion records but not validator stdout; no raw stdout transcript is claimed. Original cwd-placeholder rows are preserved in artifacts/review/gate-runtime-cwd-original.jsonl and expanded transparently in this run log. Pre-setup bootstrap records disclose recording-time limits. These are audit trace limits, not F0008 feature defects.
