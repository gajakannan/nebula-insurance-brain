# Bootstrap telemetry provenance

The 23 commands listed by /tmp/f0011_review_bootstrap.py ran before the review command wrapper was installed. They were appended retrospectively from the tool transcript. Their timestamp is the append time, not a reconstructed execution time. Exit codes are the observed tool results. No command was re-executed to manufacture setup history. Later command records use execution-start timestamps and retain captured output artifacts.

The initial resolver failed because the session started in the common parent rather than the framework checkout. Framework discovery then located nebula-agents; the product selection remained the same explicit environment value throughout. The run ID was minted exactly once using secrets.token_hex(4).
