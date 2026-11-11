"""Read-only deterministic audit reproduction of authority change between reads."""
import asyncio
import importlib.util
import sys
from pathlib import Path
from uuid import uuid4

ROOT = Path('/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain')


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


c = load('security_fixture_builders', 'engine/packages/brain-security/tests/conftest.py')
t = load('security_execution_fakes', 'engine/packages/brain-security/tests/test_execution.py')
from brain_domain.authx import Action, ResourceType
from brain_domain.fact_slots import Cardinality, SlotRole
from brain_factslots.answers import FactAnswerReader
from brain_factslots.ports import StoredSlot
from brain_factslots.service import AuthorizedFactSlots
from brain_security.casbin_adapter import CasbinAuthorizationAdapter
from brain_security.execution import AuthorizationExecution, AuthorizationDenied, PrincipalAuthority


async def main():
    policy = CasbinAuthorizationAdapter(
        ROOT / 'planning-mds/security/policies/model.conf',
        ROOT / 'planning-mds/security/policies/policy.csv',
    )
    owner, user = c.scope(), c.principal()
    secret = c.envelope(owner, classifications=('restricted',))
    slot = c.envelope(owner, ResourceType.FACT_SLOT, classifications=('internal',))

    class RevokingStore(t.FakeStore):
        async def commit(self):
            await super().commit()
            if len(self.committed) == 1:
                # Deterministic interleaving: a separate writer commits revoked
                # restricted clearance immediately after scope-read locks release.
                self.slices[user.id] = (c.grant(owner, 'TenantMember', classifications=('internal',)),)
                self.authorities[user.id] = PrincipalAuthority(user, 5)
                self.log.append('concurrent-revocation-committed')

    authority = RevokingStore(policy.release.release_id)
    authority.authorities[user.id] = PrincipalAuthority(user, 4)
    authority.slices[user.id] = (c.grant(owner, 'TenantMember'),)
    authority.resources[secret.key] = secret
    authority.resources[slot.key] = slot
    execution = AuthorizationExecution(authority, policy, policy.release, clock=lambda: c.NOW)

    class Answers:
        async def slot(self, slot_id):
            return StoredSlot(
                slot_id, owner.tenant_id, owner.knowledge_base_id, uuid4(),
                'sys:hasLegalName@v1', identity_version=1,
                slot_role=SlotRole.SLOT, cardinality=Cardinality.SINGLE,
                predicate_key='sys:hasLegalName@v1',
                predicate_release_ref='f0007-system-predicates/1',
            )

        async def answer_at(self, slot_id, **kwargs):
            return {
                'answer_contract': 'fact-answer/v1', 'state': 'NOT_FOUND',
                'scope': {'content_artifact_id': str(secret.key.id),
                          'profile_release_ref': 'profile/1', 'pages': [7, 8]},
            }

    service = AuthorizedFactSlots(execution, None, None, FactAnswerReader(Answers()))
    answer = await service.read_answer(user, slot.key.id, valid_at=c.NOW, known_at=c.NOW, trace_id='race')
    print('returned_after_scope_clearance_revoked', answer.to_json())
    async def nothing(decision):
        return None
    try:
        await execution.read(user, secret.key, Action.READ, trace_id='verify', load=nothing)
    except AuthorizationDenied:
        print('current_scope_read', 'DENIED')
    print('decision_order', [(d.resource.type.value, d.allowed, d.grant_revision) for d in authority.committed])


asyncio.run(main())
