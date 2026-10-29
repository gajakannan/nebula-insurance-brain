"""F0005 Step 2 negative controls: parent-owned deadline, latch, cleanup, orphans."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from threading import Event

import pytest
from brain_ingestion.conversion_process import (
    CONVERSION_DEADLINE_SECONDS,
    AttemptLatch,
    ConversionError,
    SupervisedConverter,
)
from brain_ingestion.worker_guard import group_members

PDF = b"%PDF-1.4\n% fixture\n"


def converter(tmp_path: Path, behavior: str, *, deadline: float = 3.0, delay: float = 0.0, **kw):
    root = tmp_path / "staging"
    return SupervisedConverter(
        root,
        deadline_seconds=deadline,
        child_args=(
            "--converter",
            "fixture",
            "--fixture-behavior",
            behavior,
            "--fixture-delay",
            str(delay),
        ),
        load_document=lambda raw: json.loads(raw),
        **kw,
    )


def assert_clean(supervisor: SupervisedConverter) -> None:
    assert list(supervisor.staging_root.iterdir()) == []


def test_production_deadline_is_300_seconds():
    assert CONVERSION_DEADLINE_SECONDS == 300.0
    assert SupervisedConverter(Path("/nonexistent")).deadline_seconds == 300.0


def test_valid_handoff_before_deadline_is_accepted_and_staging_removed(tmp_path):
    supervisor = converter(tmp_path, "complete")
    handoff = supervisor.convert(PDF, attempt_id="a1", capture_provenance=False)
    assert handoff.parsed.status == "complete" and handoff.parsed.document == {"fixture": True}
    assert handoff.diagnostics["decision"] == "accepted"
    assert handoff.diagnostics["group_confirmed_gone"] is True
    assert_clean(supervisor)


@pytest.mark.parametrize(
    "behavior", ["hang", "ignore_term", "helper_ignores_term", "block_staging"]
)
def test_hung_or_term_ignoring_child_times_out_once_with_bounded_group_cleanup(tmp_path, behavior):
    supervisor = converter(tmp_path, behavior, deadline=1.5)
    started = time.monotonic()
    with pytest.raises(ConversionError) as raised:
        supervisor.convert(PDF, attempt_id="a2", capture_provenance=False)
    elapsed = time.monotonic() - started
    diagnostics = raised.value.diagnostics
    assert raised.value.code == "conversion_timeout"
    # Decision at the deadline; cleanup is separate and bounded by 2 s + 3 s.
    assert 1.5 <= diagnostics["decision_seconds"] < 1.5 + 0.5
    assert diagnostics["cleanup_seconds"] <= 5.5
    assert elapsed <= 1.5 + 0.5 + 5.5
    assert diagnostics["group_confirmed_gone"] is True
    assert_clean(supervisor)


def test_completion_after_deadline_never_wins(tmp_path):
    supervisor = converter(tmp_path, "late", deadline=1.0, delay=1.6)
    with pytest.raises(ConversionError, match="conversion_timeout"):
        supervisor.convert(PDF, attempt_id="a3", capture_provenance=False)
    assert_clean(supervisor)


def test_latch_rechecks_clock_at_acceptance_with_injected_clock():
    now = [0.0]
    latch = AttemptLatch(deadline=300.0, clock=lambda: now[0])
    now[0] = 300.0  # completion frame validated exactly at the deadline
    assert latch.accept() is False and latch.outcome == "conversion_timeout"
    early = AttemptLatch(deadline=300.0, clock=lambda: now[0] - 0.001)
    assert early.accept() is True and early.decide("conversion_timeout") is False


def test_cancellation_uses_the_same_revoked_cleanup_path(tmp_path):
    supervisor = converter(tmp_path, "hang", deadline=30)
    cancelled = Event()
    cancelled.set()
    with pytest.raises(ConversionError, match="cancelled"):
        supervisor.convert(PDF, attempt_id="a4", capture_provenance=False, cancelled=cancelled)
    assert_clean(supervisor)


@pytest.mark.parametrize(
    ("behavior", "code"), [("fail", "conversion_failed"), ("stage_guard", "stage_guard_mismatch")]
)
def test_child_errors_are_stable_codes(tmp_path, behavior, code):
    supervisor = converter(tmp_path, behavior)
    with pytest.raises(ConversionError) as raised:
        supervisor.convert(PDF, attempt_id="a5", capture_provenance=False)
    assert raised.value.code == code
    assert_clean(supervisor)


def test_child_inherits_only_the_named_ipc_descriptors(tmp_path):
    guard = os.open(tmp_path / "guard.lock", os.O_RDWR | os.O_CREAT, 0o600)
    os.set_inheritable(guard, True)  # even an inheritable descriptor must not cross
    try:
        supervisor = converter(tmp_path, "report_inherited_fds")
        # A probe frame is not a valid handoff: the parent rejects it.
        with pytest.raises(ConversionError):
            supervisor.convert(PDF, attempt_id="a6", capture_provenance=False)
        # Run the child directly to observe its descriptor table.
        control_r, control_w = os.pipe()
        frame_r, frame_w = os.pipe()
        (tmp_path / "probe").mkdir()
        process = subprocess.Popen(
            [
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
                str(tmp_path / "probe"),
                "--nonce",
                "n",
                "--converter",
                "fixture",
                "--fixture-behavior",
                "report_inherited_fds",
            ],
            pass_fds=(control_r, frame_w),
            close_fds=True,
        )
        os.close(control_r)
        os.close(frame_w)
        os.write(control_w, b"start n\n")
        os.close(control_w)
        frame = json.loads(os.read(frame_r, 65536))
        process.wait(10)
        os.close(frame_r)
        assert guard not in frame["fds"]
        assert set(frame["fds"]) <= {0, 1, 2, control_r, frame_w}
    finally:
        os.close(guard)


def test_child_exits_without_converting_if_parent_closes_before_acknowledgement(tmp_path):
    control_r, control_w = os.pipe()
    frame_r, frame_w = os.pipe()
    (tmp_path / "s").mkdir()
    process = subprocess.Popen(
        [
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
            str(tmp_path / "s"),
            "--nonce",
            "n",
            "--converter",
            "fixture",
        ],
        pass_fds=(control_r, frame_w),
        close_fds=True,
    )
    os.close(control_r)
    os.close(frame_w)
    os.close(control_w)  # parent "dies" before the durable receipt/acknowledgement
    assert process.wait(10) == 3
    assert os.read(frame_r, 100) == b""
    assert list((tmp_path / "s").iterdir()) == []


def test_parent_killed_after_acknowledgement_leaves_a_discoverable_orphan(tmp_path):
    root = tmp_path / "staging"
    script = (
        "import json,sys\n"
        "from pathlib import Path\n"
        "from brain_ingestion.conversion_process import SupervisedConverter\n"
        f"s=SupervisedConverter(Path({str(root)!r}),deadline_seconds=60,"
        "child_args=('--converter','fixture','--fixture-behavior','helper_ignores_term'),"
        "load_document=json.loads)\n"
        "s.convert(b'%PDF-1.4\\n',attempt_id='orphan',capture_provenance=False)\n"
    )
    parent = subprocess.Popen([sys.executable, "-c", script])
    receipt = root / "orphan.launch.json"
    deadline = time.monotonic() + 20
    while not receipt.exists() and time.monotonic() < deadline:
        time.sleep(0.05)
    time.sleep(0.5)
    parent.kill()
    parent.wait()
    pgid = json.loads(receipt.read_bytes())["pgid"]
    assert group_members(pgid)  # converter and helper outlive the parent
    supervisor = SupervisedConverter(root, load_document=json.loads)
    assert supervisor.reap_orphans() == ["orphan"]
    assert group_members(pgid) == []
    assert list(root.iterdir()) == []


def test_reaper_never_kills_a_reused_pid(tmp_path):
    root = tmp_path / "staging"
    root.mkdir(mode=0o700)
    (root / "x").mkdir()
    (root / "x.launch.json").write_text(
        json.dumps(
            {
                "attempt_id": "x",
                "pid": os.getpid(),
                "pgid": os.getpid(),
                "start_ticks": 1,
                "staging": str(root / "x"),
            }
        )
    )
    with pytest.raises(ConversionError, match="converter_ownership_unconfirmed"):
        SupervisedConverter(root).reap_orphans()
    assert (root / "x").exists()


def test_a_receipt_from_an_earlier_boot_never_signals_a_reused_pid(tmp_path):
    # Code Review L3: after a reboot the recorded PID may name an unrelated process.
    import json as _json
    import subprocess as _subprocess

    from brain_ingestion import conversion_process as cp

    supervisor = cp.SupervisedConverter(tmp_path / "staging")
    supervisor._prepare_root()
    unrelated = _subprocess.Popen(["sleep", "60"], start_new_session=True)
    try:
        staging = supervisor.staging_root / "attempt-old"
        staging.mkdir()
        supervisor.receipt_path("attempt-old").write_text(
            _json.dumps(
                {
                    "attempt_id": "attempt-old",
                    "staging": str(staging),
                    "pid": unrelated.pid,
                    "pgid": unrelated.pid,
                    "start_ticks": 1,  # does not match the live process
                    "boot_id": "an-earlier-boot",
                }
            )
        )
        assert supervisor.reap_orphans() == ["attempt-old"]
        assert unrelated.poll() is None  # never signalled
        assert not staging.exists()
    finally:
        unrelated.kill()
        unrelated.wait()


def test_an_unreadable_current_boot_id_never_skips_a_live_converter(tmp_path, monkeypatch):
    # Delta review D-3: unknown is not proof of staleness; the reaper fails closed.
    import json as _json
    import subprocess as _subprocess

    from brain_ingestion import conversion_process as cp

    monkeypatch.setattr(cp, "boot_id", lambda: None)
    supervisor = cp.SupervisedConverter(tmp_path / "staging")
    supervisor._prepare_root()
    unrelated = _subprocess.Popen(["sleep", "60"], start_new_session=True)
    try:
        staging = supervisor.staging_root / "attempt-x"
        staging.mkdir()
        supervisor.receipt_path("attempt-x").write_text(
            _json.dumps(
                {
                    "attempt_id": "attempt-x",
                    "staging": str(staging),
                    "pid": unrelated.pid,
                    "pgid": unrelated.pid,
                    "start_ticks": 1,
                    "boot_id": "some-boot",
                }
            )
        )
        with pytest.raises(cp.ConverterCleanupFailed, match="converter_ownership_unconfirmed"):
            supervisor.reap_orphans()
        assert unrelated.poll() is None and staging.exists()
    finally:
        unrelated.kill()
        unrelated.wait()
