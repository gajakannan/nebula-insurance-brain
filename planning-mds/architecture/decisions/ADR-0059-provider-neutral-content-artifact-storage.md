# ADR-0059: Provider-Neutral Content Artifact Storage

## Status

- [ ] Proposed
- [x] Accepted
- [ ] Superseded
- [ ] Rejected

**Date:** 2026-09-08
**Deciders:** Architect and operator
**Source:** Master blueprint sections 5, 80, 81, 108, and 114.3; F0001 Phase B

## Context

Nebula must retain original source bytes and immutable parse-once content-artifact bundles. PostgreSQL remains the authoritative runtime store for semantic data, artifact metadata, hashes, permissions, evidence bindings, interpretation runs, review records, and canonical facts, but it is not the application-facing home for the artifact byte streams.

The content bytes must be usable by the ingestion worker, reinterpretation pipeline, authorized review panel, backup/restore tooling, and future integrations. These consumers should not depend on an S3 SDK, Azure SDK, filesystem paths, bucket names, or provider-specific URLs. Object stores also differ in consistency, conditional writes, versioning, retention, and URL-signing behavior, so the shared contract must describe only the guarantees Nebula requires.

## Decision

1. Use a Ports-and-Adapters boundary for content artifacts.
2. Keep `ContentArtifactStore` as the application-facing port. It owns Nebula semantics: artifact identity, bundle layout, manifest validation, immutability, checksums, authorization handoff, and artifact lifecycle.
3. Place a provider-neutral `ObjectStore`/blob port beneath it for byte operations such as exclusive create, read, range read, metadata, checksum verification, and controlled deletion.
4. Implement only `LocalFilesystemObjectStore` in the initial runtime. It stores artifact objects below the configured local root and exposes object keys, never filesystem paths, to its caller.
5. Select the concrete adapter in the composition root through a small factory/registry. Future adapters may include `S3ObjectStore`, `AzureBlobObjectStore`, and `GcsObjectStore`; they are not part of the initial implementation.
6. The committed `config/local.yaml` is the default local configuration. The local filesystem adapter must not require environment variables to start. It must not contain secrets.
7. A bundle is published using a manifest-last protocol: write and verify the files, write the manifest as the completion marker, then make the corresponding PostgreSQL artifact row available as `ready`. Partial bundles are never readable as accepted artifacts.
8. The portable contract is the supported baseline, not a claim that every provider feature is identical. Provider-specific capabilities such as multipart upload, presigned URLs, object versioning, retention locks, and server-side encryption require explicit capability negotiation.

## Contract boundary

```text
ContentArtifactService
    └── ContentArtifactStore port
            └── ObjectStore port
                    ├── LocalFilesystemObjectStore       (initial)
                    ├── S3ObjectStore                     (future)
                    ├── AzureBlobObjectStore              (future)
                    └── GcsObjectStore                    (future)
```

The application and domain layers depend only on ports. Adapters are infrastructure code wired by the API and worker composition roots. Authorization remains in Nebula services before an adapter read; the storage adapter does not make tenant or reviewer decisions.

## Local implementation

The default local root is `./content`, which is runtime state and remains ignored by Git. Keys use the tenant and knowledge-base boundary:

```text
content/
  {tenant_id}/
    {knowledge_base_id}/
      {artifact_id}/
        original.pdf
        docling-document.json
        normalized.md
        blocks.jsonl
        tables.jsonl
        layout.jsonl
        manifest.json
```

The local adapter uses exclusive creation, rejects path traversal, verifies per-file and bundle hashes, and uses same-filesystem temporary writes plus atomic rename where applicable. The local implementation is intended for development and a single-node pilot. Shared filesystem or a cloud adapter is required before horizontal scaling.

## Configuration and secrets

Local non-secret configuration is committed in `config/local.yaml` so a fresh checkout has a discoverable default and does not depend on `.env` or manually exported storage variables. Database, identity, inference, and future cloud-provider credentials remain separate concerns and must not be placed in the committed file. Secret-bearing deployments may use their platform secret store or another explicitly documented mechanism when those integrations are implemented.

## Consequences

- PostgreSQL continues to be the authoritative runtime store; this decision does not introduce a second semantic database.
- F0001 can prove artifact upload, authorized reads, immutability, restart reuse, and restore using the filesystem adapter alone.
- The same adapter contract can later be tested against S3-compatible, Azure Blob, and other implementations without changing ingestion, review, evidence, or interpretation code.
- A filesystem backup is part of the restore unit for the local profile. The database dump alone is insufficient.
- The initial local profile is not a distributed object-store guarantee. Multi-instance deployment, cloud durability, retention locks, and signed browser delivery require a later adapter and deployment decision.

## References

- `planning-mds/architecture/master-blueprint.md` sections 5, 80, 81, 108, and 114.3
- `planning-mds/architecture/decisions/ADR-0002-postgresql-is-the-authoritative-runtime-store.md`
- `planning-mds/architecture/decisions/ADR-0003-one-time-content-extraction.md`
- `planning-mds/architecture/decisions/ADR-0004-source-content-artifact-and-interpretation-are-separately-versioned.md`
- `planning-mds/architecture/decisions/ADR-0040-lossless-content-and-evidence-contract.md`
- `planning-mds/features/F0001-repository-and-engineering-foundation/feature-assembly-plan.md`

## Refinement — 2026-09-15

[ADR-0060](ADR-0060-docling-graph-document-pipeline-orchestration.md) proposes Docling-Graph document pipeline orchestration. Docling-Graph output directories are temporary processing outputs, not the artifact storage API. Nebula publishes the parse bundle through ContentArtifactStore, and stores graph/provenance/configuration as separate versioned interpretation outputs with authorized access and retention.
