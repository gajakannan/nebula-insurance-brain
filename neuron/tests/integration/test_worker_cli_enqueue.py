"""F0002-S0004 trusted submission: `worker_cli --enqueue` declares the artifact's
restrictions (no default label) and provisions its security metadata before the
shared evaluator authorizes ingest/interpret. Real PostgreSQL, isolated schema."""

from __future__ import annotations

import os
import sys
from collections.abc import Iterator
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from brain_content.config import LocalObjectStoreConfig
from brain_domain.principal import PrincipalKind
from brain_ingestion import worker_cli
from brain_jobs.queue import jobs, metadata
from brain_persistence.base import Base
from brain_persistence.models import AuditEventRow, ResourceAccessRow
from brain_testing import fixtures
from sqlalchemy import create_engine, select, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

ROOT = Path(__file__).resolve().parents[3]
POLICY = ROOT / "planning-mds/security/policies"


@pytest.fixture
def database() -> Iterator[tuple[Engine, str]]:
    url = os.environ.get("BRAIN_TEST_POSTGRES_URL")
    if not url:
        pytest.skip("set BRAIN_TEST_POSTGRES_URL for the PostgreSQL enqueue proof")
    schema = f"enqueue_proof_{uuid4().hex}"
    admin = create_engine(url)
    with admin.begin() as conn:
        conn.execute(text(f'CREATE SCHEMA "{schema}"'))
    scoped_url = f"{url}?options=-csearch_path%3D{schema}"
    engine = create_engine(scoped_url)
    try:
        metadata.create_all(engine)
        with engine.begin() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS btree_gist SCHEMA public"))
        Base.metadata.create_all(engine)
        yield engine, scoped_url
    finally:
        engine.dispose()
        with admin.begin() as conn:
            conn.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        admin.dispose()


def _seed(engine: Engine) -> tuple[UUID, UUID, UUID]:
    tenant, kb = uuid4(), uuid4()
    with Session(engine) as session, session.begin():
        fixtures.activate_policy(session, POLICY / "model.conf", POLICY / "policy.csv")
        service = fixtures.seed_principal(
            session, issuer="local", subject="ingest-submitter", kind=PrincipalKind.SERVICE
        )
        fixtures.seed_grant(session, service.id, tenant, kb, "ServicePrincipal")
    return tenant, kb, service.id


def _run(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, url: str, actor: UUID, argv: list[str]
) -> int:
    monkeypatch.setenv("BRAIN_ENABLE_GRAPH_CANDIDATE", "1")
    monkeypatch.setenv("BRAIN_WORKER_DATABASE_URL", url)
    monkeypatch.setenv("BRAIN_WORKER_PRINCIPAL_ID", str(actor))
    monkeypatch.setattr(
        worker_cli,
        "load_local_object_store_config",
        lambda: LocalObjectStoreConfig("filesystem", tmp_path / "objects", True),
    )
    monkeypatch.setattr(sys, "argv", ["worker_cli", "--policy-dir", str(POLICY), *argv])
    return worker_cli.main()


def test_enqueue_provisions_declared_restrictions_then_authorizes(
    database: tuple[Engine, str], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    engine, url = database
    tenant, kb, actor = _seed(engine)
    pdf = tmp_path / "policy.pdf"
    pdf.write_bytes(b"%PDF-1.4 synthetic")
    args = ["--enqueue", str(pdf), "--tenant", str(tenant), "--knowledge-base", str(kb)]

    with pytest.raises(SystemExit):  # no default label: a classification is mandatory
        _run(monkeypatch, tmp_path, url, actor, args)
    with Session(engine) as session:
        assert session.scalars(select(ResourceAccessRow)).all() == []

    assert (
        _run(
            monkeypatch,
            tmp_path,
            url,
            actor,
            [*args, "--classification", "internal", "--source-acl", "acl-broker"],
        )
        == 0
    )
    with Session(engine) as session:
        access = session.scalars(select(ResourceAccessRow)).one()
        assert (access.tenant_id, access.knowledge_base_id) == (tenant, kb)
        assert access.classifications == ["internal"] and access.source_acl_ids == ["acl-broker"]
        decisions = session.scalars(
            select(AuditEventRow).where(AuditEventRow.event_type == "authorization_decision")
        ).all()
        assert sorted(d.action for d in decisions) == ["ingest", "interpret"]
        assert all(d.decision and d.actor_principal_id == actor for d in decisions)
        assert session.scalar(select(jobs.c.state)) == "queued"


def test_enqueue_beyond_queue_depth_is_rejected_explicitly(
    database: tuple[Engine, str],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    import yaml  # type: ignore[import-untyped]

    engine, url = database
    tenant, kb, actor = _seed(engine)
    config = tmp_path / "local.yaml"
    config.write_text(
        yaml.safe_dump(
            {
                "content": {"v2_writer_enabled": False},
                "extraction": {"pipeline": "direct-baseline"},
                "jobs": {"max_queue_depth": 1},
                "object_store": {"provider": "filesystem", "root": str(tmp_path / "objects")},
            }
        )
    )
    monkeypatch.setenv("BRAIN_LOCAL_CONFIG_PATH", str(config))
    outcomes = []
    for name in ("first.pdf", "second.pdf"):
        pdf = tmp_path / name
        pdf.write_bytes(b"%PDF-1.4 synthetic " + name.encode())
        args = [
            "--enqueue",
            str(pdf),
            "--tenant",
            str(tenant),
            "--knowledge-base",
            str(kb),
            "--classification",
            "internal",
        ]
        outcomes.append(_run(monkeypatch, tmp_path, url, actor, args))
    assert outcomes == [0, 4]
    assert capsys.readouterr().out.strip().splitlines()[-1] == "queue_depth_exceeded"
    with Session(engine) as session:
        assert len(session.execute(select(jobs.c.id)).all()) == 1
    # The rejected source was never stored as accepted work.
    assert len(list((tmp_path / "objects" / "sources").rglob("*.pdf"))) == 1
