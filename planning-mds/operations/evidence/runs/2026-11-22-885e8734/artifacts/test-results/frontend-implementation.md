# F0011 headless JavaScript implementation evidence

Reviewer/implementer: Codex / Frontend Developer; fixture audit: Codex / Quality Engineer.
Run: `2026-11-22-885e8734`.

## Implemented boundary

`experience/scripts/contracts/runtime.mjs` loads the generated installed snapshot
by relative path. It verifies manifest shape, schema bytes/hashes, identities,
profile, source-derived metadata, reference closure and non-recursion before
compiling AJV 2020-12 validators. Schemas/metadata returned to callers are detached.
The validator has no remote `loadSchema` path. AJV defaults, coercion and property
removal are disabled. Portable decoding checks malformed UTF-8/JSON, duplicate
keys, paired Unicode, finite/safe numbers and the approved resource limits.

`check.mjs` executes every supplied portable case using the real decoder/AJV.
Unknown versions, missing schemas, unsupported profiles, malformed inventories
and duplicate IDs fail the whole command. Expected-instance failures produce safe
IDs/codes, never input text. The CLI returns 0 for complete conformance, 1 for an
expectation mismatch, and 2 for a broken run.

Exact tooling pins are AJV 8.20.0, ajv-formats 3.0.1, jsonc-parser 3.3.1 and
pnpm 12.21.0. Node 22.23.1 ran the checks inside the healthy `node-validation`
application container after G1. The Node suite is excluded narrowly from Vitest
discovery; ordinary UI tests continue using the existing jsdom setup.

## Executed checks

| Check | Observed result | Raw evidence under this run |
|---|---|---|
| Node unit/CLI suite | 14 passed, zero failed/skipped | `artifacts/test-results/js-unit.tap` |
| Node source coverage | check.mjs 100%; runtime.mjs 98.86%; combined 99.04% lines, 96.47% branches | same TAP summary; `artifacts/coverage/js-v8/` raw V8 files |
| Existing ESLint | exit 0 | `artifacts/test-results/frontend-lint.txt` |
| Existing TypeScript/Vite build | exit 0 | `artifacts/test-results/frontend-build.txt` |
| Existing Vitest | 12 passed in 3 files | `artifacts/test-results/frontend-test.txt` |
| Frozen lock install | exit 0, no resolution changes | `artifacts/test-results/frontend-frozen-install.txt` |

The unchanged PDF viewport tests emit jsdom canvas `getContext` diagnostics while
passing. The unchanged PDF application bundle retains its size advisory. Those
outputs are preserved verbatim in the raw regression artifacts.

## Shared behavior audit

`scripts/contracts/behavior-cases.json` adds 187 synthetic structural witnesses;
the parent merged these with the 176 preserved/imported cases into the shared
363-case inventory. `case-behavior-map.json` records source identity/hash and
pointer mappings for 66 behavior entries, including all 21 if-conditionals, six
contains/min/max occurrences and four portable formats. Empty or absent branches
are explicitly identified as unable to reject; they are never invented negative
proof. These fixtures supplement complete payload and actual consumer tests.

Full generated-bundle conformance is pending snapshot publication at this point.
This supporting implementation artifact is not a completed QE/security/signoff
report. No UI, style, theme or browser interaction changed; the approved headless
scope has no screenshot or visual-accessibility proof surface.

Implementation mechanics were checked against the primary
[AJV option documentation](https://ajv.js.org/options.html) and
[Microsoft jsonc-parser source documentation](https://github.com/microsoft/node-jsonc-parser).
The approved F0011 profile controls the product choices.
