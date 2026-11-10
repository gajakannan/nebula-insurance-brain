# Action Context

> Seeded by init-run.py. Fill the judgment sections before the first gate.

## Run Identity

- **NEBULA_PRODUCT_ROOT:** /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain
- **action:** plan
- **contract_effective_date:** 2026-07-11
- **contract_version:** 2026-07-11
- **feature_id:** F0007
- **feature_index_root:** /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain/planning-mds/operations/evidence/features/F0007-factslot-model
- **feature_slug:** factslot-model
- **mode:** clean
- **phase:** A+B
- **product_root:** /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain
- **run_folder:** /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain/planning-mds/operations/evidence/runs/2026-11-09-60865e32
- **run_id:** 2026-11-09-60865e32

## Inputs

- Operator prompt: plan action, FEATURE_ID=F0007, PHASE=A+B, FEATURE_MODE=new (2026-11-09).
- NEBULA_PRODUCT_ROOT resolved from the environment variable to the absolute path above. Product branch `plan/F0007-factslot-model`, created from `main` at `bd10279`.
- Framework checkout `nebula-agents` on `main`. One pre-existing, unrelated uncommitted change (`agents/templates/prompts/evidence-contract/plan-operator-friendly.md`) was left untouched.
- Governing sources: BLUEPRINT §§0–4.12; master blueprint §§12, 13, 15, 106.3, 107.3, 107.4, 109.1; ADR-0006 (Accepted); ADR-0038/0039/0042 (Proposed, decisions recorded 2026-11-08); ADR-0066 (Proposed); ADR-0061; the F0007 README amendments and kg-source shard notes; examples EX-OWN-003 and EX-SEM-008; the F0003 table-ownership row for `fact_slot`/`fact_slot_qualifier`; the F0001 pilot migrations 0003/0006/0007 and `brain_domain/facts.py`.

## Assumptions

- Slots are knowledge-base-owned semantic content (ADR-0061, ADR-0066 §1a).
- An unread slot answers `NOT_PROCESSED` at read time. No row is materialized per possible slot.
- F0007 accepts original-currency money only. Converted values are rejected until a feature owns exchange-rate provenance.
- G1 operator decisions (2026-11-09) are recorded in gate-decisions.md.

## Scope Boundaries

- In scope: slot identity and normalization, predicate key, cardinality with member/relationship identity, information-state carrier, qualified money and scoped identifiers, name FactSlots with a precedence-free display hook, pilot compatibility and ownership binding.
- Out of scope: bitemporal versions and supersession (F0008/F0019), lineage (F0009), change reasons (F0010), schema publication (F0011), ontology vocabulary (F0012/F0013), package completeness (F0014), run scopes (F0016), entity resolution, `entity_alias` and display precedence (F0017/F0023), SourceAuthorityPolicy and RLS enablement (F0018), isolation proof (F0026), UI, routes and new grants.
- Plan only: no runtime code, no feature evidence package, no role reports.

## Lifecycle Stage

- plan run initialized
