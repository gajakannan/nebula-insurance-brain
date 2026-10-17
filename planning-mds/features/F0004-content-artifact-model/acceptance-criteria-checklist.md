# F0004 acceptance criteria checklist

**Status:** Phase A draft. All boxes represent future implementation evidence, not planning approval. The four stories are authoritative for detailed interaction, access and failure contracts.

## F0004-S0001 — Publish and reuse an immutable content bundle

- [ ] [F0004-S0001-AC1](F0004-S0001-publish-and-reuse-content-bundle.md) — Given a retained source version and authorized ingestion handoff, when its parse is published, then the six required files and native-export assets are retained with source/artifact identities, ownership, version metadata and hashes; a read after restart returns the same bytes and references.

- [ ] [F0004-S0001-AC2](F0004-S0001-publish-and-reuse-content-bundle.md) — Given a complete bundle, when it is published, then file integrity is verified before the manifest completion marker and database ready visibility; an empty valid tables file is allowed, but a missing required file is not.

- [ ] [F0004-S0001-AC3](F0004-S0001-publish-and-reuse-content-bundle.md) — Given a parser result, when the artifact is stored and reloaded, then parser name/version/configuration identity, native schema/content contract version, parse quality, failed pages and warnings round-trip. Partial parsing is visible and cannot be reported as complete extraction.

- [ ] [F0004-S0001-AC4](F0004-S0001-publish-and-reuse-content-bundle.md) — Given the same published artifact and two existing profile consumers after restart, when they read the saved native JSON, then converter/OCR entry points are never called, original and bundle hashes are unchanged, and extraction graph/provenance/configuration remain separate run-owned outputs.

- [ ] [F0004-S0001-AC5](F0004-S0001-publish-and-reuse-content-bundle.md) — Given a published artifact, when an overwrite or conflicting publication is attempted, then accepted bytes and identity are unchanged and the result explicitly identifies reuse or conflict. Retry execution remains F0005; the storage boundary must not create two conflicting accepted versions for one identity.

- [ ] [F0004-S0001-AC6](F0004-S0001-publish-and-reuse-content-bundle.md) — Given an authorized publication, when validated content becomes available, then durable audit history records actor, scope, artifact identity and recorded time; failed publication never records a successful content mutation.

## F0004-S0002 — Preserve content structure and text origin

- [ ] [F0004-S0002-AC1](F0004-S0002-content-structure-and-text-origin.md) — Given parsed native and scanned PDF fixtures, when content is published and reloaded, then block IDs, reading order, section/page membership and available table/cell relationships point to the same immutable artifact; dangling or cross-artifact references fail validation.

- [ ] [F0004-S0002-AC2](F0004-S0002-content-structure-and-text-origin.md) — Given new-contract block records, when they are validated, then each has exactly one text_origin from STATED, OCR, TRANSCRIBED or DESCRIBED, an attributable producing engine/model/version, and the applicable origin-specific anchor. Non-model producers explicitly record that no model applies.

- [ ] [F0004-S0002-AC3](F0004-S0002-content-structure-and-text-origin.md) — Given OCR, transcript and description examples, when they round-trip, then page/region, time-span/speaker and page/figure anchors respectively retain their meaning. Native/scanned PDF uses observed parser provenance; transcript/description fixtures prove storage only and introduce no new engine.

- [ ] [F0004-S0002-AC4](F0004-S0002-content-structure-and-text-origin.md) — Given a rotated page, Unicode astral characters or unavailable geometry, when locators are stored/read, then page numbering, coordinate origin/units/page dimensions/transform, normalization version and Unicode code-point offset conventions are explicit where applicable; missing precision remains coarse or unresolved with no invented box.

- [ ] [F0004-S0002-AC5](F0004-S0002-content-structure-and-text-origin.md) — Given repeated values, merged cells, repeated headers and continuation-table content, when represented relations are stored/read, then cell/header/continuation identities remain distinguishable; matching a value alone does not establish its location.

- [ ] [F0004-S0002-AC6](F0004-S0002-content-structure-and-text-origin.md) — Given an origin/producer/anchor validation failure or a block mixing origins, when publication is attempted, then the new-contract record is rejected explicitly and no already published bundle is changed. Readable legacy content follows S0004 and is never relabeled without evidence.

- [ ] [F0004-S0002-AC7](F0004-S0002-content-structure-and-text-origin.md) — Given an authorized publication, when validated content becomes available, then durable audit history records actor, scope, artifact identity and recorded time; failed publication never records a successful content mutation.

## F0004-S0003 — Preserve document-date provenance

- [ ] [F0004-S0003-AC1](F0004-S0003-document-date-provenance.md) — Given an attributable document date from content, source metadata or an authorized human decision, when it is recorded and reloaded, then its date value, source kind, document version, source/decision reference and recorded actor/time remain available together.

- [ ] [F0004-S0003-AC2](F0004-S0003-document-date-provenance.md) — Given an undated document with upload, sync, receipt or extraction timestamps, when its date metadata is read, then document date remains absent; none of those system timestamps is substituted.

- [ ] [F0004-S0003-AC3](F0004-S0003-document-date-provenance.md) — Given a date correction with attributable authority, when the corrected metadata is persisted, then the previous value and basis remain retrievable, the correction links to its predecessor, and the original and parse bundle hashes are unchanged. Updating source metadata does not rewrite an interpretation run's historical basis.

- [ ] [F0004-S0003-AC4](F0004-S0003-document-date-provenance.md) — Given invalid source kinds, missing provenance, cross-owner references or an unverified HUMAN attribution, when a mutation is requested, then it is rejected with an explicit reason, no successful mutation audit, and no lost prior value; authorization decisions remain audited.

- [ ] [F0004-S0003-AC5](F0004-S0003-document-date-provenance.md) — Given the June 1 effective / June 10 issued / June 12 received / June 14 accepted example, when F0004 records the content-sourced document date, then it retains June 10 and its source independently; it neither computes a canonical interval nor changes receipt/acceptance times.

- [ ] [F0004-S0003-AC6](F0004-S0003-document-date-provenance.md) — Given conflicting supplied document dates, when their provenance is stored, then the different candidates/bases remain distinguishable and no undocumented precedence rule selects a date. Resolution beyond an explicit authorized selection is outside F0004.

## F0004-S0004 — Protect artifact consumers and compatibility

- [ ] [F0004-S0004-AC1](F0004-S0004-authorized-consumers-and-compatibility.md) — Given current F0002 authority, when source bytes, native/normalized files, metadata, evidence or referenced run outputs are accessed, then the existing service path enforces tenant, KB and applicable parent/source restrictions before returning data, with attributable authorization audit and policy version.

- [ ] [F0004-S0004-AC2](F0004-S0004-authorized-consumers-and-compatibility.md) — Given cross-tenant, disallowed-KB, revoked-membership or restricted-source requests, when any covered read/publication path is invoked, then it returns no unauthorized bytes or protected metadata and creates no unauthorized artifact; alternate object-key/preview paths cannot bypass the check.

- [ ] [F0004-S0004-AC3](F0004-S0004-authorized-consumers-and-compatibility.md) — Given supported historical manifests and new-contract manifests, when existing consumers load them, then each follows its declared version; historical bytes/hashes stay unchanged and missing historical date/origin data remains absent. Unsupported versions fail explicitly instead of being guessed or silently upgraded.

- [ ] [F0004-S0004-AC4](F0004-S0004-authorized-consumers-and-compatibility.md) — Given a backup of metadata, source and artifact files plus referenced retained run outputs, when the supported local restore procedure is executed, then source/artifact identities, hashes, references and restrictions round-trip. Missing or mismatched bytes prevent a verified ready response.

- [ ] [F0004-S0004-AC5](F0004-S0004-authorized-consumers-and-compatibility.md) — Given the existing F0005 publication and saved-native-JSON proof seam, when contract compatibility is exercised after restart, then its two-profile reuse and honest evidence behavior remain intact without reparse, source mutation, or moving run-owned outputs into the parse bundle.

- [ ] [F0004-S0004-AC6](F0004-S0004-authorized-consumers-and-compatibility.md) — Given the four worked examples, when the feature is implemented, then reproducible commands compare independently expected versus observed persisted outcomes, cover failure and authorization cases, validate versioned structured fixtures, and keep development cases separate from the frozen holdout.

## Cross-cutting exit evidence

- [ ] Versioned contracts and independently expected examples validate.
- [ ] Current authorization and audit cover every affected read/write boundary.
- [ ] Restart/reuse, immutable hashes, supported legacy reads and local restore are proven.
- [ ] Changed-runtime coverage is at least 80%, with required negative/integration cases.
- [ ] STATUS carries passing evidence for each role required by the architect.
