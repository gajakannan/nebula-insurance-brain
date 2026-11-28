-- F0021 migration design: 0018_f0021_browser_sessions (ADR-0082 D3, D9; Proposed).
-- Design input for the feature run; Alembic revision down_revision = 0017_f0012_ontology_releases.
-- Expand-only: four new tables, two nullable columns, one append-only trigger.
-- The 8-hour and 30-minute CHECKs encode operator decision D1; changing D1 needs a new migration.
-- Downgrade drops the four tables and two columns only when browser_session and session_event are empty;
-- otherwise it refuses (sessions are live security state; session_event is audit).

-- Server-owned display names for the shell (F0021-S0006 AC1). Nullable; dev seed sets them.
ALTER TABLE tenant         ADD COLUMN display_name text NULL CHECK (display_name IS NULL OR length(display_name) BETWEEN 1 AND 200);
ALTER TABLE knowledge_base ADD COLUMN display_name text NULL CHECK (display_name IS NULL OR length(display_name) BETWEEN 1 AND 200);

-- One row per started sign-in (F0021-S0001 AC1/AC4). Single use by conditional UPDATE … RETURNING.
CREATE TABLE browser_login_attempt (
    id                         uuid        PRIMARY KEY,
    state_digest               bytea       NOT NULL UNIQUE CHECK (length(state_digest) = 32),
    binding_digest             bytea       NOT NULL CHECK (length(binding_digest) = 32),
    nonce_digest               bytea       NOT NULL CHECK (length(nonce_digest) = 32),
    code_verifier_ciphertext   bytea       NOT NULL,
    key_id                     text        NOT NULL CHECK (key_id ~ '^[a-z0-9-]{1,32}$'),
    mode                       text        NOT NULL CHECK (mode IN ('redirect', 'popup')),
    reauth_ref                 text        NULL CHECK (reauth_ref IS NULL OR reauth_ref ~ '^[A-Za-z0-9_-]{22}$'),
    return_to                  text        NOT NULL CHECK (left(return_to, 1) = '/' AND length(return_to) <= 512),
    prompt_login               boolean     NOT NULL DEFAULT false,
    created_at                 timestamptz NOT NULL,
    expires_at                 timestamptz NOT NULL,
    consumed_at                timestamptz NULL,
    CHECK (expires_at = created_at + interval '10 minutes'),
    CHECK ((mode = 'popup') = (reauth_ref IS NOT NULL)),
    CHECK (consumed_at IS NULL OR consumed_at >= created_at)
);
CREATE INDEX ix_browser_login_attempt_expires ON browser_login_attempt (expires_at);

-- Server-side session (ADR-0051 D1, ADR-0082 D3). The cookie value is never stored; only its SHA-256.
CREATE TABLE browser_session (
    id                         uuid        PRIMARY KEY,
    cookie_digest              bytea       NOT NULL UNIQUE CHECK (length(cookie_digest) = 32),
    principal_id               uuid        NOT NULL REFERENCES principal (id),
    issuer                     text        NOT NULL,
    subject                    text        NOT NULL,
    display_name               text        NULL CHECK (display_name IS NULL OR length(display_name) BETWEEN 1 AND 200),
    created_at                 timestamptz NOT NULL,
    last_activity_at           timestamptz NOT NULL,
    idle_expires_at            timestamptz NOT NULL,
    absolute_expires_at        timestamptz NOT NULL,
    access_expires_at          timestamptz NULL,
    token_ciphertext           bytea       NULL,
    key_id                     text        NULL CHECK (key_id IS NULL OR key_id ~ '^[a-z0-9-]{1,32}$'),
    renewal_count              integer     NOT NULL DEFAULT 0 CHECK (renewal_count >= 0),
    csrf_digest                bytea       NOT NULL CHECK (length(csrf_digest) = 32),
    active_tenant_id           uuid        NULL,
    active_knowledge_base_id   uuid        NULL,
    ended_at                   timestamptz NULL,
    end_reason                 text        NULL CHECK (end_reason IS NULL OR end_reason IN (
                                   'logout', 'idle_timeout', 'absolute_timeout', 'renewal_failed',
                                   'replaced', 'principal_changed', 'principal_disabled', 'principal_mismatch')),
    CHECK (absolute_expires_at = created_at + interval '8 hours'),
    CHECK (idle_expires_at <= absolute_expires_at),
    CHECK (idle_expires_at = last_activity_at + interval '30 minutes' OR idle_expires_at = absolute_expires_at),
    CHECK ((ended_at IS NULL) = (end_reason IS NULL)),
    CHECK ((token_ciphertext IS NULL) = (key_id IS NULL)),
    CHECK (ended_at IS NULL OR token_ciphertext IS NULL),          -- an ended session holds no tokens
    CHECK (ended_at IS NOT NULL OR token_ciphertext IS NOT NULL),  -- a live session always holds tokens
    CHECK ((active_tenant_id IS NULL) = (active_knowledge_base_id IS NULL)),
    FOREIGN KEY (active_knowledge_base_id, active_tenant_id) REFERENCES knowledge_base (id, tenant_id)
);
CREATE INDEX ix_browser_session_principal_live ON browser_session (principal_id) WHERE ended_at IS NULL;

-- Append-only session lifecycle audit (F0021-S0003 AC3 renewal record, S0005 AC3/AC7 logout outcome, S0006 AC4).
CREATE TABLE session_event (
    event_id                   uuid        PRIMARY KEY,
    occurred_at                timestamptz NOT NULL,
    session_id                 uuid        NOT NULL REFERENCES browser_session (id),
    principal_id               uuid        NOT NULL REFERENCES principal (id),
    event_type                 text        NOT NULL CHECK (event_type IN (
                                   'session_created', 'session_replaced', 'renewed', 'renewal_failed',
                                   'ended_idle', 'ended_absolute', 'ended_principal_changed',
                                   'ended_principal_disabled', 'ended_principal_mismatch',
                                   'logout', 'active_knowledge_base_changed')),
    trace_id                   text        NOT NULL,
    payload                    jsonb       NOT NULL DEFAULT '{}'::jsonb,
    -- logout payload: {"revocation": {"status", "reason"?}, "end_session": {"status"}}; never a token or cookie value.
    CHECK (event_type <> 'logout' OR (payload ? 'revocation' AND payload ? 'end_session'))
);
CREATE INDEX ix_session_event_session ON session_event (session_id, occurred_at);
-- Reuse the migration 0007 append-only trigger function brain_append_only(): UPDATE and DELETE are refused,
-- exactly as for audit_event and authentication_event.
CREATE TRIGGER trg_session_event_append_only
    BEFORE UPDATE OR DELETE ON session_event
    FOR EACH ROW EXECUTE FUNCTION brain_append_only();

-- Rejected-credential counters (F0021-S0008, ADR-0082 D9). Mutable; not audit.
CREATE TABLE credential_rejection_window (
    client_key                 text        NOT NULL CHECK (length(client_key) BETWEEN 1 AND 64),
    window_start               timestamptz NOT NULL CHECK (date_trunc('minute', window_start) = window_start),
    rejected_count             integer     NOT NULL CHECK (rejected_count >= 1),
    PRIMARY KEY (client_key, window_start)
);
CREATE INDEX ix_credential_rejection_window_start ON credential_rejection_window (window_start);

-- Counting statement (one round trip, atomic across workers):
--   INSERT INTO credential_rejection_window (client_key, window_start, rejected_count)
--   VALUES ($1, date_trunc('minute', now()), 1)
--   ON CONFLICT (client_key, window_start) DO UPDATE SET rejected_count = credential_rejection_window.rejected_count + 1
--   RETURNING rejected_count;
-- Pruning: DELETE FROM credential_rejection_window WHERE window_start < now() - interval '10 minutes'
--   (run when the returned count is 1, i.e. once per new window per client).

-- Renewal lock (ADR-0082 D6), separate short transaction:
--   SET LOCAL lock_timeout = '15s';
--   SELECT … FROM browser_session WHERE id = $1 AND ended_at IS NULL FOR UPDATE;
--   (re-check access_expires_at; refresh only if still within the 60 s margin; UPDATE; COMMIT)
