"""F0012 PostgreSQL harness: an owned database per test, migrated to head.

Extends the F0007 world (tenant T: KB A and KB B) with an `OntologySteward`, a
plain `TenantMember`, a second tenant U with KB C, and trusted `resource_access`
rows for each KB's ontology scope (G0-5). Releases are compiled by the real
compiler: the committed foundation@1 lock, or variants built in a temporary root.
Synthetic development data only.
"""

from __future__ import annotations

import json
import shutil
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import httpx2 as httpx
import pytest
import yaml
from alembic import command
from brain_domain.authx import ResourceKey, ResourceType
from brain_domain.principal import Principal, PrincipalKind
from brain_factslots.predicates import ReleasePredicateRegistry
from brain_ontology.compiler import compile_release, write_release
from brain_ontology.service import OntologyReleaseService
from brain_persistence.authx import SqlAlchemyAuthorityStore
from brain_persistence.ontology_releases import OntologyReleaseStore
from brain_persistence.tenancy import provision_resource_access
from brain_security.execution import AuthorizationExecution
from brain_testing import fixtures
from brain_testing.factslots import test_registry
from engine.tests.fixtures.factslots.harness import FactSlotWorld, Owner, configuration
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from brain_api.app import create_app
from brain_api.deps import current_principal, get_db_session, get_predicate_registry

PRODUCT = Path(__file__).resolve().parents[3]
FOUNDATION_LOCK = PRODUCT / "ontology/releases/foundation/1"
FOUNDATION_MODULE = PRODUCT / "ontology/modules/foundation/module.yaml"
REFERENCES = (
    "planning-mds/domain/glossary.md",
    "planning-mds/architecture/master-blueprint.md",
    "planning-mds/examples/commercial-pc-account/records.json",
    "planning-mds/examples/commercial-pc-account/cases.md",
)
ONTOLOGY_TABLES = (
    "ontology_module_version",
    "ontology_release",
    "ontology_release_module",
    "ontology_term",
    "ontology_change_record",
    "ontology_impact_report",
    "ontology_release_review",
    "ontology_release_selection",
)
CANONICAL_TABLES = (
    "content_artifact",
    "assertion",
    "fact_slot",
    "canonical_fact_version",
    "canonical_commit",
)


@dataclass(frozen=True)
class Release:
    manifest: dict[str, Any]
    normalized: dict[str, Any]
    directory: Path

    @property
    def ref(self) -> str:
        return str(self.manifest["release_ref"])


def load_release(directory: Path) -> Release:
    return Release(
        json.loads((directory / "manifest.json").read_text(encoding="utf-8")),
        json.loads((directory / "normalized.json").read_text(encoding="utf-8")),
        directory,
    )


def foundation() -> Release:
    return load_release(FOUNDATION_LOCK)


def foundation_module() -> dict[str, Any]:
    return yaml.safe_load(FOUNDATION_MODULE.read_text(encoding="utf-8"))


class ReleaseBuilder:
    """A temporary repository root: the reference files, optionally the committed
    foundation@1 lock (identity history), and compiled variants."""

    def __init__(self, root: Path, *, with_history: bool = True) -> None:
        self.root = root
        for ref in REFERENCES:
            (root / ref).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(PRODUCT / ref, root / ref)
        (root / "ex.md").write_text("EX-1 synthetic\n", encoding="utf-8")
        if with_history:
            shutil.copytree(FOUNDATION_LOCK, root / "ontology/releases/foundation/1")

    def build(
        self,
        name: str,
        sequence: int,
        modules: dict[str, dict[str, Any]],
        *,
        changes: list[dict[str, Any]] | None = None,
        predecessor: str | None = None,
    ) -> Release:
        directory = self.root / f"ontology/releases/{name}/{sequence}"
        directory.mkdir(parents=True, exist_ok=True)
        entries = []
        for module_name, data in modules.items():
            path = self.root / f"ontology/modules/{name}-{sequence}-{module_name}/module.yaml"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
            entries.append(str(path))
        request: dict[str, Any] = {"name": name, "sequence": sequence, "modules": entries}
        if changes:
            (directory / "changes.yaml").write_text(
                yaml.safe_dump({"change_records": changes}), encoding="utf-8"
            )
            request["changes"] = ["changes.yaml"]
        if predecessor:
            request["predecessor"] = predecessor
        (directory / "release.yaml").write_text(yaml.safe_dump(request), encoding="utf-8")
        compiled = compile_release(directory / "release.yaml", root=self.root)
        write_release(compiled, directory)
        return load_release(directory)


def event_module() -> dict[str, Any]:
    """Test composition with an EVENT predicate (ADR-0081 D7: foundation has none)."""
    refs = {"examples": ["ex.md#EX-1"], "regression_cases": ["ex.md"]}
    return {
        "authoring_schema": "ontology-module-authoring/v1",
        "module": {"id": "evtest", "version": 1, "predicate_namespace": "evt", "dependencies": []},
        "terms": [
            {
                "id": "evtest.occurrence",
                "kind": "class",
                "labels": {"en-US": "Occurrence"},
                "definition": "A synthetic test class whose facts happen at one time.",
                "parents": [],
                **refs,
            },
            {
                "id": "evtest.occurrence.happened-on",
                "kind": "datatype_property",
                "labels": {"en-US": "Happened on"},
                "definition": "The day the synthetic occurrence happened; an EVENT fact.",
                "domain": "evtest.occurrence",
                "range": "xsd:date",
                "temporal_kind": "EVENT",
                "predicate": {"local_name": "happenedOn", "major": 1},
                "value_type": "date",
                "cardinality": "SINGLE",
                **refs,
            },
        ],
        "projection": [
            {
                "property": "evtest.occurrence.happened-on",
                "disposition": "vertex_property",
                "label": "happened_on",
            }
        ],
    }


class OntologyWorld(FactSlotWorld):
    def __init__(self, url: str) -> None:
        super().__init__(url)
        with Session(self.sync_engine) as session, session.begin():
            self.steward = self._principal(
                session, "steward", PrincipalKind.USER, [self.a], roles=("OntologySteward",)
            )
            self.member = self._principal(
                session, "member", PrincipalKind.USER, [self.a], roles=("TenantMember",)
            )
            tenant_u, kb_c = uuid4(), uuid4()
            fixtures.seed_scope(session, tenant_u, kb_c)
            self.c = Owner(tenant_u, kb_c, fixtures.seed_content_artifact(session, tenant_u, kb_c))
            self.service_c = self._principal(session, "service-c", PrincipalKind.SERVICE, [self.c])
            self.steward_c = self._principal(
                session, "steward-c", PrincipalKind.USER, [self.c], roles=("OntologySteward",)
            )
            for owner in (self.a, self.b, self.c):
                self.provision_scope(session, owner)

    @staticmethod
    def provision_scope(session: Session, owner: Owner) -> None:
        provision_resource_access(
            session,
            ResourceKey(ResourceType.ONTOLOGY_RELEASE, owner.knowledge_base_id),
            tenant_id=owner.tenant_id,
            knowledge_base_id=owner.knowledge_base_id,
            classifications=["internal"],
            actor_id=fixtures.SYNTHETIC_OPERATOR,
            at=datetime.now(UTC),
        )

    @asynccontextmanager
    async def ontology(self) -> AsyncIterator[OntologyReleaseService]:
        async with AsyncSession(self.engine, expire_on_commit=False) as session:
            execution = AuthorizationExecution(
                SqlAlchemyAuthorityStore(session), self.policy, self.policy.release
            )
            yield OntologyReleaseService(
                execution, OntologyReleaseStore(session), commit=session.commit
            )

    async def install(
        self, release: Release, *, principal: Principal | None = None, owner: Owner | None = None
    ):  # type: ignore[no-untyped-def]
        async with self.ontology() as service:
            return await service.install(
                principal or self.service,
                (owner or self.a).scope,
                release.manifest,
                release.normalized,
                trace_id="f0012-test",
            )

    async def run(self, fn: Callable[[OntologyReleaseService], Any]) -> Any:
        async with self.ontology() as service:
            return await fn(service)

    async def approve(
        self, release: Release, owner: Owner | None = None, decision: str = "approve"
    ) -> tuple[Any, UUID]:
        scope = (owner or self.a).scope
        steward = self.steward if owner in (None, self.a) else self.steward_c
        report = await self.run(lambda s: s.report(steward, scope, release.ref, trace_id="t"))
        review = await self.run(
            lambda s: s.review(
                steward, scope, report.id, decision, "reviewed in test", trace_id="t"
            )
        )
        return report, review

    async def activate(self, release: Release, review_id: UUID, owner: Owner | None = None):  # type: ignore[no-untyped-def]
        scope = (owner or self.a).scope
        steward = self.steward if owner in (None, self.a) else self.steward_c
        return await self.run(
            lambda s: s.activate(steward, scope, release.ref, review_id, trace_id="t")
        )

    def release_registry(self) -> Callable[..., ReleasePredicateRegistry]:
        def build(session: AsyncSession = Depends(get_db_session)) -> ReleasePredicateRegistry:
            return ReleasePredicateRegistry(test_registry(), OntologyReleaseStore(session))

        return build

    def release_client(self, principal: Principal):  # type: ignore[no-untyped-def]
        """The real route with the production-shaped release-backed registry."""
        app = create_app()

        async def session_override():  # type: ignore[no-untyped-def]
            async with AsyncSession(self.engine, expire_on_commit=False) as session:
                yield session

        app.dependency_overrides[get_db_session] = session_override
        app.dependency_overrides[current_principal] = lambda: principal
        app.dependency_overrides[get_predicate_registry] = self.release_registry()
        return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")

    @asynccontextmanager
    async def release_slots(self):  # type: ignore[no-untyped-def]
        async with AsyncSession(self.engine, expire_on_commit=False) as session:
            registry = ReleasePredicateRegistry(
                test_registry(), OntologyReleaseStore(session), strict=False
            )
            async with self.slots(registry=registry) as service:
                yield service

    def table_counts(self, tables: tuple[str, ...] = ONTOLOGY_TABLES) -> dict[str, int]:
        return {t: self.scalar(f"SELECT count(*) FROM {t}") for t in tables}

    def audit_events(self, event_type: str) -> list[tuple]:
        return self.rows(
            "SELECT reason_code, operation_outcome, payload::text, decision_id FROM audit_event "
            "WHERE event_type = %s ORDER BY occurred_at, id",
            event_type,
        )


@pytest.fixture
async def onto_world(database):  # type: ignore[no-untyped-def]
    command.upgrade(configuration(), "head")
    world = OntologyWorld(database)
    try:
        yield world
    finally:
        await world.close()


@pytest.fixture
def builder(tmp_path: Path) -> ReleaseBuilder:
    return ReleaseBuilder(tmp_path)
