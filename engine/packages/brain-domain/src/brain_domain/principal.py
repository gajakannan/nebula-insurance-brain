from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class PrincipalKind(StrEnum):
    USER = "user"
    SERVICE = "service"
    AGENT = "agent"


class PrincipalStatus(StrEnum):
    ACTIVE = "active"
    DISABLED = "disabled"


@dataclass(frozen=True, slots=True)
class Principal:
    id: UUID
    kind: PrincipalKind
    issuer: str
    subject: str
    status: PrincipalStatus


@dataclass(frozen=True, slots=True)
class Membership:
    principal_id: UUID
    tenant_id: UUID
    knowledge_base_id: UUID
    role: str
    grant_revision: int
    revoked_at: datetime | None
