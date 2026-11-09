# OWASP Top 10 Results — Nebula Insurance Brain

Status: Baseline (v0.1 local scope)
Last Updated: 2026-11-08
Owner: Security

## Scope

Project-level roll-up of the OWASP Top 10 (2021) assessments recorded by feature security reviews, most recently F0006 (run `2026-11-02-5a00b0ff`) and the 2026-11-08 SEC-01/SEC-02 remediation review. Scope is the local runtime with trusted synthetic fixtures.

## Assessment Inputs

- F0006 security review report (SAST, gitleaks, pip-audit, anonymous DAST, manual review).
- 2026-11-08 pip-audit of the neuron environment after the dependency upgrade: no known vulnerabilities. Engine: no advisories at the F0006 review.
- `neuron/packages/brain-ingestion/tests/test_conversion_limits.py` for converter containment.

## Findings Summary

| Category | Status | Notes |
| --- | --- | --- |
| A01 Broken Access Control | OK in reviewed scope | Conjunctive scope checks and source READ (F0002/F0006); derived-result and historical rules planned (ADR-0042/0053) |
| A02 Cryptographic Failures | OK locally | certifi updated to 2026.10.18; TLS and encryption at rest are production-host decisions |
| A03 Injection | OK in reviewed scope | Parameterized SQL; documents treated as untrusted evidence (section 110.4) |
| A04 Insecure Design | OK with planning items | Threat model baseline; open items listed there |
| A05 Security Misconfiguration | Issue (Low) | SEC-03 / F0004 SEC-L2: `nosniff` missing on public and error responses; target 2026-11-17 |
| A06 Vulnerable and Outdated Components | **Resolved 2026-11-08** | SEC-01: 85 neuron advisories cleared (Docling 2.142.0, pypdf 6.21.4, Pillow 13.0.0, aiohttp, certifi, filelock, setuptools) |
| A07 Identification and Authentication Failures | OK in reviewed scope | Verified principals (ADR-0049); browser session contract planned (ADR-0051, F0021) |
| A08 Software and Data Integrity Failures | OK | Locked dependencies (`uv sync --locked` in CI), immutable artifacts, append-only history |
| A09 Security Logging and Monitoring Failures | OK | Atomic durable decision audit; SEC-02 baseline documents now present |
| A10 Server-Side Request Forgery | No path in reviewed scope | No remote fetch; Docling remote-fetch features are not enabled; the upgraded Docling clears its SSRF advisories |

## Required Actions

- SEC-03 response headers by 2026-11-17.
- SEC-F5-M1 remainder (separate OS user/container and no network for the converter) before untrusted or production PDFs.
- Rerun this roll-up with each security-bearing feature review.

## Sign-Off

Baseline roll-up authored 2026-11-08 (SEC-02). It aggregates feature evidence; it is not a new penetration test.
