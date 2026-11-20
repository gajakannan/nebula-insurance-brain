# Artifact Trace

Inputs: product-context.txt, latest-run.json and selected evidence-manifest.json, prior findings, exact current diffs. Role-owned sections cite raw paths. All outputs confined to this run and /tmp; protected-input-hashes.json tracks canonical file integrity.

## Final role evidence

- artifacts/review/product-manager.md; SHA-256 d899049b76dc11bef0b6f41d43d5d8eb8a570587ac160f986f04797a10d3b8cf; exact raw citations and limits in that owned section.
- artifacts/review/architect.md; SHA-256 7651b015eb834b9eba486bce5de8c425d636cbc88db1e4614b66d72755fb7ef2; exact raw citations and limits in that owned section.
- artifacts/review/quality-engineer.md; SHA-256 c34b7f8689cfcfaf7bcfb754ae3bfa843d077ca876b6c4d2f6d87bfaec135ec7; exact raw citations and limits in that owned section.
- artifacts/review/code-reviewer.md; SHA-256 24877fab4d9ecf49fa5e6398e811395ae41df00963bc4cdb866ebc6b3e72ba9a; exact raw citations and limits in that owned section.
- artifacts/review/security.md; SHA-256 2f4f828315dae336f05d739359b4cb1625235f5aabe04122a2af60546c9ccbba; exact raw citations and limits in that owned section.
- artifacts/review/devops.md; SHA-256 09df1ebc6e976e1a196f5978cd6edef4ea2d0e8e769c3e5f17ae6bc1ab4f91c1; exact raw citations and limits in that owned section.

Validator stdout/stderr/result metadata: artifacts/validators/. Mandatory summary: artifacts/test-results/fr2-summary.json. Policy: artifacts/test-results/fr4-policy.json. Integrity: protected-input-check.json and merge-tree-equivalence.json. Diagnostic/orchestration scripts retained in artifacts/review/scripts/: f0008_gate_capture_b21ec2de.py, f0008_pm_review2_b21ec2de.py, f0008_qe2_probe_b21ec2de.py, f0008_review2_close_b21ec2de.py, f0008_review2_exec_b21ec2de.py, f0008_review2_report_b21ec2de.py, f0008_review2_setup_b21ec2de.py, f0008_review2_validation_b21ec2de.py, f0008_story_currency_b21ec2de.py.

No actual runtime authorization probe was performed. Automated cybersecurity safeguards prevented the proposed verification; the safer source-only review completed, with remaining verification explicitly pending. Gate stream capture uses the supported runtime API; no framework source was edited. Bootstrap discovery was recorded retrospectively and gate cwd originals are preserved in gate-cwd-original.jsonl.
