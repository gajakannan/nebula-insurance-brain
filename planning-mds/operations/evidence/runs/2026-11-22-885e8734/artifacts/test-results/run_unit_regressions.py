"""Run the existing job PostgreSQL checks against their owned temporary schemas."""

import os
import sys

import pytest

# Reuse the established local test connection without persisting/logging its DSN.
# Each selected job test creates and drops only its own random schema.
os.environ["BRAIN_TEST_POSTGRES_URL"] = os.environ["BRAIN_WORKER_DATABASE_URL"]
raise SystemExit(pytest.main(sys.argv[1:]))
