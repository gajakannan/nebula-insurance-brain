from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, TypeVar
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    Column,
    Float,
    Integer,
    MetaData,
    String,
    Table,
    UniqueConstraint,
    and_,
    func,
    insert,
    or_,
    select,
    update,
)
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.exc import IntegrityError

metadata = MetaData()
jobs = Table(
    "document_job",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("tenant_id", String(36), nullable=False),
    Column("knowledge_base_id", String(36), nullable=False),
    Column("artifact_id", String(36), nullable=False),
    Column("request_key", String(128), nullable=False),
    Column("payload", JSON, nullable=False),
    Column("state", String(20), nullable=False),
    Column("attempt", Integer, nullable=False),
    Column("max_attempts", Integer, nullable=False),
    Column("generation", Integer, nullable=False),
    Column("available_at", Float, nullable=False),
    Column("leased_until", Float, nullable=False),
    Column("result_ref", String, nullable=True),
    UniqueConstraint(
        "tenant_id", "knowledge_base_id", "request_key", name="uq_document_job_request"
    ),
)
leases = Table(
    "document_artifact_lease",
    metadata,
    Column("artifact_id", String(36), primary_key=True),
    Column("tenant_id", String(36), nullable=False),
    Column("knowledge_base_id", String(36), nullable=False),
    Column("job_id", String(36), nullable=True),
    Column("generation", Integer, nullable=False),
    Column("leased_until", Float, nullable=False),
)
events = Table(
    "document_job_event",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("job_id", String(36), nullable=False),
    Column("generation", Integer, nullable=False),
    Column("event", String(64), nullable=False),
    Column("occurred_at", Float, nullable=False),
)
outbox = Table(
    "document_job_outbox",
    metadata,
    Column("job_id", String(36), primary_key=True),
    Column("tenant_id", String(36), nullable=False),
    Column("knowledge_base_id", String(36), nullable=False),
    Column("result_ref", String, nullable=False),
    Column("created_at", Float, nullable=False),
    Column("delivered_at", Float, nullable=True),
)
T = TypeVar("T")


class LeaseLost(RuntimeError):
    pass


@dataclass(frozen=True)
class JobLease:
    job_id: UUID
    tenant_id: UUID
    knowledge_base_id: UUID
    artifact_id: UUID
    generation: int
    attempt: int
    payload: dict[str, Any]


class DocumentJobQueue:
    """PostgreSQL queue; SQLite is supported for deterministic contract tests.

    A separate artifact lease serializes conversion even across different profile
    jobs. Fencing and publication use the same transaction and row lock. Failed
    attempts remain audited; accepted completion emits one outbox row.
    """

    def __init__(
        self,
        engine: Engine,
        *,
        lease_seconds: float = 120,
        clock: Callable[[], float] | None = None,
    ) -> None:
        if lease_seconds <= 0:
            raise ValueError("lease duration must be positive")
        self.engine = engine
        self.lease_seconds = lease_seconds
        self.clock = clock

    def _now(self, connection: Connection) -> float:
        if self.clock is not None:
            return self.clock()
        # A PostgreSQL fence must observe time after waiting for a row lock,
        # not the transaction start time returned by CURRENT_TIMESTAMP.
        clock = (
            func.clock_timestamp()
            if connection.dialect.name == "postgresql"
            else func.current_timestamp()
        )
        value = connection.scalar(select(clock))
        assert isinstance(value, datetime)
        return value.replace(tzinfo=UTC).timestamp() if value.tzinfo is None else value.timestamp()

    def _event(self, conn: Connection, job_id: str, generation: int, event: str) -> None:
        conn.execute(
            insert(events).values(
                id=str(uuid4()),
                job_id=job_id,
                generation=generation,
                event=event,
                occurred_at=self._now(conn),
            )
        )

    def enqueue(
        self,
        *,
        tenant_id: UUID,
        knowledge_base_id: UUID,
        artifact_id: UUID,
        request_key: str,
        payload: dict[str, Any],
        max_attempts: int = 3,
    ) -> UUID:
        if not request_key or len(request_key) > 128 or max_attempts <= 0:
            raise ValueError("invalid job identity or retry limit")
        scope = dict(tenant_id=str(tenant_id), knowledge_base_id=str(knowledge_base_id))
        with self.engine.begin() as conn:
            try:
                with conn.begin_nested():
                    conn.execute(
                        insert(leases).values(
                            artifact_id=str(artifact_id),
                            **scope,
                            job_id=None,
                            generation=0,
                            leased_until=0,
                        )
                    )
            except IntegrityError:
                pass
            artifact = (
                conn.execute(select(leases).where(leases.c.artifact_id == str(artifact_id)))
                .mappings()
                .one()
            )
            if any(artifact[k] != v for k, v in scope.items()):
                raise PermissionError("artifact scope mismatch")
            job_id = uuid4()
            try:
                with conn.begin_nested():
                    conn.execute(
                        insert(jobs).values(
                            id=str(job_id),
                            **scope,
                            artifact_id=str(artifact_id),
                            request_key=request_key,
                            payload=payload,
                            state="queued",
                            attempt=0,
                            max_attempts=max_attempts,
                            generation=0,
                            available_at=self._now(conn),
                            leased_until=0,
                        )
                    )
                self._event(conn, str(job_id), 0, "queued")
                return job_id
            except IntegrityError:
                row = (
                    conn.execute(
                        select(jobs).where(
                            jobs.c.tenant_id == str(tenant_id),
                            jobs.c.knowledge_base_id == str(knowledge_base_id),
                            jobs.c.request_key == request_key,
                        )
                    )
                    .mappings()
                    .one()
                )
                if (
                    row["artifact_id"] != str(artifact_id)
                    or row["payload"] != payload
                    or row["max_attempts"] != max_attempts
                ):
                    raise ValueError("idempotency key reused for a different request") from None
                return UUID(row["id"])

    def claim(self) -> JobLease | None:
        with self.engine.begin() as conn:
            now = self._now(conn)
            eligible = or_(
                and_(jobs.c.state.in_(["queued", "retry"]), jobs.c.available_at <= now),
                and_(jobs.c.state == "running", jobs.c.leased_until <= now),
            )
            rows = (
                conn.execute(
                    select(jobs)
                    .where(eligible)
                    .order_by(jobs.c.available_at)
                    .limit(32)
                    .with_for_update(skip_locked=True)
                )
                .mappings()
                .all()
            )
            for row in rows:
                if row["attempt"] >= row["max_attempts"]:
                    conn.execute(update(jobs).where(jobs.c.id == row["id"]).values(state="failed"))
                    self._event(conn, row["id"], row["generation"], "attempts_exhausted")
                    continue
                acquired = conn.execute(
                    update(leases)
                    .where(leases.c.artifact_id == row["artifact_id"], leases.c.leased_until <= now)
                    .values(
                        job_id=row["id"],
                        leased_until=now + self.lease_seconds,
                        generation=leases.c.generation + 1,
                    )
                )
                if acquired.rowcount != 1:
                    continue
                generation = conn.scalar(
                    select(leases.c.generation).where(leases.c.artifact_id == row["artifact_id"])
                )
                if not isinstance(generation, int):
                    raise RuntimeError("artifact lease generation is missing")
                conn.execute(
                    update(jobs)
                    .where(jobs.c.id == row["id"])
                    .values(
                        state="running",
                        attempt=row["attempt"] + 1,
                        generation=generation,
                        leased_until=now + self.lease_seconds,
                    )
                )
                self._event(conn, row["id"], generation, "claimed")
                return JobLease(
                    UUID(row["id"]),
                    UUID(row["tenant_id"]),
                    UUID(row["knowledge_base_id"]),
                    UUID(row["artifact_id"]),
                    generation,
                    row["attempt"] + 1,
                    row["payload"],
                )
        return None

    def _fence(self, conn: Connection, lease: JobLease) -> None:
        row = (
            conn.execute(select(jobs).where(jobs.c.id == str(lease.job_id)).with_for_update())
            .mappings()
            .one()
        )
        artifact = (
            conn.execute(
                select(leases)
                .where(leases.c.artifact_id == str(lease.artifact_id))
                .with_for_update()
            )
            .mappings()
            .one()
        )
        if (
            row["state"] != "running"
            or row["generation"] != lease.generation
            or artifact["job_id"] != str(lease.job_id)
            or artifact["generation"] != lease.generation
            or artifact["leased_until"] <= self._now(conn)
            or row["tenant_id"] != str(lease.tenant_id)
            or row["knowledge_base_id"] != str(lease.knowledge_base_id)
        ):
            raise LeaseLost("job cancelled, expired, or superseded")
        # SQLite ignores FOR UPDATE. Acquire its writer lock before invoking an
        # external publication callback, with the same generation predicate.
        guarded = conn.execute(
            update(leases)
            .where(
                leases.c.artifact_id == str(lease.artifact_id),
                leases.c.job_id == str(lease.job_id),
                leases.c.generation == lease.generation,
                leases.c.leased_until > self._now(conn),
            )
            .values(leased_until=leases.c.leased_until)
        )
        if guarded.rowcount != 1:
            raise LeaseLost("artifact lease changed before publication")

    def heartbeat(self, lease: JobLease) -> None:
        with self.engine.begin() as conn:
            self._fence(conn, lease)
            until = self._now(conn) + self.lease_seconds
            conn.execute(
                update(jobs).where(jobs.c.id == str(lease.job_id)).values(leased_until=until)
            )
            conn.execute(
                update(leases)
                .where(leases.c.artifact_id == str(lease.artifact_id))
                .values(leased_until=until)
            )

    def publish(self, lease: JobLease, operation: Callable[[], T]) -> T:
        return self.publish_transaction(lease, lambda _connection: operation())

    def publish_transaction(self, lease: JobLease, operation: Callable[[Connection], T]) -> T:
        with self.engine.begin() as conn:
            self._fence(conn, lease)
            result = operation(conn)
            self._event(conn, str(lease.job_id), lease.generation, "checkpoint_published")
            return result

    def finish(self, lease: JobLease, result_ref: str) -> None:
        with self.engine.begin() as conn:
            self._fence(conn, lease)
            conn.execute(
                update(jobs)
                .where(jobs.c.id == str(lease.job_id))
                .values(state="complete", result_ref=result_ref)
            )
            conn.execute(
                update(leases)
                .where(leases.c.artifact_id == str(lease.artifact_id))
                .values(leased_until=0)
            )
            conn.execute(
                insert(outbox).values(
                    job_id=str(lease.job_id),
                    tenant_id=str(lease.tenant_id),
                    knowledge_base_id=str(lease.knowledge_base_id),
                    result_ref=result_ref,
                    created_at=self._now(conn),
                )
            )
            self._event(conn, str(lease.job_id), lease.generation, "complete")

    def retry(self, lease: JobLease, *, delay_seconds: float = 5) -> None:
        with self.engine.begin() as conn:
            self._fence(conn, lease)
            row = conn.execute(select(jobs).where(jobs.c.id == str(lease.job_id))).mappings().one()
            state = "retry" if lease.attempt < row["max_attempts"] else "failed"
            conn.execute(
                update(jobs)
                .where(jobs.c.id == str(lease.job_id))
                .values(state=state, available_at=self._now(conn) + max(0, delay_seconds))
            )
            conn.execute(
                update(leases)
                .where(leases.c.artifact_id == str(lease.artifact_id))
                .values(leased_until=0)
            )
            self._event(conn, str(lease.job_id), lease.generation, state)

    def cancel(self, job_id: UUID, tenant_id: UUID, knowledge_base_id: UUID) -> None:
        with self.engine.begin() as conn:
            row = (
                conn.execute(
                    select(jobs)
                    .where(
                        jobs.c.id == str(job_id),
                        jobs.c.tenant_id == str(tenant_id),
                        jobs.c.knowledge_base_id == str(knowledge_base_id),
                    )
                    .with_for_update()
                )
                .mappings()
                .one_or_none()
            )
            if row is None:
                raise PermissionError("job is not in scope")
            if row["state"] in ("complete", "cancelled", "failed"):
                return
            conn.execute(update(jobs).where(jobs.c.id == str(job_id)).values(state="cancelled"))
            # Keep the artifact lease until timeout: an in-flight converter must not
            # overlap a new one just because its consumer requested cancellation.
            self._event(conn, str(job_id), row["generation"], "cancelled")
