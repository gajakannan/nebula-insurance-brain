"""SEC-01 negative controls: conversion child resource containment.

A wall-clock deadline does not bound memory, so these tests prove that an
over-allocating child is ended by the parent's memory sampler (every mode) and
by the kernel-enforced cgroup ceiling (cgroup mode), and that the child sets its
own CPU, file-size, open-file and core-dump limits before any parser loads.
"""

from __future__ import annotations

import json
import os
import resource
import subprocess
import sys
from pathlib import Path

import pytest
from brain_ingestion import conversion_process as cp
from brain_ingestion.conversion_process import (
    MIB,
    ConversionError,
    ConversionLimits,
    IsolationUnavailable,
    SupervisedConverter,
)

PDF = b"%PDF-1.4\n% fixture\n"


def _cgroup_available() -> bool:
    try:
        cp.probe_cgroup_isolation(ConversionLimits(memory_bytes=256 * MIB))
    except IsolationUnavailable:
        return False
    return True


needs_cgroup = pytest.mark.skipif(
    not _cgroup_available(), reason="systemd user scope with memory delegation unavailable"
)


def _netns_available() -> bool:
    try:
        cp.probe_isolation(ConversionLimits(network="isolated"))
    except IsolationUnavailable:
        return False
    return True


needs_netns = pytest.mark.skipif(
    not _netns_available(), reason="unprivileged user and network namespaces unavailable"
)


def allocating(tmp_path: Path, limits: ConversionLimits, mib: int) -> SupervisedConverter:
    return SupervisedConverter(
        tmp_path / "staging",
        deadline_seconds=60,
        child_args=(
            "--converter",
            "fixture",
            "--fixture-behavior",
            "allocate",
            "--fixture-mib",
            str(mib),
        ),
        load_document=json.loads,
        limits=limits,
    )


def probe_child(tmp_path: Path, limits: ConversionLimits, prefix: list[str]) -> dict:
    """Run the child directly so its probe frame can be read."""
    control_r, control_w = os.pipe()
    frame_r, frame_w = os.pipe()
    staging = tmp_path / "probe"
    staging.mkdir()
    process = subprocess.Popen(
        [
            *prefix,
            sys.executable,
            "-m",
            "brain_ingestion.conversion_process",
            "--child",
            "--control-fd",
            str(control_r),
            "--frame-fd",
            str(frame_w),
            "--source",
            "/dev/null",
            "--staging",
            str(staging),
            "--nonce",
            "n",
            "--cpu-seconds",
            str(limits.cpu_seconds),
            "--file-size-bytes",
            str(limits.file_size_bytes),
            "--open-files",
            str(limits.open_files),
            "--converter",
            "fixture",
            "--fixture-behavior",
            "report_limits",
        ],
        pass_fds=(control_r, frame_w),
        close_fds=True,
    )
    os.close(control_r)
    os.close(frame_w)
    os.write(control_w, b"start n\n")
    os.close(control_w)
    assert process.wait(timeout=60) == 0
    with os.fdopen(frame_r, "rb") as frames:
        return json.loads(frames.read().split(b"\n", 1)[0])


def test_limits_reject_invalid_values():
    with pytest.raises(ValueError):
        ConversionLimits(memory_bytes=0)
    with pytest.raises(ValueError):
        ConversionLimits(isolation="none")  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        ConversionLimits(network="none")  # type: ignore[arg-type]


def test_child_sets_cpu_file_descriptor_and_core_limits_before_parsing(tmp_path):
    limits = ConversionLimits(cpu_seconds=77, file_size_bytes=12 * MIB, open_files=256)
    probe = probe_child(tmp_path, limits, prefix=[])
    assert probe["limits"]["RLIMIT_CPU"] == [77, 77]
    assert probe["limits"]["RLIMIT_FSIZE"] == [12 * MIB, 12 * MIB]
    assert probe["limits"]["RLIMIT_NOFILE"] == [256, 256]
    assert probe["limits"]["RLIMIT_CORE"] == [0, 0]


def test_child_never_raises_a_limit_above_an_inherited_hard_ceiling(tmp_path):
    hard = resource.getrlimit(resource.RLIMIT_NOFILE)[1]
    limits = ConversionLimits(open_files=hard + 1000 if hard != resource.RLIM_INFINITY else 1024)
    probe = probe_child(tmp_path, limits, prefix=[])
    assert probe["limits"]["RLIMIT_NOFILE"][1] <= hard


def test_watchdog_mode_ends_an_over_allocating_child_at_the_memory_ceiling(tmp_path):
    limits = ConversionLimits(isolation="watchdog", memory_bytes=256 * MIB)
    supervisor = allocating(tmp_path, limits, mib=2048)
    with pytest.raises(ConversionError) as raised:
        supervisor.convert(PDF, attempt_id="m1", capture_provenance=False)
    diagnostics = raised.value.diagnostics
    assert raised.value.code == "conversion_failed"
    assert diagnostics["resource_limit"] == "memory"
    assert diagnostics["isolation"] == "watchdog"
    # Sampled every 100 ms while the child grows 64 MiB per 50 ms: bounded overshoot.
    assert 256 * MIB < diagnostics["peak_rss_bytes"] < 1024 * MIB
    assert diagnostics["decision_seconds"] < 30
    assert diagnostics["group_confirmed_gone"] is True
    assert list(supervisor.staging_root.iterdir()) == []


def test_a_child_within_its_limits_still_completes(tmp_path):
    supervisor = SupervisedConverter(
        tmp_path / "staging",
        deadline_seconds=10,
        child_args=("--converter", "fixture", "--fixture-behavior", "complete"),
        load_document=json.loads,
        limits=ConversionLimits(isolation="watchdog", memory_bytes=1024 * MIB),
    )
    handoff = supervisor.convert(PDF, attempt_id="m2", capture_provenance=False)
    assert handoff.diagnostics["decision"] == "accepted"
    assert "resource_limit" not in handoff.diagnostics


def test_cgroup_isolation_fails_closed_without_systemd_run(tmp_path, monkeypatch):
    monkeypatch.setattr(cp.shutil, "which", lambda _name: None)
    with pytest.raises(IsolationUnavailable) as raised:
        SupervisedConverter(tmp_path / "staging", limits=ConversionLimits(isolation="cgroup"))
    assert raised.value.code == "conversion_isolation_unavailable"


def test_cgroup_isolation_fails_closed_when_the_scope_cannot_start(tmp_path, monkeypatch):
    def refused(*_args, **_kwargs):
        return subprocess.CompletedProcess([], 1)

    monkeypatch.setattr(cp.shutil, "which", lambda _name: "/usr/bin/systemd-run")
    monkeypatch.setattr(cp.subprocess, "run", refused)
    with pytest.raises(IsolationUnavailable):
        SupervisedConverter(tmp_path / "staging", limits=ConversionLimits(isolation="cgroup"))


@needs_cgroup
def test_cgroup_child_runs_under_kernel_memory_swap_and_task_ceilings(tmp_path):
    limits = ConversionLimits(isolation="cgroup", memory_bytes=512 * MIB, max_tasks=64)
    probe = probe_child(tmp_path, limits, prefix=cp._scope_command(limits))
    assert probe["cgroup"].endswith(".scope")
    assert probe["controls"] == {
        "memory.max": str(512 * MIB),
        "memory.swap.max": "0",
        "pids.max": "64",
    }


@needs_cgroup
def test_cgroup_ceiling_kills_an_over_allocating_child_even_without_sampling(tmp_path, monkeypatch):
    # Disable the parent sampler so only the kernel-enforced ceiling can act.
    monkeypatch.setattr(cp, "group_rss_bytes", lambda _pgid: 0)
    limits = ConversionLimits(isolation="cgroup", memory_bytes=256 * MIB)
    supervisor = allocating(tmp_path, limits, mib=2048)
    with pytest.raises(ConversionError) as raised:
        supervisor.convert(PDF, attempt_id="m3", capture_provenance=False)
    diagnostics = raised.value.diagnostics
    assert raised.value.code == "conversion_failed"
    assert diagnostics["child_signal"] == 9  # cgroup OOM kill
    assert "resource_limit" not in diagnostics
    assert diagnostics["group_confirmed_gone"] is True
    assert list(supervisor.staging_root.iterdir()) == []


@needs_netns
def test_network_isolated_child_sees_only_loopback(tmp_path):
    limits = ConversionLimits(network="isolated")
    probe = probe_child(tmp_path, limits, prefix=cp._launch_prefix(limits))
    assert probe["interfaces"] == ["lo"]


@needs_netns
def test_network_isolated_conversion_completes_with_ipc_receipt_and_cleanup(tmp_path):
    # unshare execs in place, so the recorded PID, process group and pipes stay valid.
    supervisor = SupervisedConverter(
        tmp_path / "staging",
        deadline_seconds=30,
        child_args=("--converter", "fixture", "--fixture-behavior", "complete"),
        load_document=json.loads,
        limits=ConversionLimits(network="isolated"),
    )
    handoff = supervisor.convert(PDF, attempt_id="n1", capture_provenance=False)
    assert handoff.diagnostics["decision"] == "accepted"
    assert handoff.diagnostics["network"] == "isolated"
    assert handoff.diagnostics["group_confirmed_gone"] is True
    assert list(supervisor.staging_root.iterdir()) == []


@needs_netns
def test_network_isolated_timeout_still_cleans_up_the_group(tmp_path):
    supervisor = SupervisedConverter(
        tmp_path / "staging",
        deadline_seconds=1.0,
        child_args=("--converter", "fixture", "--fixture-behavior", "hang"),
        load_document=json.loads,
        limits=ConversionLimits(network="isolated"),
    )
    with pytest.raises(ConversionError) as raised:
        supervisor.convert(PDF, attempt_id="n2", capture_provenance=False)
    assert raised.value.code == "conversion_timeout"
    assert raised.value.diagnostics["group_confirmed_gone"] is True


@needs_cgroup
@needs_netns
def test_cgroup_and_network_isolation_compose(tmp_path):
    limits = ConversionLimits(isolation="cgroup", network="isolated", memory_bytes=512 * MIB)
    probe = probe_child(tmp_path, limits, prefix=cp._launch_prefix(limits))
    assert probe["interfaces"] == ["lo"]
    assert probe["controls"]["memory.max"] == str(512 * MIB)


def test_network_isolation_fails_closed_without_unshare(tmp_path, monkeypatch):
    monkeypatch.setattr(cp.shutil, "which", lambda name: None if name == "unshare" else name)
    with pytest.raises(IsolationUnavailable):
        SupervisedConverter(tmp_path / "staging", limits=ConversionLimits(network="isolated"))


def test_network_isolation_fails_closed_when_the_namespace_cannot_start(tmp_path, monkeypatch):
    monkeypatch.setattr(cp.shutil, "which", lambda name: f"/usr/bin/{name}")
    monkeypatch.setattr(cp.subprocess, "run", lambda *_a, **_k: subprocess.CompletedProcess([], 1))
    with pytest.raises(IsolationUnavailable):
        SupervisedConverter(tmp_path / "staging", limits=ConversionLimits(network="isolated"))
