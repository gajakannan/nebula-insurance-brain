"""Independent review probe: real PostgreSQL READ COMMITTED date read interleaving.

Uses the run's existing fresh-database fixtures and controlled human receipts.
All filesystem writes are below this review directory; no shared data is changed.
"""
import asyncio
import json
import os
import runpy
import threading
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest
from brain_content.dates import DocumentDateValue
from brain_content.store import LocalContentArtifactStore
from brain_persistence import content_models as tables
from brain_persistence.authx import SqlAlchemyAuthorityStore
from brain_persistence.document_dates import DocumentDateService
from brain_security.execution import AuthorizationExecution
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import Session

ROOT = Path('/app/brain')
REVIEW = Path(__file__).resolve().parent
helpers = runpy.run_path(str(ROOT / 'engine/tests/integration/test_content_migration_states.py'))
patch = pytest.MonkeyPatch()
patch.setenv('BRAIN_MIGRATION_ADMIN_URL', os.environ['BRAIN_DATABASE_URL'].replace('postgresql+asyncpg://', 'postgresql://'))
database = helpers['database'].__wrapped__(patch)
url = next(database)
content_root = REVIEW / ('date-race-content-' + uuid4().hex)
publication = helpers['publication'].__wrapped__(url, content_root, SimpleNamespace())
published = next(publication)
services = helpers['date_services'].__wrapped__(published)


async def main():
    service_factory, actor, human, bundle, publisher = await anext(services)
    verifier = helpers['ControlledHumanVerifier'](human, bundle.manifest.version_id)
    async with service_factory(human_dates=verifier, human_selections=verifier) as service:
        first = await service.append_candidate(actor, artifact_id=bundle.key.artifact_id,
            date=DocumentDateValue(precision='DAY', value='2024-02-29'),
            basis=helpers['content_basis'](bundle), supersedes_id=None,
            idempotency_key='review-first', trace_id='review-first')
        initial = await service.select(actor, artifact_id=bundle.key.artifact_id,
            candidate_id=first.id, expected_selection_id=None,
            human_decision_id=verifier.selection(first.id), reason='controlled review selection',
            idempotency_key='review-select-first', trace_id='review-select-first')

    writer_result = {}

    async def write_next():
        engine = create_async_engine(url.replace('postgresql://', 'postgresql+asyncpg://'))
        try:
            async with AsyncSession(engine, expire_on_commit=False) as session:
                service = DocumentDateService(session,
                    AuthorizationExecution(SqlAlchemyAuthorityStore(session), publisher.policy, publisher.policy.release),
                    LocalContentArtifactStore(publisher.store.objects),
                    human_dates=verifier, human_selections=verifier)
                basis = verifier.date('2025-03-01')
                next_candidate = await service.append_candidate(actor, artifact_id=bundle.key.artifact_id,
                    date=DocumentDateValue(precision='DAY', value='2025-03-01'), basis=basis,
                    supersedes_id=first.id, idempotency_key='review-next', trace_id='review-next')
                next_selection = await service.select(actor, artifact_id=bundle.key.artifact_id,
                    candidate_id=next_candidate.id, expected_selection_id=initial.id,
                    human_decision_id=verifier.selection(next_candidate.id, initial.id),
                    reason='controlled concurrent review selection', idempotency_key='review-select-next',
                    trace_id='review-select-next')
                writer_result.update(candidate_id=next_candidate.id, selection_id=next_selection.id)
        finally:
            await engine.dispose()

    def write_thread():
        try:
            asyncio.run(write_next())
        except BaseException as error:
            writer_result['error'] = repr(error)

    original = Session.execute
    triggered = False

    def interleaved_execute(session, statement, *args, **kwargs):
        nonlocal triggered
        result = original(session, statement, *args, **kwargs)
        if (not triggered and session.info.get('review_date_reader')
                and tables.document_date_candidate in getattr(statement, 'get_final_froms', lambda: [])()):
            triggered = True
            thread = threading.Thread(target=write_thread)
            thread.start()
            thread.join(timeout=30)
            if thread.is_alive():
                raise AssertionError('concurrent writer blocked unexpectedly')
            if 'error' in writer_result:
                raise AssertionError(writer_result['error'])
        return result

    async with service_factory(human_dates=verifier, human_selections=verifier) as service:
        service.session.sync_session.info['review_date_reader'] = True
        patch.setattr(Session, 'execute', interleaved_execute)
        view = await service.read(actor, artifact_id=bundle.key.artifact_id,
            selection_id=None, trace_id='review-interleaved-read')
        patch.setattr(Session, 'execute', original)
    async with service_factory() as service:
        stable = await service.read(actor, artifact_id=bundle.key.artifact_id,
            selection_id=None, trace_id='review-stable-read')
    output = dict(interleaving_triggered=triggered,
        writer_committed=True,
        selected_candidate_in_returned_candidates=any(c.id == view.selection.candidate_id for c in view.candidates),
        selected_date=view.selected_date.model_dump() if view.selected_date else None,
        stable_selected_date=stable.selected_date.model_dump() if stable.selected_date else None,
        selected_selection_is_concurrent=view.selection.id == writer_result['selection_id'],
        database_is_owned_throwaway=True)
    print(json.dumps(output, sort_keys=True))
    assert triggered and view.selection.id == writer_result['selection_id']
    assert view.selected_date is None and stable.selected_date.value == '2025-03-01'
    await services.aclose()


try:
    asyncio.run(main())
finally:
    publication.close()
    database.close()
    patch.undo()
