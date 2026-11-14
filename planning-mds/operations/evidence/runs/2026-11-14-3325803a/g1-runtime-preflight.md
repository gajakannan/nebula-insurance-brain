# G1 Runtime Preflight — F0064

Role: DevOps (Claude Opus 5.5). Date: 2026-11-14.

## Applicability

`runtime_bearing` is false. F0064 adds no runtime code, container, service, migration or model call. Its "runtime" is the repository toolchain: the framework checkout at the pin, the two Python interpreters, and a clean product tree. DevOps is a required role (S0004 covers CI and the pin contract), so the toolchain is preflighted instead of recording a bare omission. Raw output: `artifacts/test-results/g1-preflight.txt`.

## Checks

| Check | Observed | Result |
|---|---|---|
| Framework checkout at the pin | `nebula-agents` HEAD `d90bbb6fc70dffcfa6d70379d42015e895a49fa0`, clean tree | PASS |
| Pin agreement | `.github/workflows/ci-gates.yml:307` `ref: d90bbb6…a49fa0`; BLUEPRINT section 0 names the same full SHA once | PASS |
| Product interpreter | `.venv/bin/python` 3.12.13 with PyYAML 6.0.2 and pytest 9.0.3 | PASS |
| Framework interpreter | `nebula-agents/.venv/bin/python` 3.14.4; system `python3` is 3.14.4 | PASS |
| Product tree | branch `feature/F0064-retro-closeout` at `fcb249d` (= `origin/main`); no changes outside this run folder | PASS |
| Product root | `NEBULA_PRODUCT_ROOT` set; every framework call also passes `--product-root` explicitly | PASS |

No container or network service is needed. CI (S0004 AC4) is the only remote dependency, and it runs on the closeout PR.

## Failure Triage

If a toolchain command fails with an environment symptom (missing interpreter or module, framework not at the pin), stop edits, restore the toolchain, and rerun the same command before classifying it as a defect.

## Result

PASS
