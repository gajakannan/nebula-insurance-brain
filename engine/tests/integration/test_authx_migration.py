"""F0002-S0001 (ADR-0061) migration proof on real PostgreSQL.

Each test owns a fresh throwaway database: legacy F0001-shaped data is written at
revision 0004, then 0005 (expand) -> reviewed reconciliation -> 0006 (constrain).
Proves: existing IDs and legacy audit rows survive byte-for-byte; 0006 refuses to
constrain un-reconciled data without changing the schema; reconciliation needs the
reviewed digest, is all-or-nothing, and re-applying it is a no-op; the constrained
database rejects cross-owner writes; invalid job UUID text stops 0005.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

import psycopg
import pytest
from alembic import command
from alembic.config import Config
from psycopg import sql

REPO_ROOT = Path(__file__).resolve().parents[3]
ALEMBIC_INI = REPO_ROOT / "engine" / "migrations" / "alembic.ini"
RECONCILE = REPO_ROOT / "scripts" / "dev" / "reconcile_authx.py"
ADMIN_URL = os.environ.get(
    "BRAIN_MIGRATION_ADMIN_URL", "postgresql://brain:brain@localhost:5432/brain"
)


@pytest.fixture
def fresh_db(monkeypatch: pytest.MonkeyPatch) -> Iterator[str]:
    name = f"brain_f0002_mig_{uuid4().hex[:12]}"
    try:
        admin = psycopg.connect(ADMIN_URL, autocommit=True, connect_timeout=3)
    except psycopg.OperationalError as exc:
        pytest.skip(f"Postgres not reachable: {exc}")
    with admin:
        admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
    base = ADMIN_URL.rsplit("/", 1)[0]
    url = f"{base}/{name}"
    with psycopg.connect(url, autocommit=True) as conn:
        conn.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")
    monkeypatch.setenv("BRAIN_DATABASE_URL", url.replace("postgresql://", "postgresql+psycopg://"))
    try:
        yield url
    finally:
        with psycopg.connect(ADMIN_URL, autocommit=True) as admin:
            admin.execute(
                sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(sql.Identifier(name))
            )


def migrate(revision: str) -> None:
    config = Config(str(ALEMBIC_INI))
    config.set_main_option("script_location", str(ALEMBIC_INI.parent))
    command.upgrade(config, revision)


def version(url: str) -> str:
    with psycopg.connect(url) as conn:
        return conn.execute("SELECT version_num FROM alembic_version").fetchone()[0]


def reconcile(url: str, mapping: Path, *extra: str) -> subprocess.CompletedProcess[str]:
    env = os.environ | {"BRAIN_DATABASE_URL": url.replace("postgresql://", "postgresql+psycopg://")}
    return subprocess.run(
        [sys.executable, str(RECONCILE), "--mapping", str(mapping), *extra],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )


class Legacy:
    """One tenant, two KBs; F0001 rows exactly as the 0001-0004 schema allows."""

    def __init__(self) -> None:
        self.tenant, self.kb1, self.kb2, self.workspace = uuid4(), uuid4(), uuid4(), uuid4()
        self.user, self.service = uuid4(), uuid4()
        self.m_user, self.m_service = uuid4(), uuid4()
        self.source, self.version, self.artifact, self.run = uuid4(), uuid4(), uuid4(), uuid4()
        self.assertion, self.evidence = uuid4(), uuid4()
        self.batch, self.item, self.item2 = uuid4(), uuid4(), uuid4()
        self.entity, self.slot, self.fact, self.commit = uuid4(), uuid4(), uuid4(), uuid4()
        self.outbox, self.audit = uuid4(), uuid4()
        self.job = uuid4()

    def write(self, url: str, *, mixed_batch: bool = False, bad_job_id: bool = False) -> None:
        t, kb1 = str(self.tenant), str(self.kb1)
        with psycopg.connect(url) as conn:
            x = conn.execute
            x(
                "INSERT INTO principal (id, kind, issuer, subject, status) VALUES "
                "(%s,'user','https://idp','alice','active'), (%s,'service','https://idp','svc','active')",
                (self.user, self.service),
            )
            x(
                "INSERT INTO membership (id, principal_id, tenant_id, knowledge_base_id, role, "
                "grant_revision) VALUES (%s,%s,%s,%s,'Reviewer',3), (%s,%s,%s,%s,'ServicePrincipal',1)",
                (self.m_user, self.user, t, kb1, self.m_service, self.service, t, kb1),
            )
            x(
                "INSERT INTO source_document (id, tenant_id, knowledge_base_id, source_sha256) "
                "VALUES (%s,%s,%s,'a')",
                (self.source, t, kb1),
            )
            x(
                "INSERT INTO document_version (id, source_document_id) VALUES (%s,%s)",
                (self.version, self.source),
            )
            x(
                "INSERT INTO content_artifact (id, document_version_id, artifact_sha256, page_count, "
                "extraction_status) VALUES (%s,%s,'b',1,'complete')",
                (self.artifact, self.version),
            )
            x(
                "INSERT INTO semantic_interpretation_run (id, artifact_id, profile_id, profile_version, "
                "status, counters, run_configuration) VALUES (%s,%s,'p','1','complete','{}','{}')",
                (self.run, self.artifact),
            )
            x(
                "INSERT INTO assertion (id, run_id, origin, version, subject_type, slot_type, value, "
                "interpretation_basis) VALUES (%s,%s,'MACHINE_EXTRACTION',1,'Policy','limit','{}','EXPLICIT')",
                (self.assertion, self.run),
            )
            x(
                "INSERT INTO assertion_evidence (id, assertion_id, artifact_id, precision) "
                "VALUES (%s,%s,%s,'span')",
                (self.evidence, self.assertion, self.artifact),
            )
            x(
                "INSERT INTO review_batch (id, assembling_principal_id) VALUES (%s,%s)",
                (self.batch, self.user),
            )
            x(
                "INSERT INTO review_item (id, type, status, assertion_id, assertion_version, tenant_id, "
                "knowledge_base_id, review_batch_id) VALUES (%s,'LOW','open',%s,1,%s,%s,%s)",
                (self.item, self.assertion, t, kb1, self.batch),
            )
            if mixed_batch:
                x(
                    "INSERT INTO review_item (id, type, status, assertion_id, assertion_version, "
                    "tenant_id, knowledge_base_id, review_batch_id) VALUES (%s,'LOW','open',%s,1,%s,%s,%s)",
                    (self.item2, self.assertion, t, str(self.kb2), self.batch),
                )
            x(
                "INSERT INTO fact_slot (id, entity_id, slot_type, tenant_id, knowledge_base_id) "
                "VALUES (%s,%s,'limit',%s,%s)",
                (self.slot, self.entity, t, kb1),
            )
            x(
                "INSERT INTO canonical_fact_version (id, slot_id, tenant_id, knowledge_base_id, value, "
                "valid, recorded, evidence, commit_id, source_received_at, artifact_created_at, "
                "assertion_created_at, canonical_accepted_at) VALUES (%s,%s,%s,%s,'{}', "
                "tstzrange('2026-01-01', NULL), tstzrange('2026-01-10', NULL), '{}', %s, now(), now(), "
                "now(), now())",
                (self.fact, self.slot, t, kb1, self.commit),
            )
            x(
                "INSERT INTO outbox_event (id, commit_id, payload) VALUES (%s,%s,'{\"k\": 1}')",
                (self.outbox, self.commit),
            )
            x(
                "INSERT INTO audit_event (id, occurred_at, actor_principal_id, resource_type, "
                "resource_id, action, decision, reason_code, policy_hash, grant_revision, trace_id) "
                "VALUES (%s,'2026-09-01 10:00',%s,'content_artifact',%s,'read',true,'allowed','h',3,'t')",
                (self.audit, self.user, self.artifact),
            )
            job_id = "not-a-uuid" if bad_job_id else str(self.job)
            x(
                "INSERT INTO document_job (id, tenant_id, knowledge_base_id, artifact_id, request_key, "
                "payload, state, attempt, max_attempts, generation, available_at, leased_until) "
                "VALUES (%s,%s,%s,%s,'k','{}','queued',0,3,0,0,0)",
                (job_id, t, kb1, str(self.artifact)),
            )

    def mapping(self, path: Path) -> Path:
        uid = str
        mapping = {
            "version": 1,
            "tenants": [
                {
                    "id": uid(self.tenant),
                    "workspaces": [
                        {
                            "id": uid(self.workspace),
                            "knowledge_bases": [uid(self.kb1), uid(self.kb2)],
                        }
                    ],
                }
            ],
            "entities": [
                {
                    "id": uid(self.entity),
                    "tenant_id": uid(self.tenant),
                    "namespace": "account",
                    "external_key": "ACME-1",
                }
            ],
            "memberships": [
                {
                    "id": uid(m),
                    "valid_from": "2026-09-01T00:00:00+00:00",
                    "expires_at": None,
                    "selectors": [
                        {"kind": k, "mode": "all", "ids": []}
                        for k in ("broker", "account", "policy")
                    ],
                    "classifications": ["internal"],
                    "source_acl_ids": "*",
                }
                for m in (self.m_user, self.m_service)
            ],
            "resources": [
                {
                    "type": "content_artifact",
                    "id": uid(self.artifact),
                    "classifications": ["internal"],
                },
                {
                    "type": "review_task",
                    "id": uid(self.item),
                    "classifications": ["internal"],
                    "dependency_keys": [{"type": "content_artifact", "id": uid(self.artifact)}],
                },
                {"type": "fact_slot", "id": uid(self.slot), "classifications": ["internal"]},
            ],
        }
        path.write_text(json.dumps(mapping))
        return path


def _ids(url: str) -> dict[str, list[str]]:
    tables = (
        "principal",
        "membership",
        "source_document",
        "document_version",
        "content_artifact",
        "semantic_interpretation_run",
        "assertion",
        "assertion_evidence",
        "review_item",
        "review_batch",
        "fact_slot",
        "canonical_fact_version",
        "outbox_event",
    )
    with psycopg.connect(url) as conn:
        return {
            t: [str(r[0]) for r in conn.execute(f"SELECT id FROM {t} ORDER BY id")] for t in tables
        }


def _legacy_audit_digest(url: str, audit_id: UUID) -> str:
    with psycopg.connect(url) as conn:
        row = conn.execute(
            "SELECT id, occurred_at, actor_principal_id, delegate_principal_id, resource_type, "
            "resource_id, action, decision, reason_code, policy_hash, grant_revision, trace_id "
            "FROM audit_event WHERE id = %s",
            (audit_id,),
        ).fetchone()
    return hashlib.sha256(repr(row).encode()).hexdigest()


def _constraint_exists(url: str, name: str) -> bool:
    with psycopg.connect(url) as conn:
        return (
            conn.execute("SELECT 1 FROM pg_constraint WHERE conname = %s", (name,)).fetchone()
            is not None
        )


def test_expand_reconcile_constrain_preserves_ids_and_enforces_ownership(
    fresh_db: str, tmp_path: Path
) -> None:
    legacy = Legacy()
    migrate("0004")
    legacy.write(fresh_db)
    ids_before = _ids(fresh_db)
    audit_before = _legacy_audit_digest(fresh_db, legacy.audit)

    migrate("0005")
    with psycopg.connect(fresh_db) as conn:
        aliases = conn.execute("SELECT count(*) FROM external_identity").fetchone()[0]
        revision = conn.execute(
            "SELECT revision FROM principal_authority WHERE principal_id = %s", (legacy.user,)
        ).fetchone()[0]
        job_type = conn.execute(
            "SELECT data_type FROM information_schema.columns "
            "WHERE table_name = 'document_job' AND column_name = 'id'"
        ).fetchone()[0]
    assert aliases == 2 and revision == 3 and job_type == "uuid"

    # 0006 refuses un-reconciled data and leaves the schema exactly as 0005 left it.
    with pytest.raises(RuntimeError, match="0006 preflight failed"):
        migrate("0006")
    assert version(fresh_db) == "0005"
    assert not _constraint_exists(fresh_db, "fk_document_version_source_document_id_owner")

    mapping = legacy.mapping(tmp_path / "mapping.json")
    dry = reconcile(fresh_db, mapping, "--dry-run")
    assert dry.returncode == 0, dry.stdout + dry.stderr
    report = json.loads(dry.stdout)
    assert report["blocking"] == [] and "alice" not in dry.stdout  # counts/IDs only
    wrong = reconcile(
        fresh_db,
        mapping,
        "--apply",
        "--expected-digest",
        "0" * 64,
        "--actor-id",
        str(uuid4()),
        "--approval-ref",
        "CHG-1",
    )
    assert wrong.returncode != 0
    operator = uuid4()
    applied = reconcile(
        fresh_db,
        mapping,
        "--apply",
        "--expected-digest",
        report["digest"],
        "--actor-id",
        str(operator),
        "--approval-ref",
        "CHG-1",
        "--activate-policy",
    )
    assert applied.returncode == 0, applied.stderr
    assert json.loads(applied.stdout)["status"] == "applied"
    again = reconcile(
        fresh_db,
        mapping,
        "--apply",
        "--expected-digest",
        report["digest"],
        "--actor-id",
        str(operator),
        "--approval-ref",
        "CHG-1",
    )
    assert json.loads(again.stdout)["status"] == "no-op"

    migrate("0006")
    assert version(fresh_db) == "0006"
    assert _ids(fresh_db) == ids_before  # no ID rewritten, nothing deleted
    assert _legacy_audit_digest(fresh_db, legacy.audit) == audit_before  # history untouched

    with psycopg.connect(fresh_db) as conn:
        owner = conn.execute(
            "SELECT tenant_id, knowledge_base_id FROM assertion_evidence WHERE id = %s",
            (legacy.evidence,),
        ).fetchone()
        assert tuple(map(str, owner)) == (str(legacy.tenant), str(legacy.kb1))
        slice_row = conn.execute(
            "SELECT valid_from IS NOT NULL, selectors FROM membership WHERE id = %s",
            (legacy.m_user,),
        ).fetchone()
        assert slice_row[0] and len(slice_row[1]) == 3
        assert conn.execute("SELECT count(*) FROM canonical_commit").fetchone()[0] == 1
        assert (
            conn.execute(
                "SELECT count(*) FROM audit_event WHERE event_type = 'scope_reconciled'"
            ).fetchone()[0]
            == 1
        )

    other_tenant = uuid4()
    violations = [
        # A child whose owner disagrees with its parent (S0001 AC2 / EX-AUTHX-001).
        (
            "INSERT INTO document_version (id, source_document_id, tenant_id, knowledge_base_id) "
            "VALUES (%s,%s,%s,%s)",
            (uuid4(), legacy.source, other_tenant, legacy.kb1),
        ),
        # A KB-scoped row naming a KB that is not registered to that tenant.
        (
            "INSERT INTO source_document (id, tenant_id, knowledge_base_id, source_sha256) "
            "VALUES (%s,%s,%s,'z')",
            (uuid4(), other_tenant, legacy.kb1),
        ),
        # A fact slot for an entity identity owned by another tenant.
        (
            "INSERT INTO fact_slot (id, entity_id, slot_type, tenant_id, knowledge_base_id) "
            "VALUES (%s,%s,'x',%s,%s)",
            (uuid4(), uuid4(), legacy.tenant, legacy.kb1),
        ),
        # A membership with no restriction slice.
        (
            "INSERT INTO membership (id, principal_id, tenant_id, knowledge_base_id, role, "
            "grant_revision, valid_from) VALUES (%s,%s,%s,%s,'Reviewer',1,now())",
            (uuid4(), legacy.user, legacy.tenant, legacy.kb1),
        ),
        # A KB attached to a workspace of another tenant.
        (
            "INSERT INTO knowledge_base (id, workspace_id, tenant_id, created_at, created_by) "
            "VALUES (%s,%s,%s,now(),%s)",
            (uuid4(), legacy.workspace, other_tenant, uuid4()),
        ),
    ]
    expected = [
        "fk_document_version_source_document_id_owner",
        "fk_source_document_kb_owner",
        "fk_fact_slot_entity_owner",
        None,  # NOT NULL on the membership slice columns
        "fk_kb_workspace_owner",
    ]
    for (statement, params), constraint in zip(violations, expected, strict=True):
        with psycopg.connect(fresh_db) as conn, pytest.raises(psycopg.errors.IntegrityError) as exc:
            conn.execute(statement, params)
        if constraint is None:
            assert isinstance(exc.value, psycopg.errors.NotNullViolation)
        else:
            assert exc.value.diag.constraint_name == constraint


def test_mixed_kb_batch_blocks_reconciliation_without_partial_writes(
    fresh_db: str, tmp_path: Path
) -> None:
    legacy = Legacy()
    migrate("0004")
    legacy.write(fresh_db, mixed_batch=True)
    migrate("0005")
    mapping = legacy.mapping(tmp_path / "mapping.json")
    dry = reconcile(fresh_db, mapping, "--dry-run")
    report = json.loads(dry.stdout)
    assert dry.returncode == 1 and "review_batch_mixed_kb" in report["blocking"]
    assert report["conflicts"]["review_batch_mixed_kb"] == [str(legacy.batch)]
    applied = reconcile(
        fresh_db,
        mapping,
        "--apply",
        "--expected-digest",
        report["digest"],
        "--actor-id",
        str(uuid4()),
        "--approval-ref",
        "CHG-2",
    )
    assert applied.returncode == 1 and "rejected" in applied.stderr
    with psycopg.connect(fresh_db) as conn:
        for table in (
            "tenant",
            "workspace",
            "knowledge_base",
            "resource_access",
            "entity_identity",
        ):
            assert conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0] == 0, table
        assert (
            conn.execute(
                "SELECT count(*) FROM document_version WHERE tenant_id IS NOT NULL"
            ).fetchone()[0]
            == 0
        )
    with pytest.raises(RuntimeError, match="review batches spanning more than one KB"):
        migrate("0006")


def test_invalid_job_uuid_text_stops_expand_before_any_change(fresh_db: str) -> None:
    legacy = Legacy()
    migrate("0004")
    legacy.write(fresh_db, bad_job_id=True)
    with pytest.raises(RuntimeError, match="document_job.id: 1 invalid UUID values"):
        migrate("0005")
    assert version(fresh_db) == "0004"
    with psycopg.connect(fresh_db) as conn:
        assert conn.execute("SELECT to_regclass('public.tenant')").fetchone()[0] is None
    assert datetime.now(UTC)  # the run is wall-clock independent


def test_safeguards_make_ownership_immutable_audit_append_only_and_restore_deferrable(
    fresh_db: str, tmp_path: Path
) -> None:
    """0007 (BLUEPRINT §4.11, operator scope amendment at G4)."""
    legacy = Legacy()
    migrate("0004")
    legacy.write(fresh_db)
    migrate("0005")
    mapping = legacy.mapping(tmp_path / "mapping.json")
    digest = json.loads(reconcile(fresh_db, mapping, "--dry-run").stdout)["digest"]
    applied = reconcile(
        fresh_db,
        mapping,
        "--apply",
        "--expected-digest",
        digest,
        "--actor-id",
        str(uuid4()),
        "--approval-ref",
        "CHG-7",
    )
    assert applied.returncode == 0, applied.stderr
    migrate("head")
    assert version(fresh_db) == "0007"

    rewrites = [
        ("UPDATE document_version SET tenant_id = %s WHERE id = %s", (uuid4(), legacy.version)),
        ("UPDATE review_item SET knowledge_base_id = %s WHERE id = %s", (legacy.kb2, legacy.item)),
        (
            "UPDATE resource_access SET knowledge_base_id = %s WHERE resource_id = %s",
            (legacy.kb2, legacy.artifact),
        ),
        ("UPDATE membership SET principal_id = %s WHERE id = %s", (legacy.service, legacy.m_user)),
        ("UPDATE knowledge_base SET workspace_id = %s WHERE id = %s", (uuid4(), legacy.kb1)),
        (
            "UPDATE external_identity SET principal_id = %s WHERE subject = 'alice'",
            (legacy.service,),
        ),
        ("UPDATE audit_event SET reason_code = 'rewritten' WHERE id = %s", (legacy.audit,)),
        ("DELETE FROM audit_event WHERE id = %s", (legacy.audit,)),
    ]
    for statement, params in rewrites:
        with psycopg.connect(fresh_db) as conn, pytest.raises(psycopg.errors.CheckViolation) as exc:
            conn.execute(statement, params)
        assert "immutable" in str(exc.value) or "append-only" in str(exc.value), statement
    # Non-ownership updates keep working (revocation, status, fact supersession).
    with psycopg.connect(fresh_db) as conn:
        conn.execute("UPDATE membership SET revoked_at = now() WHERE id = %s", (legacy.m_user,))
        conn.execute("UPDATE review_item SET status = 'decided' WHERE id = %s", (legacy.item,))

    # Restore order: a correction may be loaded before its original when deferred.
    original, correction = uuid4(), uuid4()
    insert = (
        "INSERT INTO assertion (id, run_id, origin, original_assertion_id, version, subject_type, "
        "slot_type, value, interpretation_basis, tenant_id, knowledge_base_id) "
        "VALUES (%s, NULL, %s, %s, 1, 'Policy', 'limit', '{}', 'EXPLICIT', %s, %s)"
    )
    with psycopg.connect(fresh_db) as conn, pytest.raises(psycopg.errors.ForeignKeyViolation):
        conn.execute(insert, (correction, "HUMAN_REVIEW", original, legacy.tenant, legacy.kb1))
    with psycopg.connect(fresh_db) as conn:
        conn.execute("SET CONSTRAINTS ALL DEFERRED")
        conn.execute(insert, (correction, "HUMAN_REVIEW", original, legacy.tenant, legacy.kb1))
        conn.execute(insert, (original, "MACHINE_EXTRACTION", None, legacy.tenant, legacy.kb1))
    with psycopg.connect(fresh_db) as conn:
        assert (
            conn.execute(
                "SELECT count(*) FROM assertion WHERE id IN (%s, %s)", (original, correction)
            ).fetchone()[0]
            == 2
        )
