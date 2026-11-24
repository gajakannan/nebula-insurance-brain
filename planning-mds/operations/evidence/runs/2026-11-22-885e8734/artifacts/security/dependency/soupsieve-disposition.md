# Independent disposition of SoupSieve audit results

Reviewer: Codex / independent Security Reviewer. Date: 2026-11-23.
Status: Preparatory disposition; final Security verdict remains pending G2.

The strict installed-pin audit reports 75 third-party engine dependencies with no
known advisories and 171 third-party Neuron dependencies with four advisories on
SoupSieve 2.9.2. Exact installed/lock reconciliation and editable product package
omissions are recorded by DevOps in the adjacent inventory/receipt artifacts.
The original four-advisory report is retained as
`neuron-before-soupsieve-remediation.json`; a later `neuron.json` must be read as
the current result, not assumed identical or clean.

| Advisory | Required exploitation condition | Raw fixed version floor |
|---|---|---|
| CVE-2026-126190 / GHSA-mmhr-3c5m-f64f | Descendant-combinator CSS selectors evaluated against attacker-influenced deeply nested HTML/XML | 4.0.0 |
| CVE-2026-126191 / GHSA-6655-6qjp-jx7x | Attacker controls a CSS selector string containing pathological digit escapes | 3.0.2 |
| CVE-2026-126192 / GHSA-4j63-6c4x-wfg4 | A general-sibling combinator inside `:has()` evaluated against crafted HTML siblings | 2.10.0 |
| CVE-2026-126193 / GHSA-7g44-g9rc-x53w | Attacker controls deeply nested pseudo-class selector syntax | 3.0.2 |

These are availability issues. The raw descriptions do not establish a
confidentiality or integrity exploit. The fixed floors are taken from the raw
advisory results, rather than assumed from the older descriptions' publication
text. The highest floor needed to remove all four is 4.0.0.

## Actual scope and reachability

This is a scoped assessment, not a waiver merely because the dependency predates
F0011. The base revision and candidate both pin 2.9.2. F0011's selected schema,
model, content-reader, FactSlot/temporal and API paths do not import BeautifulSoup
or SoupSieve and expose no CSS selector parameter. No product-owned Neuron source
imports those libraries or calls their CSS selection APIs.

The existing input adapter at
`neuron/packages/brain-ingestion/src/brain_ingestion/docling_adapter.py:45`
constructs `DocumentConverter(allowed_formats=[InputFormat.PDF])`. The parse method
also requires the source to begin with `%PDF-` before calling either parser. This
excludes the HTML and XML backend paths that use BeautifulSoup from the currently
configured ingestion entry point; F0011 does not broaden it.

The exact installed-source inventory in `soupsieve-reachability-final.json`
parsed all 301 Docling-slim files, 121 Docling-graph files, 105 Docling-core files,
four Docling-parse files and 25 IBM-model files with no read/parse failures.
`docling` itself is a metadata-only distribution, so an earlier inventory that
omitted `docling-slim` is not treated as coverage of its code.

The slim HTML backend has one actual CSS selection call at
`docling/backend/html_backend.py:1868`: a `p:has(...)` selector assembled from the
developer-owned `_PARA_BREAKERS` tag list. It accepts no user selector syntax and
does not include the general-sibling combinator required by CVE-2026-126192.
The HTML backend is outside the current PDF-only adapter path. XML backends use
BeautifulSoup but the inventory finds no CSS selector calls there. This static
inventory is a reachability aid, not a proof about all dynamic library behavior
or future features.

## Security decision

No demonstrated current F0011/PDF exploitation path meets any of the four
advisory preconditions. The known vulnerable component remains installed unless
the orchestration owner completes a compatible upgrade and a fresh audit.
Do not describe that state as a clean Neuron audit or erase the four raw results.

Preferred disposition: upgrade the transitive SoupSieve selection to a compatible
version at or above 4.0.0, preserve the lock delta and rerun the strict installed
audit and affected Neuron regression checks. This reviewer has not changed
application code or dependency pins.

If it remains unpatched at final review, treat component hardening as a Low
recommendation scoped to this existing PDF-only configuration, with DevOps and
AI Engineer ownership and follow-up before introducing any HTML/XML/CSS selector
input path. Reassess severity if that configuration changes; this assessment
does not authorize such activation. Final owner/date/disposition must be recorded
in the Security report if this recommendation is carried forward.

## Remediation (2026-11-23, G4 "fix all Lows")

Reviewer: Claude / Security Reviewer, at the user's G4 direction.

- Lock-only upgrade: `uv lock --project neuron --upgrade-package soupsieve`
  (uv 0.11.31) moved SoupSieve 2.9.2 → 4.1.3, above the 4.0.0 floor for all four
  advisories. No other package version changed
  (`neuron-soupsieve-lock-delta.diff`; prior lock `neuron-lock-before-soupsieve-upgrade.toml`).
  `beautifulsoup4` 4.15.0 declares an unconstrained `soupsieve` dependency.
- Fresh strict installed-pin audit: Neuron 171 third-party pins, **0 advisories**
  (`neuron.json`, `neuron-execution.json`, `summary.json`). The lock was unchanged during the audit.
- Compatibility: the full Neuron suite passes on 4.1.3, 265 passed, 0 failed
  (`../../test-results/neuron-full-soupsieve4.xml`). The 48 skips are all environment
  opt-ins (live qualification, PostgreSQL URLs, namespaces, vLLM, cached tokenizer),
  none HTML-related. Docling's one CSS call shape, `p:has(<33 _PARA_BREAKERS>)`,
  selects correctly (`soupsieve4-selector-smoke.json`).
- The four advisories are resolved. The vulnerable-component finding is closed rather than deferred.
