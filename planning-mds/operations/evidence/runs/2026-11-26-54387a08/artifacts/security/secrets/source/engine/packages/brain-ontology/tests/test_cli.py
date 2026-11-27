"""CLI contract (PRD assumption A1): JSON on stdout; exit 0 ok, 1 refused/invalid, 2 usage."""

from __future__ import annotations

import json
from contextlib import asynccontextmanager
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from uuid import UUID, uuid4

import pytest
from brain_domain.authx import AuthorizationDecision
from brain_domain.ontology import OntologyReason, OntologyRefused
from brain_ontology import cli, runtime
from brain_security.execution import AuthorizationDenied
from brain_security.verification import CredentialError

REPO = Path(__file__).resolve().parents[4]
FOUNDATION_REQUEST = REPO / "ontology/releases/foundation/1/release.yaml"


def run(capsys: pytest.CaptureFixture[str], *argv: str) -> tuple[int, Any]:
    code = cli.main(list(argv))
    out = capsys.readouterr().out
    return code, json.loads(out) if out.strip() else None


def test_validate(capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    code, out = run(
        capsys,
        "--root",
        str(REPO),
        "validate",
        str(REPO / "ontology/modules/foundation/module.yaml"),
    )
    assert code == 0 and out["results"][0]["valid"] is True
    bad = tmp_path / "m.yaml"
    bad.write_text("authoring_schema: ontology-module-authoring/v1\n", encoding="utf-8")
    code, out = run(capsys, "--root", str(tmp_path), "validate", str(bad))
    assert code == 1 and out["results"][0]["errors"]


def test_compile_check_and_write(capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    code, out = run(capsys, "--root", str(REPO), "compile", "--check", str(FOUNDATION_REQUEST))
    assert code == 0 and out["status"] == "pass"
    request = tmp_path / "ontology/releases/demo/1/release.yaml"
    request.parent.mkdir(parents=True)
    (tmp_path / "m.yaml").write_text("not: [valid", encoding="utf-8")
    request.write_text("name: demo\nsequence: 1\nmodules: [../../../../m.yaml]\n", encoding="utf-8")
    code, out = run(capsys, "--root", str(tmp_path), "compile", str(request))
    assert code == 1 and out["errors"][0]["code"] == "YAML_INVALID"
    assert not (request.parent / "manifest.json").exists()  # no partial output


def test_compile_check_detects_stale_output(
    capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    import shutil

    target = tmp_path / "repo"
    shutil.copytree(REPO / "ontology", target / "ontology")
    for ref in (
        "planning-mds/domain/glossary.md",
        "planning-mds/architecture/master-blueprint.md",
        "planning-mds/examples/commercial-pc-account/records.json",
        "planning-mds/examples/commercial-pc-account/cases.md",
    ):
        (target / ref).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(REPO / ref, target / ref)
    (target / "ontology/releases/foundation/1/release.ttl").write_text("stale\n", encoding="utf-8")
    code, out = run(
        capsys,
        "--root",
        str(target),
        "compile",
        "--check",
        str(target / "ontology/releases/foundation/1/release.yaml"),
    )
    assert code == 1 and [e["code"] for e in out["errors"]] == ["OUTPUT_STALE"]
    code, out = run(
        capsys,
        "--root",
        str(target),
        "compile",
        str(target / "ontology/releases/foundation/1/release.yaml"),
    )
    assert code == 0 and out["release_ref"].startswith("ontrel:sha256-")


def test_usage_error_exit_2(capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.main(["install"]) == 2
    assert cli.main(["--help"]) == 0
    capsys.readouterr()


class FakeService:
    def __init__(self, behaviour: Any) -> None:
        self.behaviour = behaviour

    def __getattr__(self, name: str) -> Any:
        async def call(*args: Any, **kwargs: Any) -> Any:
            return self.behaviour(name, args, kwargs)

        return call


def _decision() -> AuthorizationDecision:
    return SimpleNamespace(allowed=False)  # type: ignore[return-value]


@pytest.mark.parametrize(
    ("raised", "reason"),
    [
        (OntologyRefused(OntologyReason.SELECTION_CONFLICT), "SELECTION_CONFLICT"),
        (AuthorizationDenied(_decision()), "DENIED"),
        (CredentialError("expired"), "UNAUTHENTICATED"),
    ],
)
def test_runtime_refusals(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    raised: Exception,
    reason: str,
) -> None:
    token = tmp_path / "token"
    token.write_text("secret-token-value", encoding="utf-8")

    def behaviour(name: str, args: Any, kwargs: Any) -> Any:
        raise raised

    @asynccontextmanager
    async def compose(args: Any) -> Any:
        if isinstance(raised, CredentialError):
            raise raised
        yield SimpleNamespace(session=None, principal=None, service=FakeService(behaviour))

    monkeypatch.setattr(runtime, "COMPOSE", compose)
    tenant, kb = str(uuid4()), str(uuid4())
    code, out = run(
        capsys,
        "rollback",
        "--tenant",
        tenant,
        "--kb",
        kb,
        "--token-file",
        str(token),
        "--release",
        "x",
    )
    assert code == 1 and out["status"] == "refused" and out["reason"] == reason
    assert "secret-token-value" not in json.dumps(out)


def test_runtime_dispatch(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    token = tmp_path / "token"
    token.write_text("t", encoding="utf-8")
    release_dir = REPO / "ontology/releases/foundation/1"
    now = __import__("datetime").datetime(2026, 11, 26)
    selection = SimpleNamespace(
        sequence=1,
        action="activate",
        release_ref="r",
        review_id=None,
        actor_principal_id=UUID(int=1),
        selected_at=now,
    )
    results = {
        "install": SimpleNamespace(
            status="installed",
            release_ref="r",
            release_id=UUID(int=2),
            manifest_digest="d",
            terms=53,
        ),
        "report": SimpleNamespace(id=UUID(int=3), status="complete", report={"status": "complete"}),
        "review": UUID(int=4),
        "activate": selection,
        "rollback": selection,
        "history": [selection],
    }

    def behaviour(name: str, args: Any, kwargs: Any) -> Any:
        if name == "install_extension":
            raise OntologyRefused(OntologyReason.TENANT_EXTENSION_UNSUPPORTED)
        return results[name]

    @asynccontextmanager
    async def compose(args: Any) -> Any:
        yield SimpleNamespace(session=None, principal=None, service=FakeService(behaviour))

    monkeypatch.setattr(runtime, "COMPOSE", compose)
    common = ["--tenant", str(uuid4()), "--kb", str(uuid4()), "--token-file", str(token)]
    cases = [
        (["install", *common, str(release_dir)], "outcome"),
        (["report", *common, "--candidate", "r"], "report_id"),
        (
            [
                "review",
                *common,
                "--report",
                str(uuid4()),
                "--decision",
                "approve",
                "--rationale",
                "ok",
            ],
            "review_id",
        ),
        (["activate", *common, "--release", "r", "--review", str(uuid4())], "sequence"),
        (["rollback", *common, "--release", "r"], "sequence"),
        (["history", *common], "selections"),
    ]
    for argv, field in cases:
        code, out = run(capsys, *argv)
        assert code == 0 and field in out, argv
    code, out = run(capsys, "install-extension", *common, "ext.yaml")
    assert code == 1 and out["reason"] == "TENANT_EXTENSION_UNSUPPORTED"
