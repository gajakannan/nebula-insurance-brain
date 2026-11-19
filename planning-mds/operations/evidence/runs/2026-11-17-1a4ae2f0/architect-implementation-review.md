# Architect Implementation Review — F0008 (run 2026-11-17-1a4ae2f0)

- Role: Architect
- Reviewer: Claude (Opus 5.5) / Architect
- Date: 2026-11-18
- Result: PASS

## Conformance to the approved design (ADR-0078, assembly plan)

| Decision | As built | Conforms |
|---|---|---|
| D1 versioned contract on the existing row; legacy stays legacy | `temporal_contract` NULL/1; the insert trigger binds it to the slot's `identity_version`, and only a legacy predecessor's remainder may stay legacy on a v1 slot; a pilot shape to v1 is `temporal_fields_required`; a `temporal` block to a legacy slot is a 400 | Yes |
| D2 per-bound precision and zone, truncation in zone, DB authoritative | Service check (`zoneinfo` allowlist, wall-clock truncation) and trigger check (`pg_timezone_names`, `date_trunc(field, ts, zone)`) | Yes |
| D3 end states; UNKNOWN closes at the end of the `attested_to` period; `validity_unknown_from` | As specified, including the `end_state_invalid` refusal when positive evidence postdates the ending | Yes |
| D4 attestation from F0004 selections; floor; `START_UNATTESTED`; disclosure through READ checks | As specified. The clear semantics follow the F0004 read (CR-I2). Attesting documents are READ-checked at commit and on GET | Yes |
| D5 algorithm, remainder lineage, close-only immutability | As specified. Clarification: only a BOUNDED successor leaves a right remainder, and an end revision leaves none, both following the D5/D8 text | Yes |
| D6 lock order, `23P01` → `temporal_conflict`, MULTI and RELATIONSHIP slots in the same table | As specified; no `canonical_relationship_version` table | Yes |
| D7 envelope backstop (CHECK and trigger) with the upgrade preflight | As specified | Yes |
| D8 guards, end revision not a succession | As specified. The refusal is audited as a failed decision; reason persistence goes to F0018 (G0 note) | Yes, with note |
| D9 reads and the additive GET | As specified; a no-version coordinate stays 404 | Yes |
| D10 kinds reserved; STATE written | CHECK and trigger reserve EVENT and ETERNAL; v1 writes STATE only | Yes |

## Proof gates before acceptance

| Gate | Status | Evidence |
|---|---|---|
| 1 §115.4 under v1 | Met | `test_temporal_v1_commit.py` S0003, `test_temporal_concurrency.py` S0004 AC1 (12 racers, grid of at least 200) |
| 2 Immutability negatives and the single close | Met | `test_temporal_immutability.py` (23 columns, reopen, move, DELETE, TRUNCATE, change append-only) |
| 3 Zone and precision fixtures, both tzdata versions recorded | Met | `test_bounds.py`, S0001 PostgreSQL tests, `g1-tzdata-versions.txt` (PostgreSQL 2025b, Python 2026e) |
| 4 EX-SEM-004 and EX-PC-014 A–D | Met | `test_temporal_reads.py` |
| 5 Envelope backstop, guards, per-member independence | Met | `test_temporal_immutability.py`, `test_temporal_v1_commit.py` S0005, `test_temporal_concurrency.py` S0004 AC3 |
| 6 Migration snapshot byte-identical; downgrade guard names rows | Met | `test_temporal_migration.py`, `g2-migration-cycle.txt` |

All six proof gates have passing PostgreSQL 18 evidence. This review recommends ADR-0078 for acceptance, but acceptance stays an operator decision; the ADR remains Proposed until the operator records it. ADR-0064 and ADR-0039 stay Proposed.

## Shared semantics

No canonical semantics changed outside the approved design. The G0 reconciliations and the two G3 fixes changed no reason code meaning, route, grant or schema field meaning. The `brain-api.yaml` `FactVersion` gains the four optional read fields that the plan intended.

## Follow-ups

- CR-I1: `FactVersion` `valid`/`recorded` contract drift, which predates F0008.
- CR-I2: align the ADR-0078 D4 "not a clear" wording at acceptance.
- SEC-F8-02 → F0018.
- Refusal reason-code persistence → F0018.
