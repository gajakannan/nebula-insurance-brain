"""F0005 migrations 0009/0010: expand-only job failure reasons, upgrade and restore drill."""

from __future__ import annotations

import os
import runpy
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

import psycopg
import pytest
from alembic import command
from brain_jobs.queue import FAILURE_REASONS, DocumentJobQueue
from brain_testing import fixtures
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

PRODUCT = Path(__file__).resolve().parents[3]
_helpers = runpy.run_path(str(Path(__file__).with_name("test_content_migration_states.py")))
database = _helpers["database"]
configuration = _helpers["configuration"]
_clean_fact_tables = _helpers["_clean_fact_tables"]
_migration = runpy.run_path(
    str(PRODUCT / "engine/migrations/versions/0009_f0005_job_event_reason.py")
)
_expansion = runpy.run_path(
    str(PRODUCT / "engine/migrations/versions/0010_f0005_job_event_reason_expand.py")
)


def _legacy_job(url: str) -> tuple[str, str]:
    """A pre-0009 job and event written without any reason column."""
    job, event = str(uuid4()), str(uuid4())
    tenant, kb = uuid4(), uuid4()
    engine = create_engine(url.replace("postgresql://", "postgresql+psycopg://"))
    with Session(engine) as session, session.begin():
        fixtures.seed_scope(session, tenant, kb)
    engine.dispose()
    with psycopg.connect(url, autocommit=True) as connection:
        connection.execute(
            "INSERT INTO document_job (id, tenant_id, knowledge_base_id, artifact_id, request_key,"
            " payload, state, attempt, max_attempts, generation, available_at, leased_until)"
            " VALUES (%s,%s,%s,%s,'legacy','{}','retry',1,3,1,0,0)",
            (job, str(tenant), str(kb), str(uuid4())),
        )
        connection.execute(
            "INSERT INTO document_job_event (id, job_id, generation, event, occurred_at)"
            " VALUES (%s,%s,1,'retry',1)",
            (event, job),
        )
    return job, event


def test_queue_reasons_match_the_frozen_migration_enumeration():
    assert set(_expansion["REASONS"]) == FAILURE_REASONS
    # 0010 only adds: every 0009 value keeps its meaning.
    assert _expansion["PREVIOUS"] == _migration["REASONS"]


def _insert_reason(url: str, job: str, reason: str) -> None:
    with psycopg.connect(url, autocommit=True) as connection:
        connection.execute(
            "INSERT INTO document_job_event (id, job_id, generation, event, occurred_at, reason)"
            " VALUES (%s,%s,1,'retry',5,%s)",
            (str(uuid4()), job, reason),
        )


@pytest.mark.parametrize("reason", _expansion["ADDED"])
def test_expansion_admits_new_reasons_only_after_0010(database, reason):
    config = configuration()
    command.upgrade(config, "0009")
    job, _event = _legacy_job(database)
    with pytest.raises(psycopg.errors.CheckViolation):
        _insert_reason(database, job, reason)
    command.upgrade(config, "0010")
    _insert_reason(database, job, reason)
    _insert_reason(database, job, "conversion_timeout")  # 0009 values still admitted
    # Recorded expanded reasons are history: downgrade refuses to narrow under them.
    with pytest.raises(RuntimeError, match="expanded failure reasons exist"):
        command.downgrade(config, "0009")


def test_expansion_downgrade_without_new_reasons_restores_the_0009_constraint(database):
    config = configuration()
    command.upgrade(config, "0010")
    job, _event = _legacy_job(database)
    _insert_reason(database, job, "model_timeout")
    command.downgrade(config, "0009")
    with pytest.raises(psycopg.errors.CheckViolation):
        _insert_reason(database, job, "interpretation_failed")
    command.upgrade(config, "0010")


def test_upgrade_keeps_history_null_and_constrains_new_reasons(database):
    config = configuration()
    command.upgrade(config, "0008")
    job, event = _legacy_job(database)
    command.upgrade(config, "0009")
    with psycopg.connect(database, autocommit=True) as connection:
        assert connection.execute("SELECT version_num FROM alembic_version").fetchone()[0] == "0009"
        assert connection.execute(
            "SELECT event, reason FROM document_job_event WHERE id=%s", (event,)
        ).fetchone() == ("retry", None)
        with pytest.raises(psycopg.errors.CheckViolation):
            connection.execute(
                "INSERT INTO document_job_event (id, job_id, generation, event, occurred_at,"
                " reason) VALUES (%s,%s,1,'retry',2,'provider said something')",
                (str(uuid4()), job),
            )
    # The application queue writes reasons through the migrated column.
    engine = create_engine(database.replace("postgresql://", "postgresql+psycopg://"))
    queue = DocumentJobQueue(engine)
    with psycopg.connect(database, autocommit=True) as connection:
        tenant, kb = connection.execute(
            "SELECT tenant_id, knowledge_base_id FROM document_job WHERE id=%s", (job,)
        ).fetchone()
    queue.enqueue(
        tenant_id=tenant, knowledge_base_id=kb, artifact_id=uuid4(), request_key="new", payload={}
    )
    lease = queue.claim()
    assert lease is not None
    queue.retry(lease, reason="conversion_timeout")
    engine.dispose()
    with psycopg.connect(database) as connection:
        assert connection.execute(
            "SELECT reason FROM document_job_event WHERE job_id=%s AND event='retry'",
            (str(lease.job_id),),
        ).fetchone() == ("conversion_timeout",)
    # Recorded reasons are audit history: downgrade refuses instead of dropping them.
    with pytest.raises(RuntimeError, match="failure reasons exist"):
        command.downgrade(config, "0008")


def test_downgrade_without_reasons_is_safe_and_reupgrade_is_idempotent(database):
    config = configuration()
    command.upgrade(config, "0009")
    command.downgrade(config, "0008")
    with psycopg.connect(database) as connection:
        columns = {
            row[0]
            for row in connection.execute(
                "SELECT column_name FROM information_schema.columns"
                " WHERE table_name='document_job_event'"
            )
        }
    assert "reason" not in columns
    command.upgrade(config, "0009")


def test_backup_and_isolated_restore_preserve_reason_column_and_rows(database, tmp_path):
    config = configuration()
    command.upgrade(config, "0009")
    job, legacy_event = _legacy_job(database)
    reasoned = str(uuid4())
    with psycopg.connect(database, autocommit=True) as connection:
        connection.execute(
            "INSERT INTO document_job_event (id, job_id, generation, event, occurred_at, reason)"
            " VALUES (%s,%s,1,'failed',3,'model_timeout')",
            (reasoned, job),
        )
    environment = os.environ | {
        "BRAIN_WRITERS_QUIESCED": "1",
        "BRAIN_OPS_PYTHON": sys.executable,
        "BRAIN_OPS_DATABASE_URL": database,
        "BRAIN_POSTGRES_DATABASE": database.rsplit("/", 1)[1],
        "BRAIN_CONTENT_ROOT": str(tmp_path),
        "BRAIN_BACKUP_ROOT": str(tmp_path.parent / (tmp_path.name + "-backups")),
    }
    backup = subprocess.run(
        ["bash", str(PRODUCT / "scripts/ops/backup.sh")],
        env=environment,
        text=True,
        capture_output=True,
        timeout=60,
    )
    assert backup.returncode == 0, backup.stdout + backup.stderr
    destination = Path(backup.stdout.split("Backup complete: ")[1].strip())
    restored = subprocess.run(
        ["bash", str(PRODUCT / "scripts/ops/restore.sh"), str(destination), "--keep"],
        env=environment,
        text=True,
        capture_output=True,
        timeout=100,
    )
    container = None
    try:
        assert restored.returncode == 0, restored.stdout + restored.stderr
        assert "Restore drill PASSED" in restored.stdout
        container = restored.stdout.split("Kept isolated target: ")[1].split(";")[0].strip()
        query = (
            "SELECT id, reason FROM document_job_event ORDER BY occurred_at;"
            "SELECT conname FROM pg_constraint WHERE conname='ck_document_job_event_reason';"
            "SELECT version_num FROM alembic_version;"
        )
        out = subprocess.run(
            [
                "docker",
                "exec",
                "-e",
                "PGPASSWORD=brain",
                container,
                "psql",
                "-h",
                "127.0.0.1",
                "-U",
                "brain",
                "-d",
                "brain",
                "-At",
                "-F",
                "|",
                "-c",
                query,
            ],
            text=True,
            capture_output=True,
            timeout=30,
        )
        assert out.returncode == 0, out.stderr
        lines = out.stdout.split()
        assert f"{legacy_event}|" in lines
        assert f"{reasoned}|model_timeout" in lines
        assert "ck_document_job_event_reason" in lines and "0009" in lines
    finally:
        if container:
            subprocess.run(["docker", "rm", "-f", container], capture_output=True, timeout=60)
        kept = (
            restored.stdout.split("content: ")[-1].split()[0]
            if "content: " in restored.stdout
            else ""
        )
        if kept.startswith("/tmp/"):
            subprocess.run(["rm", "-rf", kept], capture_output=True)
