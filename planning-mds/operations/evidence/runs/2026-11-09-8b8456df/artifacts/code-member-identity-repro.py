import asyncio
import importlib.util
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

ROOT = Path('/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain')
spec = importlib.util.spec_from_file_location('f0007audit_memory', ROOT / 'engine/packages/brain-factslots/tests/conftest.py')
memory = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = memory
spec.loader.exec_module(memory)

from brain_domain.authx import ResourceKey, ResourceType
from brain_factslots.answers import FactAnswerPolicy
from brain_factslots.predicates import SYSTEM_PREDICATES
from brain_factslots.resolution import FactSlotResolver
from brain_testing.factslots import ADDITIONAL_INSURED, test_registry, slot_key

async def main():
    scene = memory.scene.__wrapped__()
    owner = (scene.tenant, scene.kb)
    registry = test_registry()
    resolver = FactSlotResolver(registry, scene.store)
    policy = FactAnswerPolicy(registry, scene.store)
    actor = uuid4()
    source = [ResourceKey(ResourceType.CONTENT_ARTIFACT, UUID(int=7))]

    async def resolve(predicate, value):
        return await resolver.resolve(slot_key(scene.kb, scene.subject, predicate, member=value), authorized_scope=owner, source_keys=source, actor_id=actor)

    a, b = scene.entity(), scene.entity()
    result = await resolve(ADDITIONAL_INSURED, {'type': 'entity_ref', 'entity_id': str(a)})
    accepted = await policy.canonical_value(result.member_slot_id, {'answer_contract': 'fact-answer/v1', 'state': 'PRESENT', 'value': {'type': 'entity_ref', 'entity_id': str(b)}}, authorized_scope=owner)
    print(json.dumps({'case': 'entity_member_mismatch', 'stored_member_key': scene.store.slots[result.member_slot_id].member_key, 'different_entity_submitted': str(b), 'accepted': accepted}, indent=2))

    assertion, document = uuid4(), uuid4()
    scene.store.evidence[assertion] = (document, owner, ())
    evidence = {'assertion_id': str(assertion), 'document_version_id': str(document)}
    trade = SYSTEM_PREDICATES[1]
    result = await resolve(trade, {'type': 'name', 'verbatim': 'Acme Restoration', 'evidence': evidence})
    accepted = await policy.canonical_value(result.member_slot_id, {'answer_contract': 'fact-answer/v1', 'state': 'PRESENT', 'value': {'type': 'name', 'verbatim': 'Zed Services', 'evidence': evidence}}, authorized_scope=owner)
    print(json.dumps({'case': 'production_sys_name_member_mismatch', 'predicate': str(trade.key), 'stored_member_key': scene.store.slots[result.member_slot_id].member_key, 'different_name_submitted': 'Zed Services', 'accepted': accepted}, indent=2))

asyncio.run(main())
