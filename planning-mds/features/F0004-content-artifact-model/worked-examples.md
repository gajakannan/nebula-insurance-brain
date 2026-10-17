# F0004 worked examples

**Provenance:** synthetic development examples extending [EX-GL-001](../../examples/neurosymbolic-gl/README.md) and [EX-SEM-003/006](../../examples/statements-time-and-governance.md).\
**Delivery:** v0.1A storage/contracts; all outputs below are illustrative expectations, not observed F0004 execution. No new insurance rule is asserted. Keep these cases outside the frozen evaluation holdout.

## EX-CONTENT-001 — Preserve source, artifact and run identity

**Definition:** the immutable original document version, its parsed content artifact, and an interpretation run are distinct identities ([master blueprint §6](../../architecture/master-blueprint.md), ADR-0004).

The EX-GL-001 declarations PDF has a retained source version. Parsing creates one six-file content bundle. Profiles A and B read its native JSON after a worker restart and create two separate run outputs. Expected: identical source/artifact/file hashes before and after; zero converter/OCR entry-point calls in both reuse runs.

**Boundary:** change one byte in `blocks.jsonl`, omit `tables.jsonl`, or fail before manifest publication. The candidate is not returned as a verified ready artifact. A valid empty tables file is different from a missing file. Changing a profile never grants permission to rewrite the bundle.

**Owner/contracts:** [S0001](F0004-S0001-publish-and-reuse-content-bundle.md), [S0004](F0004-S0004-authorized-consumers-and-compatibility.md); [ADR-0040](../../architecture/decisions/ADR-0040-lossless-content-and-evidence-contract.md), [ADR-0059](../../architecture/decisions/ADR-0059-provider-neutral-content-artifact-storage.md), existing [manifest schema](../../schemas/content-artifact-manifest.schema.json). Phase B versioned the extensions: [manifest v2](../../schemas/content-artifact-manifest-v2.schema.json) and the [read union](../../schemas/content-artifact-manifest-read.schema.json).

## EX-CONTENT-002 — Preserve structure without overstating evidence

**Definition:** a content block is an addressable piece of the retained parse; its origin records how its words were obtained ([glossary](../../domain/glossary.md), ADR-0065).

The same synthetic declarations amount appears in a native text block (`STATED`) and in the scanned fixture's OCR block (`OCR`). Each has its actual producer/version and an artifact-local anchor. A generated chart description is a separate `DESCRIBED` block with its figure anchor. A synthetic transcript record uses `TRANSCRIBED`, producer and time-span/speaker anchor; it proves contract validation only, not audio ingestion.

**Boundary:** a single block combining stated text and a description is invalid. A repeated dollar amount in two cells cannot be anchored solely by matching its words. Preserve separate table/cell references and origin; missing geometry never becomes a fabricated bounding box. Astral Unicode characters must not change stored code-point positions into UTF-16 offsets. Merged cells, repeated headers and continuation tables retain available relationships.

**Owner/contracts:** [S0002](F0004-S0002-content-structure-and-text-origin.md); [ADR-0058 as amended](../../architecture/decisions/ADR-0058-evidence-anchoring-and-selector-contract.md), [ADR-0065 §3](../../architecture/decisions/ADR-0065-assertion-admission-text-origin-and-mood.md). F0006/F0018/F0022 own admission, canonical effects and review, including the described-only restriction. Block/table/layout records are bound to [content records v2](../../schemas/content-records-v2.schema.json).

## EX-CONTENT-003 — A document date is not its receipt time

**Definition:** the document's own date is part of its time context, distinct from upload, sync, receipt, extraction and acceptance times ([glossary](../../domain/glossary.md), ADR-0064 §3).

A synthetic endorsement says issued June 10, effective June 1; it arrives June 12 and is accepted June 14. Expected F0004 metadata: document date June 10 with `CONTENT` and its source locator. Receipt remains June 12. F0004 does not compute an effective interval or a canonical acceptance time from the document date.

A source system's attributable issue/send date can instead carry `SOURCE_METADATA`. A reviewer-supplied date carries `HUMAN` with the authorized decision/actor reference. Later correction preserves the earlier value and basis; no content file is edited.

**Boundary:** a document containing only “today” and an upload timestamp stays undated. A missing source/basis or forged human authority fails validation/authorization. Two conflicting supplied dates remain distinguishable; F0004 does not silently choose one. Later time resolution and the reviewer input screen belong to F0016/F0022.

**Owner/contracts:** [S0003](F0004-S0003-document-date-provenance.md); [ADR-0064](../../architecture/decisions/ADR-0064-time-interpretation-and-valid-time-precision.md), [ADR-0037](../../architecture/decisions/ADR-0037-human-corrections-append-they-do-not-rewrite-evidence.md). The versioned metadata contract is the [document-date record schema](../../schemas/document-date-record.schema.json). In v0.1 the selection itself requires a verified human selection decision.

## EX-CONTENT-004 — A retained artifact does not retain permission

**Definition:** current resource scope controls reads independently of historical ownership ([F0002 examples](../archive/F0002-tenancy-aware-domain-kernel-and-principal-contracts/worked-examples.md)).

An authorized principal reloads the EX-GL-001 artifact, source and run-output references. After membership or applicable source access is revoked, those reads disclose no bytes. Restoring the database and object-store backup preserves exact content identity while current authorization still applies.

**Boundary:** a principal from another tenant or a disallowed KB cannot access an object by guessing its key or reaching an alternate metadata/preview path. An old manifest without new origin/date fields is read under its supported legacy version; its missing provenance is not silently synthesized. Unknown versions fail explicitly.

**Owner/contracts:** [S0004](F0004-S0004-authorized-consumers-and-compatibility.md); ADR-0059, F0002 approved AuthX contracts, F0003 persistence/restore contracts. Existing F0005 proof outputs are compatibility inputs, not production release approval.

## Verification handoff

Contract versions, executable fixtures and validation commands are in [contract-examples.json](contract-examples.json), [validate-contract-examples.py](validate-contract-examples.py) and the assembly plan's test matrix. The feature implementation must retain expected-versus-observed results, actual reproduction commands, restart/restore evidence and negative authorization cases. The fixtures prove schema conformance only; no runtime result is claimed.
