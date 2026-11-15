# Post-Closeout Corrections — run 2026-10-17-8a6cc79f (F0004)

Attested run files (signoff ledger, PM closeout, gate decisions) are unchanged. This note records corrections made after closeout.

## 2026-11-15 — Dangling symlinks in `artifacts/review/`

The review step ran inside the validation container, where the repository was mounted at `/app/brain` (see `README.md`). Pytest's `*current` convenience links, plus one `normalized.md` link that a test creates to `source.pdf`, were captured with absolute `/app/brain/...` targets. They did not resolve in any checkout outside the container.

Each of the six links was retargeted to the same file or directory as a relative link. Link names, targets and every other file are unchanged.

| Link (under `artifacts/review/`) | Old target | New target |
|---|---|---|
| `content-unit-temp/test_async_and_sync_adapters_ocurrent` | `/app/brain/…/test_async_and_sync_adapters_o0` | `test_async_and_sync_adapters_o0` |
| `content-unit-temp/test_round_trip_keeps_exact_macurrent` | `/app/brain/…/test_round_trip_keeps_exact_ma0` | `test_round_trip_keeps_exact_ma0` |
| `content-unit-temp/test_undeclared_objects_and_sycurrent` | `/app/brain/…/test_undeclared_objects_and_sy0` | `test_undeclared_objects_and_sy0` |
| `content-unit-temp/test_undeclared_objects_and_sy0/bundles/…/090bdd78-…/normalized.md` | `/app/brain/…/090bdd78-…/source.pdf` | `source.pdf` |
| `date-regression-temp/test_date_read_keeps_selected_current` | `/app/brain/…/test_date_read_keeps_selected_0` | `test_date_read_keeps_selected_0` |
| `date-regression-temp/test_durable_table_cells_headecurrent` | `/app/brain/…/test_durable_table_cells_heade0` | `test_durable_table_cells_heade0` |

None of these paths is listed in `evidence-manifest.json` or `gate-state.json`, so no recorded hash changes.
