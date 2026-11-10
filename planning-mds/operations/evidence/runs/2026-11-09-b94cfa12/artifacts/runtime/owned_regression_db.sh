#!/usr/bin/env bash
# F0007 run 2026-11-09-b94cfa12: run a command against a fresh owned database at
# migration head, then drop it. Never migrates or truncates the shared dev DB.
# usage: owned_regression_db.sh <command...>   (cwd: product root)
set -u
ADMIN=postgresql://brain:brain@localhost:5432/brain
NAME="f0007_regr_$(python3 -c 'import secrets; print(secrets.token_hex(4))')"
docker exec brain-postgres psql -U brain -d brain -qAtc "CREATE DATABASE $NAME" >/dev/null
docker exec brain-postgres psql -U brain -d "$NAME" -qAtc "CREATE EXTENSION IF NOT EXISTS btree_gist" >/dev/null
( cd engine/migrations && BRAIN_DATABASE_URL="postgresql+psycopg://brain:brain@localhost:5432/$NAME" ../.venv/bin/alembic upgrade head >/dev/null 2>&1 ) || { echo "migration failed"; exit 3; }
echo "owned regression database: $NAME (alembic head applied)"
BRAIN_DATABASE_URL="postgresql+asyncpg://brain:brain@localhost:5432/$NAME" \
BRAIN_TEST_POSTGRES_URL="postgresql+psycopg://brain:brain@localhost:5432/$NAME" \
BRAIN_MIGRATION_ADMIN_URL="$ADMIN" "$@"
rc=$?
docker exec brain-postgres psql -U brain -d brain -qAtc "DROP DATABASE $NAME WITH (FORCE)" >/dev/null
echo "dropped $NAME; exit=$rc"
exit $rc
