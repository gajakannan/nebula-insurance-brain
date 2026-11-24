"""F0011 sweep failure semantics; successful history proof runs on PostgreSQL."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from brain_contracts.schema_runtime import ContractError
from sqlalchemy.engine import make_url

from scripts.contracts import check_stored_fact_versions as sweep


class _Stream:
    def __init__(self, rows, *, interrupted=False):
        self.rows = rows
        self.interrupted = interrupted
        self.closed = False

    def __aiter__(self):
        return self._iterate()

    async def _iterate(self):
        for row in self.rows:
            yield row
        if self.interrupted:
            raise OSError("protected data must never enter the result")

    async def close(self):
        self.closed = True


class _Session:
    def __init__(self, rows, *, expected=None, interrupted=False, unavailable=False):
        self.rows = rows
        self.expected = len(rows) if expected is None else expected
        self.stream = _Stream(rows, interrupted=interrupted)
        self.commands = []
        self.rolled_back = False
        self.unavailable = unavailable

    async def execute(self, statement):
        self.commands.append(str(statement))
        if self.unavailable:
            raise OSError("protected credential: do not expose")

    async def scalar(self, statement):
        sql = str(statement)
        self.commands.append(sql)
        if "transaction_read_only" in sql:
            return "on"
        if "transaction_isolation" in sql:
            return "repeatable read"
        if "current_database" in sql:
            return "owned-test"
        if "transaction_timestamp" in sql:
            return datetime(2026, 11, 22, tzinfo=UTC)
        return self.expected

    async def stream_scalars(self, statement):
        self.commands.append(str(statement))
        assert "WHERE" not in str(statement)
        return self.stream

    async def rollback(self):
        self.rolled_back = True


class _Out:
    def __init__(self, value):
        self.value = value

    @classmethod
    def from_domain(cls, value):
        return cls(value)

    def model_dump(self, *, mode):
        assert mode == "json"
        return self.value


def _row(*, temporal=None, closed=False, remainder=False):
    return SimpleNamespace(
        temporal_contract=temporal,
        recorded=SimpleNamespace(upper=datetime.now(UTC) if closed else None),
        split_of_version_id="synthetic" if remainder else None,
        change_reason="split" if remainder else None,
    )


@pytest.fixture(autouse=True)
def _adapter(monkeypatch):
    monkeypatch.setattr(
        sweep, "_fact_version_from_row", lambda row: {"valid_start": "bad-format"}
    )
    monkeypatch.setattr(sweep, "FactVersionOut", _Out)
    monkeypatch.setattr(sweep, "candidate_code_digest", lambda: "1" * 64)
    monkeypatch.setattr(sweep, "guard_fact_response", lambda payload: None)


async def _run(session, **kwargs):
    return await sweep.sweep_session(
        session,
        environment="integration",
        expected_database="owned-test",
        bundle_digest="0" * 64,
        code_revision="fixture",
        **kwargs,
    )


async def test_closed_history_legacy_and_remainders_are_all_enumerated():
    session = _Session(
        [_row(), _row(temporal=1, closed=True), _row(temporal=1, remainder=True)]
    )
    report, code = await _run(session)
    assert code == 0 and report["status"] == "pass"
    assert report["rows_expected"] == report["selected"] == report["checked"] == 3
    assert report["groups"] == {
        "legacy": 1,
        "temporal": 2,
        "closed_recorded": 1,
        "remainders": 1,
    }
    assert (
        session.commands[0]
        == "SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY"
    )
    assert session.rolled_back and session.stream.closed


async def test_source_format_guard_mismatch_is_counted_without_data(monkeypatch):
    def invalid(payload):
        assert payload["valid_start"] == "bad-format"
        raise ContractError(
            "CONTRACT_INSTANCE_INVALID", schema_pointer="/properties/valid_start"
        )

    monkeypatch.setattr(sweep, "guard_fact_response", invalid)
    report, code = await _run(_Session([_row()]))
    assert code == 1 and report["guard_failures"] == 1
    assert report["checked"] == report["selected"] == 1
    assert "bad-format" not in json.dumps(report)
    assert "schema_pointer" not in json.dumps(report)


async def test_mapping_failure_does_not_skip_a_row_or_leak_exception(monkeypatch):
    def invalid(row):
        raise ValueError("protected row identity")

    monkeypatch.setattr(sweep, "_fact_version_from_row", invalid)
    report, code = await _run(_Session([_row()]))
    assert code == 1 and report["mapping_failures"] == 1
    assert report["checked"] == 1
    assert "protected" not in json.dumps(report)


@pytest.mark.parametrize(
    "session", [_Session([_row()], expected=2), _Session([_row()], interrupted=True)]
)
async def test_incomplete_or_interrupted_enumeration_is_execution_failure(session):
    report, code = await _run(session)
    assert code == 2 and report["status"] == "error"
    assert session.rolled_back
    assert "protected" not in json.dumps(report)


async def test_unavailable_database_is_never_an_empty_pass():
    session = _Session([], unavailable=True)
    report, code = await _run(session, empty_inventory_verified=True)
    assert code == 2 and report["status"] == "error"
    assert report["read_only"] is False
    assert "protected" not in json.dumps(report)


async def test_empty_database_requires_explicit_signed_inventory():
    report, code = await _run(_Session([]))
    assert code == 2 and report["codes"] == ["CONTRACT_SWEEP_EMPTY_REQUIRES_INVENTORY"]
    report, code = await _run(_Session([]), empty_inventory_verified=True)
    assert code == 0 and report["zero_row_inventory_verified"] is True


def test_zero_row_inventory_requires_both_named_roles_and_iso_dates(tmp_path):
    path = tmp_path / "inventory.json"
    value = {
        "environment": "dev",
        "rows": 0,
        "quality_engineer": {"reviewer": "QE fixture", "date": "2026-11-22"},
        "devops": {"reviewer": "DevOps fixture", "date": "2026-11-22"},
    }
    path.write_text(json.dumps(value))
    assert sweep.zero_row_inventory(path, "dev")
    assert not sweep.zero_row_inventory(path, "integration")
    del value["quality_engineer"]
    path.write_text(json.dumps(value))
    assert not sweep.zero_row_inventory(path, "dev")


def test_named_environment_uses_inventoried_database_and_existing_configuration(
    tmp_path, monkeypatch
):
    path = tmp_path / "environments.json"
    path.write_text(
        json.dumps(
            {
                "dev": {"database": "existing-dev"},
                "integration": {
                    "database": "existing-integration",
                    "host": "postgres",
                    "port": 5432,
                },
            }
        )
    )
    monkeypatch.setattr(
        sweep.Settings,
        "from_env",
        lambda: SimpleNamespace(
            database_url="postgresql+asyncpg://fixture:synthetic@localhost:5433/default"
        ),
    )
    url, database = sweep.environment_target("integration", path)
    parsed = make_url(url)
    assert database == parsed.database == "existing-integration"
    assert (parsed.host, parsed.port, parsed.username, parsed.password) == (
        "postgres",
        5432,
        "fixture",
        "synthetic",
    )
    url, database = sweep.environment_target("dev", path)
    assert make_url(url).host == "localhost" and database == "existing-dev"
    path.write_text(json.dumps({"dev": {"database": "existing-dev"}}))
    with pytest.raises(
        sweep.SweepExecutionError, match="CONTRACT_SWEEP_ENVIRONMENT_UNAVAILABLE"
    ):
        sweep.environment_target("integration", path)


def test_explicit_revision_does_not_require_git_in_operator_container(monkeypatch):
    def unavailable(*args, **kwargs):
        raise FileNotFoundError

    monkeypatch.setattr(sweep.subprocess, "check_output", unavailable)
    assert sweep.resolve_code_revision("a" * 40) == "a" * 40
    with pytest.raises(
        sweep.SweepExecutionError, match="CONTRACT_SWEEP_CODE_IDENTITY_UNAVAILABLE"
    ):
        sweep.resolve_code_revision("not-a-full-code-revision")


def test_host_revision_fallback_is_checked(monkeypatch):
    monkeypatch.setattr(
        sweep.subprocess, "check_output", lambda *args, **kwargs: "b" * 40 + "\n"
    )
    assert sweep.resolve_code_revision(None) == "b" * 40
