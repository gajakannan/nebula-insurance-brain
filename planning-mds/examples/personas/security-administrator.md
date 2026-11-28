# Persona: Noor the Security Administrator

**Role/Title:** Identity and access administrator for the Nebula Insurance Brain deployment
**Archetype:** Internal platform user — operates the identity provider, sessions, principals and grants (master blueprint §1.2, §65, §66)
**Priority:** Secondary (F0021); primary for F0026 AuthX hardening

## Demographics & Background

**Experience Level:** 8+ years running enterprise SSO and access reviews; reads audit trails daily
**Technical Proficiency:** High for identity tooling and logs; not a frontend developer
**Daily Responsibilities:**
- Provision and disable users and service clients at the identity provider
- Revoke grants and confirm the revocation took effect
- Investigate failed sign-ins, credential stuffing and unusual session activity

## Goals & Motivations

### Primary Goals
1. Know that no browser holds a reusable token: a stolen laptop or a script injected into the page cannot lift a refresh token (ADR-0051 D5)
2. Know that "signed out" means the upstream session and refresh token are revoked, and be told when that failed (ADR-0051 D4)
3. Keep audit storage bounded when an attacker floods bad credentials (F0002 carry-in)

### Success Metrics
- Zero tokens found in browser storage during review; every logout has a recorded upstream outcome; rejected-credential rows stay within the configured bound per client per window

## Pain Points & Frustrations

1. **Logout that only clears a cookie** — Impact: a refresh token keeps working upstream; Frequency: every logout; Severity: Critical
2. **Audit tables flooded by bad-credential bursts** — Impact: storage growth and noisy investigations; Frequency: during attacks; Severity: High
3. **UI-only session timeouts** — Impact: a modal is dismissed and the server session lives on; Frequency: daily; Severity: High

## Jobs-to-be-Done

1. **When** I disable a user or revoke a grant, **I want to** see the next request refused, **so I can** close an incident with evidence.
2. **When** a logout cannot reach the identity provider, **I want to** find a recorded failure, **so I can** revoke the session manually.
3. **When** one address floods bad credentials, **I want to** see it throttled with one summary event per window, **so I can** investigate without wading through thousands of rows.

## Constraints & Considerations

- Authorization: administers the identity provider and policy releases; holds no special data-read authority inside Nebula through the shell.
- Does not use the shell for administration in v0.1; evidence comes from audit rows and logs.

## Related Features

F0021 (session, logout, throttling), F0026 (retention, production ingress, AuthX negative tests).
