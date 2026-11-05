"""Create only this run's dedicated runtime DB; preserve historical databases."""
import os
from pathlib import Path

import psycopg
from alembic import command
from alembic.config import Config
from psycopg import sql

name = "brain_f0006_runtime"
with psycopg.connect("postgresql://brain:brain@postgres:5432/postgres", autocommit=True) as connection:
    if not connection.execute("SELECT 1 FROM pg_database WHERE datname=%s", (name,)).fetchone():
        connection.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
with psycopg.connect(f"postgresql://brain:brain@postgres:5432/{name}", autocommit=True) as connection:
    connection.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")
os.environ["BRAIN_DATABASE_URL"] = f"postgresql+psycopg://brain:brain@postgres:5432/{name}"
config = Config("engine/migrations/alembic.ini")
config.set_main_option("script_location", str(Path("engine/migrations").resolve()))
command.upgrade(config, "head")
print("Dedicated F0006 runtime database ready at migration 0011")
