from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Literal, TypeVar, get_args
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
from sqlalchemy.dialects import postgresql
from sqlalchemy.engine import Connection, Dialect, Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.types import TypeDecorator, TypeEngine


class UUIDText(TypeDecorator[str]):
    """UUID-valued job identity carried as canonical text in Python.

    PostgreSQL stores a native `uuid` (migration 0005 converts the 0004 text
    columns, so invalid values cannot exist); SQLite contract tests keep
    `String(36)`. Binding and results are always the dashed string form, so the
    queue's fencing comparisons are identical on both dialects (F0002 assembly
    plan: reconcile job UUID ownership without changing lease/fence behaviour)."""

    impl = String(36)
    cache_ok = True

    def load_dialect_impl(self, dialect: Dialect) -> TypeEngine[str]:
        if dialect.name == "postgresql":
            return dialect.type_descriptor(postgresql.UUID(as_uuid=False))
        return dialect.type_descriptor(String(36))

    def process_bind_param(self, value: object, dialect: Dialect) -> str | None:
        return None if value is None else str(UUID(str(value)))

    def process_result_value(self, value: object, dialect: Dialect) -> str | None:
        return None if value is None else str(value)


metadata = MetaData()
jobs = Table(
    "document_job",
    metadata,
    Column("id", UUIDText(), primary_key=True),
    Column("tenant_id", UUIDText(), nullable=False),
    Column("knowledge_base_id", UUIDText(), nullable=False),
    Column("artifact_id", UUIDText(), nullable=False),
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
    Column("artifact_id", UUIDText(), primary_key=True),
    Column("tenant_id", UUIDText(), nullable=False),
    Column("knowledge_base_id", UUIDText(), nullable=False),
    Column("job_id", UUIDText(), nullable=True),
    Column("generation", Integer, nullable=False),
    Column("leased_until", Float, nullable=False),
)
events = Table(
    "document_job_event",
    metadata,
    Column("id", UUIDText(), primary_key=True),
    Column("job_id", UUIDText(), nullable=False),
    Column("generation", Integer, nullable=False),
    Column("event", String(64), nullable=False),
    Column("occurred_at", Float, nullable=False),
    # Migration 0009 (F0005): stable failure reason; NULL for non-failure events.
    Column("reason", String(64), nullable=True),
)
outbox = Table(
    "document_job_outbox",
    metadata,
    Column("job_id", UUIDText(), primary_key=True),
    Column("tenant_id", UUIDText(), nullable=False),
    Column("knowledge_base_id", UUIDText(), nullable=False),
    Column("result_ref", String, nullable=False),
    Column("created_at", Float, nullable=False),
    Column("delivered_at", Float, nullable=True),
)
T = TypeVar("T")

# Mirrors migration 0009's CHECK constraint. Codes only: never source or SDK text.
FailureReason = Literal[
    "model_unavailable",
    "model_timeout",
    "model_http_error",
    "model_malformed_output",
    "model_schema_invalid",
    "storage_write_failed",
    "conversion_failed",
    "conversion_timeout",
    "stage_guard_mismatch",
    "unsupported_targeting",
    "unsupported_output",
    "authorization_denied",
    "cancelled",
    # Migration 0010 (Code Review H1/M1).
    "model_budget_exceeded",
    "model_deadline_exceeded",
    "model_contract_fallback",
    "interpretation_failed",
]
FAILURE_REASONS: frozenset[str] = frozenset(get_args(FailureReason))


class LeaseLost(RuntimeError):
    pass


class QueueFull(RuntimeError):
    """Explicit rejection of a new submission beyond the configured depth (F0005-S0002)."""

    code = "queue_depth_exceeded"

    def __init__(self) -> None:
        super().__init__(self.code)


# Unfinished work counts against the bound; terminal jobs never do.
ACTIVE_STATES = ("queued", "retry", "running")
# Serializes PostgreSQL depth checks so concurrent submitters cannot overshoot.
_DEPTH_LOCK_KEY = 0x0F0005


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
        max_depth: int | None = None,
    ) -> None:
        if lease_seconds <= 0:
            raise ValueError("lease duration must be positive")
        if max_depth is not None and (type(max_depth) is not int or max_depth <= 0):
            raise ValueError("queue depth bound must be a positive integer")
        self.engine = engine
        self.lease_seconds = lease_seconds
        self.clock = clock
        self.max_depth = max_depth

    def depth(self) -> int:
        """Unfinished jobs: queued, waiting to retry, or running."""
        with self.engine.connect() as conn:
            return int(
                conn.scalar(
                    select(func.count()).select_from(jobs).where(jobs.c.state.in_(ACTIVE_STATES))
                )
                or 0
            )

    def _admit(self, conn: Connection, scope: dict[str, str], request_key: str) -> None:
        """Reject a new job when the bound is reached; duplicates stay idempotent."""
        if self.max_depth is None:
            return
        if conn.dialect.name == "postgresql":
            conn.execute(select(func.pg_advisory_xact_lock(_DEPTH_LOCK_KEY)))
        existing = conn.scalar(
            select(jobs.c.id).where(
                jobs.c.tenant_id == scope["tenant_id"],
                jobs.c.knowledge_base_id == scope["knowledge_base_id"],
                jobs.c.request_key == request_key,
            )
        )
        if existing is not None:
            return
        active = conn.scalar(
            select(func.count()).select_from(jobs).where(jobs.c.state.in_(ACTIVE_STATES))
        )
        if (active or 0) >= self.max_depth:
            raise QueueFull()

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

    def _event(
        self,
        conn: Connection,
        job_id: str,
        generation: int,
        event: str,
        reason: FailureReason | None = None,
    ) -> None:
        if reason is not None and reason not in FAILURE_REASONS:
            raise ValueError("unknown job failure reason")
        conn.execute(
            insert(events).values(
                id=str(uuid4()),
                job_id=job_id,
                generation=generation,
                event=event,
                occurred_at=self._now(conn),
                reason=reason,
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
            self._admit(conn, scope, request_key)
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
            # Object publication can outlast a lease while its row locks prevent
            # heartbeat/reclaim. Expiry still fences the database readiness commit.
            self._fence(conn, lease)
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

    def retry(self, lease: JobLease, *, reason: FailureReason, delay_seconds: float = 5) -> None:
        """Record a failed attempt; exhausted attempts end explicitly as `failed`."""
        self._fail(lease, reason, delay_seconds=delay_seconds, terminal=False)

    def fail(self, lease: JobLease, *, reason: FailureReason) -> None:
        """Terminal failure for a cause another attempt cannot change."""
        self._fail(lease, reason, delay_seconds=0, terminal=True)

    def _fail(
        self, lease: JobLease, reason: FailureReason, *, delay_seconds: float, terminal: bool
    ) -> None:
        if reason not in FAILURE_REASONS:
            raise ValueError("unknown job failure reason")
        with self.engine.begin() as conn:
            self._fence(conn, lease)
            row = conn.execute(select(jobs).where(jobs.c.id == str(lease.job_id))).mappings().one()
            state = "retry" if not terminal and lease.attempt < row["max_attempts"] else "failed"
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
            self._event(conn, str(lease.job_id), lease.generation, state, reason)

    def conversion_started(self, lease: JobLease) -> None:
        """Durably record a physical conversion launch before it starts (F0005 M2).

        Fenced like publication, so a stale attempt cannot record a launch. A crash
        mid-conversion leaves no failure reason, but the launch still counts.
        """
        with self.engine.begin() as conn:
            self._fence(conn, lease)
            self._event(conn, str(lease.job_id), lease.generation, "conversion_started")

    def conversion_launches(self, job_id: UUID) -> int:
        with self.engine.connect() as conn:
            return int(
                conn.scalar(
                    select(func.count())
                    .select_from(events)
                    .where(events.c.job_id == str(job_id), events.c.event == "conversion_started")
                )
                or 0
            )

    def failure_reasons(self, job_id: UUID) -> list[str]:
        """Recorded failure reasons for one job, oldest first (append-only history)."""
        with self.engine.connect() as conn:
            return list(
                conn.scalars(
                    select(events.c.reason)
                    .where(events.c.job_id == str(job_id), events.c.reason.is_not(None))
                    .order_by(events.c.occurred_at)
                )
            )

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
            self._event(conn, str(job_id), row["generation"], "cancelled", "cancelled")
