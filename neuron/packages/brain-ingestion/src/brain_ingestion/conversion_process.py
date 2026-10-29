"""Supervised physical conversion with a parent-owned decision deadline (F0005 Step 2).

The authorized parent owns the lease, host guard, content store and ready
publication. A spawned conversion-only child runs the pinned Graph stage guard
with real Docling/OCR and hands back a validated native-JSON/quality/provenance
frame through private staging. Only the parent decides the outcome: a monotonic
deadline set immediately before launch, a watchdog independent of converter, IPC
and staging I/O, and one attempt latch that a late completion can never win.

Protocol: the child blocks until the parent has durably written a launch receipt
(attempt nonce, staging path, process-group identity) and sent the start
acknowledgement; parent IPC closure before that makes the child exit without
converting. The child's environment carries no database, inference or
application credentials, it has no model transport, and it cannot publish.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import select
import shutil
import subprocess
import sys
import threading
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from pathlib import Path
from threading import Event
from typing import Any, Literal

from brain_interpretation.parsed_content import (
    BlockOriginInput,
    OcrObservation,
    ParseResult,
    ProducerIdentity,
)

from brain_ingestion.worker_guard import (
    _atomic_write,
    group_members,
    process_start_ticks,
    terminate_group,
)

CONVERSION_DEADLINE_SECONDS = 300.0
TERM_GRACE_SECONDS = 2.0
KILL_GRACE_SECONDS = 3.0
MAX_FRAME_BYTES = 64 * 1024
_FILES = ("docling-document.json", "parse.json")
# Only non-secret runtime settings cross into the converter environment.
_CHILD_ENV = (
    "PATH",
    "HOME",
    "LANG",
    "LC_ALL",
    "TZ",
    "HF_HOME",
    "HF_HUB_CACHE",
    "HF_HUB_OFFLINE",
    "TRANSFORMERS_OFFLINE",
    "OMP_NUM_THREADS",
    "CUDA_VISIBLE_DEVICES",
    "LITELLM_LOCAL_MODEL_COST_MAP",
    "DOCLING_ARTIFACTS_PATH",
)

Outcome = Literal["accepted", "conversion_timeout", "cancelled", "conversion_failed"]


class ConversionError(RuntimeError):
    """Stable reason; never contains converter output or source text."""

    def __init__(self, code: str, diagnostics: dict[str, Any] | None = None) -> None:
        self.code = code
        self.diagnostics = diagnostics or {}
        super().__init__(code)


class ConverterCleanupFailed(ConversionError):
    """The child group could not be confirmed gone: stop the worker, keep the guard."""


@dataclass(slots=True)
class AttemptLatch:
    """Serializes completion, timeout and cancellation for one attempt."""

    deadline: float
    clock: Callable[[], float]
    outcome: Outcome | None = None
    decided_at: float | None = None
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def decide(self, outcome: Outcome) -> bool:
        with self._lock:
            if self.outcome is not None:
                return False
            self.outcome, self.decided_at = outcome, self.clock()
            return True

    def accept(self) -> bool:
        """Accept a validated handoff only if nothing else won and time remains."""
        with self._lock:
            if self.outcome is not None:
                return False
            now = self.clock()
            # WHY: re-check the deadline at acceptance, under the lock: a handoff that
            # arrives after 300 s loses even if the watchdog has not fired yet.
            if now >= self.deadline:
                self.outcome, self.decided_at = "conversion_timeout", now
                return False
            self.outcome, self.decided_at = "accepted", now
            return True


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _encode_parse(parsed: ParseResult[Any]) -> dict[str, Any]:
    return {
        "page_count": parsed.page_count,
        "failed_pages": list(parsed.failed_pages),
        "ocr_page_count": parsed.ocr_page_count,
        "status": parsed.status,
        "warnings": list(parsed.warnings),
        "projection_version": parsed.projection_version,
        "provenance": {
            ref: [{**asdict(origin), "producer": asdict(origin.producer)} for origin in origins]
            for ref, origins in parsed.provenance.items()
        },
        "origin_unavailable": list(parsed.origin_unavailable),
        "page_rotations": {str(page): rotation for page, rotation in parsed.page_rotations.items()},
        "model_artifact_digests": list(parsed.model_artifact_digests),
        "ocr": None
        if parsed.ocr is None
        else {
            "pages": list(parsed.ocr.pages),
            "engine": None if parsed.ocr.engine is None else asdict(parsed.ocr.engine),
        },
    }


def _decode_ocr(data: dict[str, Any] | None) -> OcrObservation | None:
    if data is None:
        return None
    engine = data["engine"]
    return OcrObservation(
        pages=tuple(int(page) for page in data["pages"]),
        engine=None if engine is None else ProducerIdentity(**engine),
    )


def decode_parse(document: Any, data: dict[str, Any]) -> ParseResult[Any]:
    return ParseResult(
        document=document,
        page_count=int(data["page_count"]),
        failed_pages=[int(page) for page in data["failed_pages"]],
        ocr_page_count=int(data["ocr_page_count"]),
        status=data["status"],
        warnings=[str(warning) for warning in data["warnings"]],
        projection_version=data["projection_version"],
        provenance={
            ref: tuple(
                BlockOriginInput(
                    native_ref=origin["native_ref"],
                    text=origin["text"],
                    text_origin=origin["text_origin"],
                    producer=ProducerIdentity(**origin["producer"]),
                    origin_anchor=origin["origin_anchor"],
                    confidence=origin["confidence"],
                )
                for origin in origins
            )
            for ref, origins in data["provenance"].items()
        },
        origin_unavailable=tuple(data["origin_unavailable"]),
        page_rotations={
            int(page): int(rotation) for page, rotation in data["page_rotations"].items()
        },
        model_artifact_digests=tuple(data["model_artifact_digests"]),
        ocr=_decode_ocr(data.get("ocr")),
    )


# ---------------------------------------------------------------------------
# Child: conversion only, no publication capability and no model transport.
# ---------------------------------------------------------------------------


class _NoInferenceClient:
    """The child never contacts a model; any request is an integration defect."""

    def get_json_response(self, *_args: Any, **_kwargs: Any) -> Any:
        raise RuntimeError("conversion child has no inference transport")

    def get_json_response_stream(self, *_args: Any, **_kwargs: Any) -> Any:
        raise RuntimeError("conversion child has no inference transport")


def _write_frame(fd: int, frame: dict[str, Any]) -> None:
    payload = json.dumps(frame, sort_keys=True).encode() + b"\n"
    if len(payload) > MAX_FRAME_BYTES:
        payload = json.dumps({"type": "error", "code": "conversion_failed"}).encode() + b"\n"
    os.write(fd, payload)


def _child(args: argparse.Namespace) -> int:
    control = os.fdopen(args.control_fd, "rb", buffering=0)
    start = control.readline()
    if start != f"start {args.nonce}\n".encode():
        # The parent closed IPC before durably recording this child.
        return 3
    staging, source = Path(args.staging), Path(args.source)
    if args.converter == "fixture":
        # Test-only negative controls: no Docling, real process behavior.
        return _fixture_converter(args, staging)
    from brain_extraction.docling_graph_pipeline import (
        DoclingGraphPipelineAdapter,
        StageLayoutMismatch,
    )

    try:
        from brain_extraction.profiles import load_profile

        from brain_ingestion.docling_adapter import DoclingAdapter

        adapter = DoclingAdapter(capture_provenance=args.provenance)
        frame: dict[str, Any] = {}

        def serialize(parsed: ParseResult[Any]) -> None:
            out = staging / "out"
            out.mkdir(mode=0o700)
            _atomic_write(out / "docling-document.json", parsed.document.model_dump_json().encode())
            _atomic_write(
                out / "parse.json", json.dumps(_encode_parse(parsed), sort_keys=True).encode()
            )
            frame.update(
                type="complete",
                nonce=args.nonce,
                source_sha256=_sha256_file(source),
                files={name: _sha256_file(out / name) for name in _FILES},
                status=parsed.status,
                guard=_stage_guard(),
            )
            # Raising here ends the conversion-only run before any extraction stage.

        DoclingGraphPipelineAdapter(llm_client=_NoInferenceClient(), model_id="none").run(
            source=source,
            template=load_profile("gl-limits-a").template,
            converter=adapter.parse,
            publish=serialize,
            conversion_only=True,
        )
        if frame.get("type") != "complete":
            raise RuntimeError("conversion produced no handoff")
        _write_frame(args.frame_fd, frame)
        return 0
    except StageLayoutMismatch:
        _write_frame(
            args.frame_fd, {"type": "error", "nonce": args.nonce, "code": "stage_guard_mismatch"}
        )
        return 4
    except Exception:
        # Converter exceptions may contain source text; only the code crosses IPC.
        _write_frame(
            args.frame_fd, {"type": "error", "nonce": args.nonce, "code": "conversion_failed"}
        )
        return 5


def _fixture_converter(args: argparse.Namespace, staging: Path) -> int:
    """Deterministic child behaviors for the deadline/cleanup negative controls."""
    import signal

    behavior = args.fixture_behavior
    if behavior in ("ignore_term", "helper_ignores_term"):
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
    if behavior == "helper_ignores_term":
        subprocess.Popen(
            [
                sys.executable,
                "-c",
                "import signal,time;signal.signal(signal.SIGTERM,signal.SIG_IGN);time.sleep(600)",
            ],
            close_fds=True,
        )
    if behavior in ("hang", "ignore_term", "helper_ignores_term"):
        time.sleep(600)
        return 0
    if behavior == "block_staging":
        # The staging callback blocks across the parent's deadline selection.
        (staging / "out").mkdir(mode=0o700)
        time.sleep(600)
        return 0
    if behavior == "report_inherited_fds":
        listed = [int(fd) for fd in os.listdir("/proc/self/fd")]
        inherited = []
        for fd in listed:
            try:
                target = os.readlink(f"/proc/self/fd/{fd}")
            except OSError:
                continue  # the directory handle used for this listing, now closed
            if not target.startswith("/proc/"):
                inherited.append(fd)
        inherited.sort()
        _write_frame(args.frame_fd, {"type": "probe", "fds": inherited})
        return 0
    if behavior == "fail":
        _write_frame(
            args.frame_fd, {"type": "error", "nonce": args.nonce, "code": "conversion_failed"}
        )
        return 5
    if behavior == "stage_guard":
        _write_frame(
            args.frame_fd, {"type": "error", "nonce": args.nonce, "code": "stage_guard_mismatch"}
        )
        return 4
    # "complete" / "late": a valid handoff, optionally after a delay.
    time.sleep(args.fixture_delay)
    out = staging / "out"
    out.mkdir(mode=0o700)
    document = json.dumps({"fixture": True}).encode()
    parse = {
        "page_count": 1,
        "failed_pages": [],
        "ocr_page_count": 0,
        "status": "complete",
        "warnings": [],
        "projection_version": None,
        "provenance": {},
        "origin_unavailable": [],
        "page_rotations": {},
        "model_artifact_digests": [],
    }
    _atomic_write(out / "docling-document.json", document)
    _atomic_write(out / "parse.json", json.dumps(parse).encode())
    _write_frame(
        args.frame_fd,
        {
            "type": "complete",
            "nonce": args.nonce,
            "source_sha256": _sha256_file(Path(args.source)),
            "files": {name: _sha256_file(out / name) for name in _FILES},
            "status": "complete",
            "guard": _stage_guard(),
        },
    )
    return 0


# ---------------------------------------------------------------------------
# Parent: deadline, latch, validation, cleanup and orphan recovery.
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ConversionHandoff:
    parsed: ParseResult[Any]
    diagnostics: dict[str, Any]


def _child_environment() -> dict[str, str]:
    environment = {name: os.environ[name] for name in _CHILD_ENV if name in os.environ}
    environment["PYTHONNOUSERSITE"] = "1"
    return environment


class SupervisedConverter:
    """One supervised physical conversion per call; parent alone decides."""

    def __init__(
        self,
        staging_root: Path,
        *,
        deadline_seconds: float = CONVERSION_DEADLINE_SECONDS,
        clock: Callable[[], float] = time.monotonic,
        python: str = sys.executable,
        child_args: tuple[str, ...] = (),
        load_document: Callable[[bytes], Any] | None = None,
        term_grace: float = TERM_GRACE_SECONDS,
        kill_grace: float = KILL_GRACE_SECONDS,
    ) -> None:
        if deadline_seconds <= 0:
            raise ValueError("conversion deadline must be positive")
        self.staging_root = staging_root
        self.deadline_seconds = deadline_seconds
        self.clock = clock
        self.python = python
        self.child_args = child_args
        self.load_document = load_document or _load_docling_document
        self.term_grace, self.kill_grace = term_grace, kill_grace

    def _prepare_root(self) -> None:
        self.staging_root.mkdir(mode=0o700, parents=False, exist_ok=True)
        info = os.lstat(self.staging_root)
        if not os.path.isdir(self.staging_root) or os.path.islink(self.staging_root):
            raise ConversionError("conversion_staging_invalid")
        if info.st_uid != os.getuid() or info.st_mode & 0o077:
            raise ConversionError("conversion_staging_invalid")

    def receipt_path(self, attempt_id: str) -> Path:
        return self.staging_root / f"{attempt_id}.launch.json"

    def convert(
        self,
        source_bytes: bytes,
        *,
        attempt_id: str,
        capture_provenance: bool,
        cancelled: Event | None = None,
    ) -> ConversionHandoff:
        cancelled = cancelled or Event()
        self._prepare_root()
        if not attempt_id.replace("-", "").isalnum():
            raise ConversionError("conversion_attempt_invalid")
        staging = self.staging_root / attempt_id
        nonce = os.urandom(16).hex()
        # Bound starts immediately before preparing/launching physical conversion.
        started = self.clock()
        latch = AttemptLatch(deadline=started + self.deadline_seconds, clock=self.clock)
        staging.mkdir(mode=0o700)
        (staging / "source.pdf").write_bytes(source_bytes)
        source_sha256 = hashlib.sha256(source_bytes).hexdigest()
        control_read, control_write = os.pipe()
        frame_read, frame_write = os.pipe()
        child = None
        diagnostics: dict[str, Any] = {"deadline_seconds": self.deadline_seconds}
        try:
            child = subprocess.Popen(
                [
                    self.python,
                    "-m",
                    "brain_ingestion.conversion_process",
                    "--child",
                    "--control-fd",
                    str(control_read),
                    "--frame-fd",
                    str(frame_write),
                    "--source",
                    str(staging / "source.pdf"),
                    "--staging",
                    str(staging),
                    "--nonce",
                    nonce,
                    *(["--provenance"] if capture_provenance else []),
                    *self.child_args,
                ],
                pass_fds=(control_read, frame_write),
                close_fds=True,
                start_new_session=True,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                env=_child_environment(),
                cwd=staging,
            )
        finally:
            os.close(control_read)
            os.close(frame_write)
        try:
            start_ticks = process_start_ticks(child.pid)
            _atomic_write(
                self.receipt_path(attempt_id),
                json.dumps(
                    {
                        "attempt_id": attempt_id,
                        "nonce_sha256": hashlib.sha256(nonce.encode()).hexdigest(),
                        "staging": str(staging),
                        "pid": child.pid,
                        "pgid": child.pid,
                        "start_ticks": start_ticks,
                        "boot_id": boot_id(),
                    },
                    sort_keys=True,
                ).encode(),
            )
            os.write(control_write, f"start {nonce}\n".encode())
        except Exception:
            os.close(control_write)
            os.close(frame_read)
            self._cleanup(child, staging, attempt_id, diagnostics)
            raise
        os.close(control_write)

        watchdog_stop = Event()

        def watchdog() -> None:
            # Independent of converter, IPC and staging I/O; never holds the latch
            # while waiting on anything else.
            while not watchdog_stop.is_set() and latch.outcome is None:
                if self.clock() >= latch.deadline:
                    latch.decide("conversion_timeout")
                    break
                if cancelled.is_set():
                    latch.decide("cancelled")
                    break
                watchdog_stop.wait(0.01)

        thread = threading.Thread(target=watchdog, name="conversion-deadline", daemon=True)
        thread.start()
        frame_bytes = b""
        failure: str | None = None
        handoff: ConversionHandoff | None = None
        try:
            while latch.outcome is None:
                ready, _, _ = select.select([frame_read], [], [], 0.05)
                if not ready:
                    continue
                chunk = os.read(frame_read, 65536)
                if not chunk:
                    break
                frame_bytes += chunk
                if len(frame_bytes) > MAX_FRAME_BYTES:
                    failure = "conversion_failed"
                    break
            # Require a successful child exit as well as a complete frame.
            while latch.outcome is None and failure is None and child.poll() is None:
                time.sleep(0.01)
            if latch.outcome is None and failure is None:
                failure, parsed = self._validate(
                    frame_bytes, child.returncode, nonce, source_sha256, staging
                )
                if failure is None and parsed is not None and latch.accept():
                    handoff = ConversionHandoff(parsed, diagnostics)
            if failure is not None:
                latch.decide("conversion_failed")
        finally:
            watchdog_stop.set()
            thread.join(timeout=1)
            os.close(frame_read)
        diagnostics["decision"] = latch.outcome
        diagnostics["decision_seconds"] = (latch.decided_at or self.clock()) - started
        cleanup_started = time.monotonic()
        self._cleanup(child, staging, attempt_id, diagnostics)
        diagnostics["cleanup_seconds"] = time.monotonic() - cleanup_started
        if latch.outcome == "accepted" and handoff is not None:
            return handoff
        if latch.outcome == "cancelled":
            raise ConversionError("cancelled", diagnostics)
        if latch.outcome == "conversion_timeout":
            raise ConversionError("conversion_timeout", diagnostics)
        raise ConversionError(failure or "conversion_failed", diagnostics)

    def _validate(
        self,
        frame_bytes: bytes,
        returncode: int | None,
        nonce: str,
        source_sha256: str,
        staging: Path,
    ) -> tuple[str | None, ParseResult[Any] | None]:
        try:
            frame = json.loads(frame_bytes.split(b"\n", 1)[0])
        except (ValueError, IndexError):
            return "conversion_failed", None
        if not isinstance(frame, dict):
            return "conversion_failed", None
        if frame.get("type") == "error" and frame.get("code") == "stage_guard_mismatch":
            return "stage_guard_mismatch", None
        if (
            returncode != 0
            or frame.get("type") != "complete"
            or frame.get("nonce") != nonce
            or frame.get("source_sha256") != source_sha256
            or frame.get("guard") != _stage_guard()
            or not isinstance(frame.get("files"), dict)
            or set(frame["files"]) != set(_FILES)
        ):
            return "conversion_failed", None
        out = staging / "out"
        try:
            # Declared relative files only; no symlinks or extra entries.
            if sorted(entry.name for entry in out.iterdir()) != sorted(_FILES):
                return "conversion_failed", None
            for name in _FILES:
                path = out / name
                if path.is_symlink() or _sha256_file(path) != frame["files"][name]:
                    return "conversion_failed", None
            document = self.load_document((out / "docling-document.json").read_bytes())
            parsed = decode_parse(document, json.loads((out / "parse.json").read_bytes()))
        except (OSError, ValueError, KeyError, TypeError):
            return "conversion_failed", None
        if parsed.status != frame.get("status"):
            return "conversion_failed", None
        return None, parsed

    def _cleanup(
        self,
        child: subprocess.Popen[bytes] | None,
        staging: Path,
        attempt_id: str,
        diagnostics: dict[str, Any],
    ) -> None:
        if child is not None:
            gone = terminate_group(
                child.pid,
                term_grace=0
                if child.poll() is not None and not group_members(child.pid)
                else self.term_grace,
                kill_grace=self.kill_grace,
                reap=child.poll,
            )
            diagnostics["group_confirmed_gone"] = gone
            if not gone:
                # Keep guard and private staging for explicit DevOps recovery.
                raise ConverterCleanupFailed("converter_cleanup_unconfirmed", diagnostics)
        shutil.rmtree(staging, ignore_errors=False) if staging.exists() else None
        self.receipt_path(attempt_id).unlink(missing_ok=True)

    def reap_orphans(self) -> list[str]:
        """Under the host guard, before claims: end recorded children, remove staging."""
        if not self.staging_root.exists():
            return []
        self._prepare_root()
        reaped = []
        for receipt in sorted(self.staging_root.glob("*.launch.json")):
            data = json.loads(receipt.read_bytes())
            pid, ticks = int(data["pid"]), data["start_ticks"]
            # A receipt from an earlier boot cannot name a live child: its PID may
            # now be anyone's, so only the staging is removed (Code Review L3).
            current_boot = boot_id()
            # Only a known, different boot proves staleness; unknown is not proof
            # (delta review D-3: never skip a possibly live converter).
            stale_boot = None not in (data.get("boot_id"), current_boot) and (
                data.get("boot_id") != current_boot
            )
            live = None if stale_boot else process_start_ticks(pid)
            if live is not None and live != ticks:
                # PID reused by an unrelated process: never kill it.
                raise ConverterCleanupFailed("converter_ownership_unconfirmed")
            # A group id is not reused while any member lives, so remaining members
            # are this attempt's converter/helpers even after the leader exited.
            if (
                not stale_boot
                and group_members(pid)
                and not terminate_group(pid, term_grace=self.term_grace, kill_grace=self.kill_grace)
            ):
                raise ConverterCleanupFailed("converter_cleanup_unconfirmed")
            staging = Path(data["staging"])
            if staging.parent != self.staging_root:
                raise ConverterCleanupFailed("conversion_staging_invalid")
            shutil.rmtree(staging, ignore_errors=True)
            receipt.unlink()
            reaped.append(str(data["attempt_id"]))
        # Staging without a receipt was never acknowledged, so never converted.
        for entry in self.staging_root.iterdir():
            if entry.is_dir() and not (self.staging_root / f"{entry.name}.launch.json").exists():
                shutil.rmtree(entry, ignore_errors=True)
        return reaped


def _stage_guard() -> dict[str, str]:
    """The pinned stage-layout guard both sides of the handoff must agree on.

    Derived from the one recorded Docling-Graph pin, not repeated as a literal
    (Architect G3). `pins` has no dependencies, so the child never loads Graph.
    """
    from brain_extraction.pins import DOCLING_GRAPH_VERSION

    return {"stage_layout": "pinned", "docling_graph": DOCLING_GRAPH_VERSION}


def boot_id() -> str | None:
    try:
        return Path("/proc/sys/kernel/random/boot_id").read_text().strip()
    except OSError:
        return None


def _load_docling_document(raw: bytes) -> Any:
    from docling_core.types.doc import DoclingDocument

    return DoclingDocument.model_validate_json(raw)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--child", action="store_true", required=True)
    parser.add_argument("--control-fd", type=int, required=True)
    parser.add_argument("--frame-fd", type=int, required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--staging", required=True)
    parser.add_argument("--nonce", required=True)
    parser.add_argument("--provenance", action="store_true")
    parser.add_argument("--converter", choices=("docling", "fixture"), default="docling")
    parser.add_argument("--fixture-behavior", default="complete")
    parser.add_argument("--fixture-delay", type=float, default=0.0)
    return _child(parser.parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
