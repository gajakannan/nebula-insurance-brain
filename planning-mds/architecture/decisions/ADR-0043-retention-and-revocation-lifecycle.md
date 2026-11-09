# ADR-0043: Retention and Revocation Lifecycle

## Status

- [x] Proposed
- [ ] Accepted
- [ ] Superseded
- [ ] Rejected

**Date:** 2026-09-05 (record created from the master blueprint baseline)
**Decision recorded:** 2026-11-08 by the operator (blueprint requirement-ownership amendment). Features plan against the decision below. The status stays Proposed under the section 106 decision posture until the proof below is recorded.
**Owner:** Architect + Security Reviewer; records/legal owners supply retention schedules before a production pilot
**Proving features:** F0010 (distinct lifecycle events), F0018 (tombstone hook), F0026 (deletion and restore drill)
**Formal acceptance:** F0026 deletes a source through the operator workflow, restores a backup taken before the deletion, and shows that the deletion is re-applied and the source and its dependants stay unavailable.
**Source:** `planning-mds/architecture/master-blueprint.md` sections 110.3 and 116

## Context

Sections 0 and 5 use indefinite-preservation language while section 94 defers verifiable forgetting. Section 110.3 requires a practical delete, revoke and restore contract before a production pilot. Retention schedules are jurisdiction-specific and are not yet available (section 117.1 item 7).

## Decision

1. **Wording.** Preserve immutable evidence for its authorized retention period; apply approved hold, deletion and access policies across dependent representations.
2. **Four distinct events.** Source withdrawal, canonical retraction, access revocation and authorized deletion are separate event types with separate effects. None is modelled as another.
3. **v0.1 minimum (operator-initiated deletion only).** No automatic schedule-driven deletion in v0.1. An operator deletion request:
   - builds a dependency inventory across original files, content artifacts, assertions, facts, review records, chat history, embeddings, derived results, caches and exports;
   - removes or tombstones each dependant (tombstones keep identity and audit, not content);
   - records a deletion record that a restore re-applies before the restored data becomes readable.
4. **Schedules later.** Retention schedules and legal holds become versioned policy inputs before a production pilot. The deletion workflow is designed so that a schedule can trigger it later without changing it.
5. **Offline copies.** The service cannot recall material already downloaded; that treatment is a separate policy decision.

## Consequences

- F0010 defines the four event types; F0018 records deletion and revocation through the commit audit with tombstones.
- F0026 runs the deletion and restore drill together with the existing ADR-0073 restore drill.
- Section 117.1 item 7 stays open for production; it does not block v0.1.

## References

- `planning-mds/architecture/master-blueprint.md` sections 106.3, 110.3, 116 and 117.1
