# F0004 implementation decisions

## Transactional authorization audit order (Architect)

The approved date design has an immediate foreign key from each date row to its
authorization audit row. The existing `AuthorizationExecution.mutate` appends
that audit after the operation callback, so a correct candidate insert cannot
satisfy the constraint. Step 3 explicitly requires this facade and one unit of
work; deferring the constraint or independently committing authorization would
weaken that requirement.

Refinement: stage each successful decision inside the existing transaction
before calling the protected operation, then commit audit and effects together.
The staged audit is not durable or externally visible before commit. An audit
insert failure prevents the callback. An operation failure rolls back staged
success and effects before writing the failed decision in a fresh transaction.
Recheck time validity after audit staging and before the effect. No evaluator,
grant, public method signature or read semantics change. ADR-0073 stays Proposed.

KG blast radius identifies F0002-S0006 durable authorization decisions. Its
existing mutation regression suite plus new audit ordering/failure tests must
pass; PostgreSQL date tests will prove the immediate foreign key in practice.
This is a necessary integration refinement within the approved F0004 plan.

## Observed Graph provenance limitation (AI Engineer / Architect)

The pinned Graph 1.9.1 direct pipeline emits a version-2 chunk ledger whose
`doc_item_refs` is empty for the controlled saved-native fixture. The existing
conservative evidence mapper consequently returns `unresolved` and the run is
`partial` with `unresolved_property_evidence`, for both v1 and v2 parse bundles.
F0004 preserves that result; it does not invent refs, alter property attribution,
or qualify Graph activation. A separate controlled reference-ledger expectation
proves the stored native geometry still translates to the existing exact-span
BoxSelector. The real pipeline reuse proof forbids actual parser and OCR entry
points and measures recorded model requests; it is not an inference-quality proof.

## Durable fallback diagnostics and the existing queue fence (Architect)

An enabled v2 attempt can legitimately publish the plan's deterministic v1
fallback ID, which differs from its queued v2 artifact ID. The original queue
lease remains the conversion serialization/fencing resource; it is never silently
retargeted. Publication must validate the fallback ID from the source-based
version/recipe identities and authorize both resources in the queue transaction.
The trusted submitter provisions both pre-record security envelopes with the
same declared restrictions. Import and interpretation use the accepted registry
artifact key, with current authorization on that actual resource.

The strict v1 manifest has no fallback fields. A marker can survive a failed DB
commit, so the original unattributed-item count must also survive before that
marker is written. Retain a deterministic immutable publication-intent receipt
outside the parse inventory, bound to owner/document/version/artifact/source,
recipe and bundle hash. It carries only the observed fallback reason/count.
Write and recover it under the same fenced current-authority boundary. A retry
validates the receipt and adopts the existing marker without parsing; a missing
or mismatched receipt fails explicitly. Receipt bytes confer no permission and
are not served by content routes. This adds no public contract or queue engine.
Implementation is complete. PostgreSQL fault proofs retain the count after a
failed readiness commit and reject missing/tampered receipts. The worker proof
publishes actual observed native content as v2, exercises explicit origin-unavailable
v1 fallback and reuses both under another profile with parser/OCR calls forbidden.
The v2 flag remains false pending final compatibility and review.

## Concurrent trusted submissions (Architect)

Concurrent profile requests for one unaccepted source must share its physical
identity. Serialize submitters with a PostgreSQL transaction advisory lock on a
separate `submission:tenant:kb:sourceSHA` namespace. Only submitters acquire it;
publishers retain job → authority → source/version → artifact order and never
wait on the submission lock. The existing queue still owns leases, fences,
retries, completion and idempotent request keys. A two-thread PostgreSQL proof
confirms both profiles share the pending identity; a later writer-flag change
preserves it. Existing security restrictions cannot be overwritten by enqueue.

## Local snapshot and isolated restoration (DevOps / Architect)

Require an explicit quiesced ingestion/date-writer window. Verify and record the
selected revision, all application table hashes, complete object inventory,
dependency locks and packaged contracts before and after capture. Restoration
uses a unique throwaway container and fresh directory, validates the backup
inventory before extraction, then checks every referenced readable bundle/run,
normalized indexes, date lineage/audit identity and ownership without repairs or
conversion. Unreferenced objects are reported and retained. This is a supported
local procedure, not a distributed snapshot. Actual v1/v2 restore proofs passed,
including two resolving citations each, historical selection after a clear,
and rejection of missing required bytes/index rows. No shared database migration
or operator mutation was performed.

## Security scan refinements (Architect / Backend / AI)

Initial pip-audit identified reachable advisories in unchanged dependencies.
The bounded remediation updates both locks to PyJWT 2.15.0, and neuron to pypdf
6.19.0, urllib3 2.8.0 and multidict 6.9.1. Docling 2.126.0, core/parse/Graph,
RapidOCR and Torch remain pinned. Repeat the provenance/compatibility and
authorization tests on the rebuilt locked jobs before claiming acceptance.

The physical adapter now explicitly allows PDF only, matching the authored
source contract and excluding HTML/JATS/LaTeX/archive/serialized-JSON backends.
Recorded native consumers remain readers, never converter inputs. Remaining
pinned-Docling advisories require reachability assessment; they are not waived
or declared fixed by this configuration. Installed plugin code remains a trusted
deployment boundary; no untrusted plugin-install capability is introduced.

SAST identified constructed SQL over trusted fixed/catalog identifiers. The
new downgrade existence checks use SQLAlchemy selects; global uniqueness
reconciliation uses DropConstraint on the catalog-discovered single-column
unique constraint. Its existing owner constraints and inventory/authority
checks stay intact. Read-only content responses explicitly use private,
no-store and nosniff headers. The operator-only restore validation job now
uses its Docker network and scoped socket group: host-published loopback
ports were unreachable from Docker Desktop's host-network job. The normal
local restore still binds a unique loopback port; network mode publishes none.


## G3 review corrections — 2026-10-20

- SEC-H1: reject source bytes that do not start with %PDF- before PdfReader or
  Docling detection/pipeline initialization. Allowed formats apply too late to
  exclude gzip/PDF polyglots; pypdf's non-strict reader accepts them. Both
  provenance modes reject gzip, ZIP, text-prefixed and empty inputs. Real
  native/scanned conversion and v2 provenance remain exercised.
- Code review date-read race: hold the DocumentVersion row FOR SHARE through
  read audit commit. Date writers already use FOR UPDATE in the same authority
  ordering. Candidate and latest-selection statements cannot straddle a writer.
  The PG regression observes actual blocking, then checks consistent old and
  new selected dates on either side of commit.
- Code review scaling: split each blocks/tables JSONL payload once per index
  insertion/verification instead of once per record. Exact ordinal hashes and
  durable table/continuation semantics remain unchanged.

No new grant, accepted ADR, model activation or production operator action.
