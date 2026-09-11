#!/usr/bin/env python3
"""Verify the F0001-S0002 authentik dev seed (two tenants, one service client).

authentik provisions `docker/authentik/blueprints/nebula-brain-dev.yaml` declaratively on
container boot (it scans `/blueprints/**`). This script does not provision principals
itself — it confirms the blueprint applied, using the same ROPC token flow S0006's proof
harness will use, so a broken blueprint is caught in CI/dev before a proof story blocks on it.

Usage:
    python3 scripts/dev/seed_principals.py [--base-url http://localhost:9010]
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request

EXPECTED_USERNAMES = ("alice.tenant-a", "bob.tenant-b", "brain-service")
DEV_TOKEN = "brain-dev-token"  # noqa: S105 — dev-only fixture value, never a real secret


def _get_token(base_url: str, username: str) -> str:
    """Exchange the seeded app-password token for an access token via ROPC,
    proving both the principal and its token exist and are usable."""
    body = (
        f"grant_type=password&client_id=brain&username={username}&password={DEV_TOKEN}"
    ).encode("ascii")
    request = urllib.request.Request(
        f"{base_url}/application/o/token/",
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=10) as response:  # noqa: S310
        payload = json.loads(response.read())
    return str(payload["access_token"])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://localhost:9010")
    args = parser.parse_args()

    failures: list[str] = []
    for username in EXPECTED_USERNAMES:
        try:
            _get_token(args.base_url, username)
            print(f"ok: {username} authenticates via ROPC")
        except (urllib.error.URLError, KeyError, json.JSONDecodeError) as exc:
            failures.append(f"{username}: {exc}")

    if failures:
        print("Seed verification failed:", file=sys.stderr)
        for failure in failures:
            print(f"  {failure}", file=sys.stderr)
        return 1

    print(f"All {len(EXPECTED_USERNAMES)} seeded principals verified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
