# Bootstrap command provenance

Initial root selection, instruction reads, runbook discovery and run initialization occurred before commands.log existed. They were transcribed into commands.log after initialization; their timestamps are transcription times. Captured compound shell exit codes are the shell exit codes, not a claim that every internal command succeeded. Full setup output is in the conversation tool record; applicable context is preserved in artifacts/product-context.txt.

Observed setup invocation errors: project_context.py was once invoked from the product cwd (missing framework-relative script), corrected immediately by using framework cwd; run-gate.py --list without plan scope/target returned invalid_scope, corrected before any gate execution; exploratory _gate_runtime.py search used an absent filename (actual gate_runtime.py). None mutated product artifacts or bypassed a gate. No setup or validator exception was waived.
