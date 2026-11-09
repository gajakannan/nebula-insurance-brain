# Security Review — 2026-11-09

Date: 2026-11-09
Reviewer: Security role (changes executed by Claude Code for the operator)
Status: Remediation recorded; independent Security verification pending at the PR

## Scope

- SEC-03 (Low, F0006 review, due 2026-11-17), together with F0004 SEC-L2: baseline response headers.
- SEC-F5-M1 (F0005 review): the part that can be delivered without host privileges, network isolation for the conversion child. The memory, CPU and task ceilings were delivered on 2026-11-08 ([review](security-review-2026-11-08.md)).

## SEC-03 / F0004 SEC-L2 — response headers

A pure ASGI middleware (`brain_api/security_headers.py`) adds `X-Content-Type-Options: nosniff` and `Cross-Origin-Resource-Policy: same-origin` to every HTTP response, without overriding headers a route already set. Starlette answers unhandled exceptions outside user middleware, so a new 500 handler returns problem details with the same headers and no exception text.

**Evidence:** `engine/apps/api/tests/test_security_headers.py` covers the public health route, an unauthenticated protected route, a BrainError problem response, a validation error, a framework 404, an unhandled 500 (no leaked text), and a route-set header that is not duplicated. Engine ruff, mypy and API tests pass; the full engine suite shows the same 13 environment-dependent AuthX failures as `main`.

## SEC-F5-M1 — converter network isolation

With `conversion.network: isolated` (the committed default), the child runs inside its cgroup scope in its own unprivileged user and network namespace (`unshare --user --map-current-user --net`). The namespace has only a downed loopback; outbound connections fail with "network unreachable". `unshare` execs in place, so the recorded PID, process group, IPC pipes and cleanup are unchanged. The worker probes the namespace at startup and refuses to start without it.

**Evidence:** `test_conversion_limits.py` shows the isolated child sees only `lo`; conversion, timeout and group cleanup work through the namespace; cgroup and network isolation compose; startup fails closed without `unshare` or when the namespace cannot start. Real native and OCR conversions using the committed configuration exactly as the worker loads it (cgroup + no network) complete, at peak 2.6 / 2.9 GiB. Conversion now depends on locally cached model weights.

**Not delivered:** a separate OS user or container for the converter. That needs host privileges (a system user or a container runtime) and is a deployment decision. Until then the child shares the worker's OS user and filesystem permissions.

## Assessment

- Critical: 0
- High: 0
- Medium: 1 open — SEC-F5-M1 remainder (separate OS user or container)
- Low: 0 open — SEC-03 / SEC-L2 resolved

## Recommendations

1. Independent Security verification of this record on the PR.
2. Decide the converter's separate identity with the production host (blueprint 117.1 item 3): a dedicated system user, or a container with its own user, read-only staging mount and no network.
