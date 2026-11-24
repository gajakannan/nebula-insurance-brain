# Architect reconciliation — portable profile parity

Owner/reviewer: Codex / Architect
Date: 2026-11-23
Run: 2026-11-22-885e8734

Independent initial review found three High portable-boundary mismatches and a
Medium schema-position issue. These are blocking implementation defects, not
accepted deviations. The approved single-profile/cross-language requirement
controls. No released source schema identity, assertion or legacy domain/hash
semantics changes.

1. Depth counts every JSON value, including a scalar leaf; the root is depth1.
   The existing bound remains128. Both raw decoding and direct value admission
   enforce it. Schema positions, metadata strings and object property names do
   not create additional instance-value depths.
2. Portable patterns use ECMAScript exact terminal-dollar semantics. All16
   selected patterns use ASCII explicit classes and one unescaped terminal
   dollar. Python's portable-only engine registry projects that admitted anchor to
   exact-end \Z; unsupported dollar placements are rejected during admission.
   Native compatibility retains its previous Python pattern behavior.
3. Incoming UTF-8 bytes retain the exact16MiB cap. Already-decoded values use
   canonical RFC8785 UTF-8 length, so binary64 exponent/negative-zero formatting
   cannot change acceptance by language. Pin the isolated rfc8785 Python encoder;
   JavaScript JSON.stringify has the same byte length for admitted JSON values
   (canonical key ordering does not alter length). Do not extend or reuse the
   F0007 JCS subset: its no-float/ASCII-key identity policy stays unchanged.
4. Caller-selected fragments must be admitted schema positions. Annotation data
   objects are never schemas; resolve/schema/metadata/validate refuse them in
   both languages even when they are object-valued.

Add independently expected shared boundary witnesses and actual negative tests
for all four fixes. Compact raw-repeat fixture recipes keep16MiB boundary cases
reproducible without committing padded payloads; unknown/malformed recipes fail.
Replay the affected conformance, generated-model, consumer, installed-package
and final-history proofs against the final code. Native differential evidence
must remain unchanged. G2 and later gates remain pending.

References: approved assembly plan's portable facade and source-gated model
requirements; initial code-review-report.md and code-review-initial-probes.json.
The encoder API and UTF-8 behavior were verified against the maintainer's
[rfc8785 documentation](https://pypi.org/project/rfc8785/0.1.4/).

The final shared inventory has443 cases: all363 originals plus80 independently expected review regressions. The initial custom-validator approach was discarded after a root-dialect regression proved that ref evolution could bypass it. The internal registry projection preserves exact-end behavior through root and fragment ref chains; public/native schemas remain untouched.
