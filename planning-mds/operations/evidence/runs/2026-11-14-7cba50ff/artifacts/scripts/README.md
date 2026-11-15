# Review helper scripts

These are copies of the six helper scripts this review ran from `/tmp`, preserved on 2026-11-14 so the audit can be re-run. `commands.log` cites the original `/tmp/f0064_*.py` paths; the copies here are byte-identical. They hard-code absolute local paths for the review host.

- `f0064_review_exec.py` — command wrapper writing `commands.log` and `lifecycle-gates.log`
- `f0064_arch_audit.py` — binding and symbol AST audit (`artifacts/reviews/architect-static-audit.txt`)
- `f0064_qe_raw_audit.py` — raw-artifact audit (`artifacts/reviews/qe-raw-artifact-audit.json`)
- `f0064_story_currency.py` — isolated story-index currency check
- `f0064_log_bootstrap.py` — backfill of pre-logger commands
- `f0064_finalize_review.py` — read-only check and report finalization
