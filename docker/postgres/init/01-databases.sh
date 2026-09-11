#!/bin/bash
# Creates the authentik database alongside the default `brain` database
# (POSTGRES_DB). Mounted into /docker-entrypoint-initdb.d/ and runs once on
# first container start.
set -euo pipefail

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    SELECT 'CREATE DATABASE authentik'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'authentik')\gexec
EOSQL
