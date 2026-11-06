"""Observed admission/explicit-commit boundary; no new acceptance policy."""
import json

import pytest
from engine.tests.fixtures.assertions import harness
from engine.tests.integration.test_assertion_consumers import commit, slot

_clean_fact_tables = harness._clean_fact_tables
database = harness.database
world = harness.world
world_factory = harness.world_factory
counts = harness.counts


@pytest.mark.parametrize('basis', ['INFERRED', 'AMBIGUOUS'])
async def test_admission_never_automatically_commits_high_confidence_basis(world, database, basis):
    record = world.candidate(interpretation_basis=basis, model_confidence=0.99)
    accepted = (await world.admit([record])).accepted[0]
    assert accepted.record.interpretation_basis == basis
    after_admission = counts(database)['canonical_fact_version']
    assert after_admission == 0
    evidence = [accepted.server_evidence[0].evidence_id]
    result = await commit(world, slot(world), evidence)
    assert len(result.fact_version_ids) == 1
    print(json.dumps({'basis':basis,'review_required':accepted.review_required,
                      'canonical_after_admission':after_admission,
                      'canonical_after_separately_authorized_commit':counts(database)['canonical_fact_version']}))
