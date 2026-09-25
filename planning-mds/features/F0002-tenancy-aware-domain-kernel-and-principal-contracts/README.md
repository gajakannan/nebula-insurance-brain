# F0002 — Tenancy-aware domain kernel + verified stable principal and scope contracts

**Status:** Planned — Phase A and Phase B approved on 2026-09-25; implementation not started
**Phase:** v0.1A · **Roadmap:** Next · **Total Stories:** 6

Build on F0001’s verified identity and scoped authorization. Preserve tenant-scoped entity identity, explicit KB grants and the existing pilot roles while adding structural ownership, current complete grant slices, resource restrictions, bounded delegation and durable audit.

## Documents

- [PRD](PRD.md), [personas](personas.md), [acceptance checklist](acceptance-criteria-checklist.md)
- [Assembly plan](feature-assembly-plan.md), [status](STATUS.md), [getting started](GETTING-STARTED.md)
- [Worked examples](worked-examples.md), [structured contract examples](contract-examples.json)
- [ADR-0061](../../architecture/decisions/ADR-0061-tenant-identity-and-structural-ownership.md), [ADR-0062](../../architecture/decisions/ADR-0062-current-authorization-and-durable-decisions.md)
- [OpenAPI](../../api/brain-api.yaml), [internal v1 schema](../../schemas/authx-kernel.schema.json)

## Stories

| ID | Title | Status |
|---|---|---|
| F0002-S0001 | [Preserve structural tenancy and tenant-scoped entity identity](F0002-S0001-structural-tenancy-and-entity-identity.md) | Not Started |
| F0002-S0002 | [Resolve verified credentials to stable typed principals](F0002-S0002-verified-stable-principal-resolution.md) | Not Started |
| F0002-S0003 | [Resolve current memberships and intersect requested scope](F0002-S0003-current-membership-and-request-scope.md) | Not Started |
| F0002-S0004 | [Enforce parent, classification and source restrictions together](F0002-S0004-conjunctive-resource-authorization.md) | Not Started |
| F0002-S0005 | [Bound delegated and autonomous service authority](F0002-S0005-bounded-delegation-and-service-authority.md) | Not Started |
| F0002-S0006 | [Prove audited kernel behavior through existing consumers](F0002-S0006-audit-and-consumer-contract-proof.md) | Not Started |

## Feature ERD — proposed ownership and security substrate

```mermaid
erDiagram
    TENANT ||--o{ WORKSPACE : owns
    WORKSPACE ||--o{ KNOWLEDGE_BASE : owns
    TENANT ||--o{ ENTITY_IDENTITY : identifies
    ENTITY_IDENTITY ||--o{ ENTITY_KNOWLEDGE_BASE : associates
    KNOWLEDGE_BASE ||--o{ ENTITY_KNOWLEDGE_BASE : contains
    PRINCIPAL ||--o{ EXTERNAL_IDENTITY : resolves
    PRINCIPAL ||--o{ MEMBERSHIP : receives
    KNOWLEDGE_BASE ||--o{ MEMBERSHIP : scopes
    PRINCIPAL ||--o{ DELEGATION : acts
    PRINCIPAL ||--o{ AUTHORIZATION_DECISION : accountable
    KNOWLEDGE_BASE ||--o{ RESOURCE_ACCESS : protects
    TENANT {
        uuid id PK
    }
    WORKSPACE {
        uuid id PK
        uuid tenant_id FK
    }
    KNOWLEDGE_BASE {
        uuid id PK
        uuid workspace_id FK
        uuid tenant_id FK
    }
    ENTITY_IDENTITY {
        uuid id PK
        uuid tenant_id PK
    }
    ENTITY_KNOWLEDGE_BASE {
        uuid entity_id FK
        uuid tenant_id FK
        uuid knowledge_base_id FK
    }
    PRINCIPAL {
        uuid id PK
        string kind
        string status
    }
    EXTERNAL_IDENTITY {
        string issuer PK
        string subject PK
        uuid principal_id FK
    }
    MEMBERSHIP {
        uuid id PK
        uuid principal_id FK
        uuid knowledge_base_id FK
        string role
        int grant_revision
    }
    DELEGATION {
        uuid id PK
        uuid acting_principal_id FK
        uuid executor_principal_id FK
        datetime expires_at
    }
    RESOURCE_ACCESS {
        string resource_type PK
        uuid resource_id PK
        int revision
    }
    AUTHORIZATION_DECISION {
        uuid decision_id PK
        uuid actor_principal_id FK
        string policy_release
        int grant_revision
    }
```

`AUTHORIZATION_DECISION` denotes the v1 audit payload on append-only audit events, not a second authoritative business store. Resource and membership ownership also carry tenant IDs, enforced by composite constraints in the assembly plan.

```text
Tenant -> Workspace -> KB -> semantic rows + ResourceAccess
  |                    |
  +-> EntityIdentity <-+ EntityKB association (not permission)
Principal <- ExternalIdentity
  +-> Membership -> KB + complete role/restriction slice
  +-> Delegation -> exact executor + ceiling + expiry
  +-> Decision audit (current actor/grants/policy/resource)
```

## Component view

```mermaid
C4Component
    Container_Boundary(engine, "Existing engine process") {
        Component(api, "API / worker adapters", "Python", "Verify caller and open unit of work")
        Component(identity, "PrincipalResolver", "brain_security", "Stable verified identity")
        Component(scope, "Scope / resource / delegation resolvers", "brain_security ports", "Current trusted state")
        Component(evaluator, "Shared evaluator + Casbin", "brain_security", "Complete-slice conjunction")
        Component(execution, "AuthorizationExecution", "brain_security", "Effect and audit transaction")
        Component(repository, "Persistence adapters", "brain_persistence", "Sync worker / async API")
    }
    ContainerDb(db, "PostgreSQL", "Existing database", "Ownership, grants, semantic state, audit")
    Rel(api, identity, "Verified credential")
    Rel(api, execution, "Protected operation")
    Rel(execution, scope, "Resolve current state")
    Rel(scope, repository, "Trusted reads and locks")
    Rel(execution, evaluator, "Evaluate typed inputs")
    Rel(execution, repository, "Atomic effect/audit")
    Rel(repository, db, "SQL")
```

No new service, container or browser surface. Existing [C4 context](../../architecture/c4-context.md) and [container](../../architecture/c4-container.md) remain applicable. Policy allow never overrides missing parent/classification/source/delegation requirements.
