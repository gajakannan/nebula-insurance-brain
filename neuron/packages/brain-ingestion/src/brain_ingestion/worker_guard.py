"""Host singleton for the dedicated local inference provider (F0005 Step 0a).

A local one-worker deployment control, not a distributed quota. Every processing
process on this host, whatever its checkout, content root, profile, tenant or
temporary configuration, contends for the same advisory lock inode in a fixed
directory derived from the host account UID. The lock key is the canonical
provider endpoint, never the credential, model, tenant or a raw alias string.

Releasing an OS lock does not cancel GPU work. A durable in-flight marker is
written before each provider request and cleared only after a terminal response.
A dirty marker blocks every replacement until a supervisor confirms the provider
process group exited, restarts the pinned server and records a receipt.
"""

from __future__ import annotations

import contextlib
import errno
import fcntl
import hashlib
import ipaddress
import json
import os
import socket
import stat
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager, suppress
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

CONTROL_PARENT = Path("/tmp")
_DEFAULT_PORTS = {"http": 80, "https": 443}


class GuardError(RuntimeError):
    """Stable startup/refusal code; never contains credentials or prompts."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class EndpointIdentity:
    scheme: str
    address: str
    port: int
    base_path: str

    @property
    def canonical(self) -> str:
        host = f"[{self.address}]" if ":" in self.address else self.address
        return f"{self.scheme}://{host}:{self.port}{self.base_path}"

    @property
    def key(self) -> str:
        return hashlib.sha256(self.canonical.encode()).hexdigest()


def canonical_endpoint(
    base_url: str,
    *,
    resolve: Callable[[str], set[str]] | None = None,
) -> EndpointIdentity:
    """Resolve a configured URL to the one numeric loopback service it names.

    Only the dedicated local Brain provider is supported: a non-loopback origin,
    credentials in the URL, or a name resolving to several addresses is refused.
    """
    parts = urlsplit(base_url)
    if parts.scheme not in _DEFAULT_PORTS or not parts.hostname:
        raise GuardError("inference_endpoint_invalid")
    if parts.username or parts.password or parts.query or parts.fragment:
        raise GuardError("inference_endpoint_invalid")
    try:
        port = parts.port or _DEFAULT_PORTS[parts.scheme]
    except ValueError:
        raise GuardError("inference_endpoint_invalid") from None
    addresses = (resolve or _resolve)(parts.hostname)
    if len(addresses) != 1:
        raise GuardError("inference_endpoint_ambiguous")
    address = ipaddress.ip_address(next(iter(addresses)))
    if not address.is_loopback:
        raise GuardError("inference_endpoint_not_allowlisted")
    segments = [segment for segment in parts.path.split("/") if segment]
    if any(segment in (".", "..") for segment in segments):
        raise GuardError("inference_endpoint_invalid")
    return EndpointIdentity(parts.scheme, str(address), port, "/" + "/".join(segments))


def _resolve(hostname: str) -> set[str]:
    try:
        return {
            str(info[4][0]) for info in socket.getaddrinfo(hostname, None, type=socket.SOCK_STREAM)
        }
    except OSError:
        raise GuardError("inference_endpoint_unresolvable") from None


def control_directory(uid: int | None = None) -> Path:
    """Fixed per-host-account directory; no environment or config override exists."""
    return CONTROL_PARENT / f"nebula-brain-inference-{os.getuid() if uid is None else uid}"


def _fsync_directory(path: Path) -> None:
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _atomic_write(path: Path, payload: bytes) -> None:
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    fd = os.open(
        temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600
    )
    try:
        try:
            os.write(fd, payload)
            os.fsync(fd)
        finally:
            os.close(fd)
        os.replace(temporary, path)
    except BaseException:
        # A leftover temporary would make every later O_EXCL open in this process
        # fail after the disk recovers (F0005 M3).
        with contextlib.suppress(FileNotFoundError):
            os.unlink(temporary)
        raise
    _fsync_directory(path.parent)


def process_start_ticks(pid: int) -> int | None:
    """Kernel start time of `pid` (clock ticks since boot), to defeat PID reuse."""
    # The command name may contain spaces/parentheses; fields resume after the last ')'.
    fields = _stat_fields(pid)
    return None if fields is None or fields[0] == "Z" else int(fields[19])


def _stat_fields(pid: int) -> list[str] | None:
    try:
        raw = Path(f"/proc/{pid}/stat").read_text()
    except (FileNotFoundError, ProcessLookupError, PermissionError):
        return None
    return raw[raw.rindex(")") + 2 :].split()


def group_members(pgid: int) -> list[int]:
    """Live (non-zombie) processes in a process group, including escaped helpers."""
    members = []
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        fields = _stat_fields(int(entry.name))
        if fields is not None and fields[0] != "Z" and int(fields[2]) == pgid:
            members.append(int(entry.name))
    return members


def terminate_group(
    pgid: int, *, term_grace: float, kill_grace: float, reap: Callable[[], object] | None = None
) -> bool:
    """SIGTERM the whole group, then SIGKILL; True only when no member remains."""
    import signal

    for sig, grace in ((signal.SIGTERM, term_grace), (signal.SIGKILL, kill_grace)):
        with suppress(ProcessLookupError):
            os.killpg(pgid, sig)
        deadline = time.monotonic() + grace
        while True:
            if reap is not None:
                reap()
            if not group_members(pgid):
                return True
            if time.monotonic() >= deadline:
                break
            time.sleep(0.02)
    return not group_members(pgid)


class DispatchHandle:
    def __init__(self) -> None:
        self.confirmed = False

    def confirm(self) -> None:
        """The provider returned a terminal response: the request is finished."""
        self.confirmed = True


class HostInferenceGuard:
    """Hold for the whole processing-worker lifetime; acquire before any claim."""

    def __init__(
        self,
        provider_url: str,
        *,
        directory: Path | None = None,
        resolve: Callable[[str], set[str]] | None = None,
    ) -> None:
        self.identity = canonical_endpoint(provider_url, resolve=resolve)
        self.directory = directory or control_directory()
        self._fd: int | None = None
        self.uncertain = False

    @property
    def lock_path(self) -> Path:
        return self.directory / f"{self.identity.key}.lock"

    @property
    def marker_path(self) -> Path:
        return self.directory / f"{self.identity.key}.inflight.json"

    @property
    def provider_path(self) -> Path:
        return self.directory / f"{self.identity.key}.provider.json"

    @property
    def receipts_path(self) -> Path:
        return self.directory / f"{self.identity.key}.receipts"

    @property
    def staging_root(self) -> Path:
        return self.directory / "conversion"

    @property
    def held(self) -> bool:
        return self._fd is not None

    def _prepare_directory(self) -> None:
        uid = os.getuid()
        try:
            info = os.lstat(self.directory)
        except FileNotFoundError:
            with suppress(FileExistsError):
                os.mkdir(self.directory, 0o700)
            info = os.lstat(self.directory)
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
            raise GuardError("inference_guard_directory_invalid")
        if info.st_uid != uid or stat.S_IMODE(info.st_mode) != 0o700:
            raise GuardError("inference_guard_directory_invalid")

    def acquire(self) -> None:
        """Take the host lock, then refuse to start while provider work is uncertain."""
        if self._fd is not None:
            raise GuardError("inference_guard_already_held")
        self._prepare_directory()
        try:
            fd = os.open(
                self.lock_path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600
            )
        except OSError:
            raise GuardError("inference_guard_directory_invalid") from None
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid():
            os.close(fd)
            raise GuardError("inference_guard_directory_invalid")
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            os.close(fd)
            if exc.errno in (errno.EWOULDBLOCK, errno.EAGAIN):
                raise GuardError("inference_guard_busy") from None
            raise GuardError("inference_guard_lock_unsupported") from None
        # The descriptor is never inherited: helpers are spawned with close_fds.
        os.set_inheritable(fd, False)
        self._fd = fd
        # Owner metadata is informational; PID presence never overrides the lock.
        _atomic_write(
            self.directory / f"{self.identity.key}.owner.json",
            json.dumps(
                {"pid": os.getpid(), "start_ticks": process_start_ticks(os.getpid())}
            ).encode(),
        )

    def require_quiescent(self) -> None:
        if self.marker_path.exists():
            raise GuardError("provider_quiescence_required")

    def release(self) -> None:
        if self._fd is not None:
            # Closing releases the OS lock. The lock inode is never unlinked.
            os.close(self._fd)
            self._fd = None

    def __enter__(self) -> HostInferenceGuard:
        self.acquire()
        return self

    def __exit__(self, *_exc: object) -> None:
        self.release()

    def provider_fingerprint(self) -> str:
        try:
            return hashlib.sha256(self.provider_path.read_bytes()).hexdigest()
        except FileNotFoundError:
            return "unrecorded"

    @contextmanager
    def inflight(self, correlation: str) -> Iterator[DispatchHandle]:
        """Durably mark one provider request; leave it dirty unless confirmed finished."""
        if self._fd is None:
            raise GuardError("inference_guard_not_held")
        if self.uncertain or self.marker_path.exists():
            # A leftover marker is uncertain work too: stop this worker rather than
            # refuse one job after another (Code Review L-N3).
            self.uncertain = True
            raise GuardError("provider_quiescence_required")
        marker = {
            "correlation_sha256": hashlib.sha256(correlation.encode()).hexdigest(),
            "provider_fingerprint": self.provider_fingerprint(),
            "pid": os.getpid(),
            "started_at": time.time(),
        }
        try:
            _atomic_write(self.marker_path, json.dumps(marker, sort_keys=True).encode())
        except OSError:
            # Durability failed: send nothing. Remove any non-durable remnant only
            # if no request can have been dispatched against it (none was).
            raise GuardError("inflight_marker_not_durable") from None
        handle = DispatchHandle()
        try:
            yield handle
        finally:
            if handle.confirmed:
                try:
                    self.marker_path.unlink()
                    _fsync_directory(self.directory)
                except OSError:
                    # The marker may survive: treat it as uncertain and stop.
                    self.uncertain = True
            else:
                # Timeout, disconnect, cancellation or crash: outcome uncertain.
                self.uncertain = True

    def clear_after_quiescence(self, receipt: dict[str, Any]) -> Path:
        """Record a durable receipt, then clear the marker, while holding the guard."""
        if self._fd is None:
            raise GuardError("inference_guard_not_held")
        for field in ("old_provider", "new_provider", "confirmed_exit", "pins"):
            if field not in receipt:
                raise GuardError("quiescence_receipt_incomplete")
        if receipt["confirmed_exit"] is not True:
            raise GuardError("quiescence_receipt_incomplete")
        self.receipts_path.mkdir(mode=0o700, exist_ok=True)
        path = self.receipts_path / f"{time.time_ns()}.json"
        _atomic_write(path, json.dumps(receipt, sort_keys=True).encode())
        if self.marker_path.exists():
            self.marker_path.unlink()
            _fsync_directory(self.directory)
        self.uncertain = False
        return path


@dataclass(frozen=True, slots=True)
class ProviderRecord:
    """Preflight-recorded identity of the dedicated serving process group."""

    pid: int
    pgid: int
    start_ticks: int
    argv: list[str]
    cwd: str
    endpoint: str

    @classmethod
    def capture(cls, pid: int, endpoint: EndpointIdentity) -> ProviderRecord:
        start = process_start_ticks(pid)
        if start is None:
            raise GuardError("provider_process_missing")
        record = cls(
            pid=pid,
            pgid=os.getpgid(pid),
            start_ticks=start,
            argv=_cmdline(pid),
            cwd=os.readlink(f"/proc/{pid}/cwd"),
            endpoint=endpoint.canonical,
        )
        record.validate(endpoint)
        if not record.owns_listener(endpoint):
            # The guarded port must be served by this group, not another process.
            raise GuardError("provider_record_invalid")
        return record

    def validate(self, endpoint: EndpointIdentity) -> None:
        """Only a `vllm serve` group leader bound to this endpoint may be recorded.

        The record is a restart command and a kill target, so a tampered or
        mistaken record must never name another program, group or listener
        (Security SEC-F5-L1). The credential never appears in the argv.
        """
        argv = self.argv

        def option(name: str) -> str | None:
            return argv[argv.index(name) + 1] if name in argv[:-1] else None

        program = _serving_program(argv)
        if (
            self.endpoint != endpoint.canonical
            or self.pid != self.pgid
            or program is None
            or "serve" not in argv
            or option("--host") != endpoint.address
            or option("--port") != str(endpoint.port)
            or any(part == "--api-key" or part.startswith("--api-key=") for part in argv)
        ):
            raise GuardError("provider_record_invalid")

    def is_live(self) -> bool:
        """The recorded leader is running unchanged: same start, group and argv."""
        return (
            process_start_ticks(self.pid) == self.start_ticks
            and _pgid(self.pid) == self.pgid
            and _cmdline(self.pid) == self.argv
        )

    def owns_listener(self, endpoint: EndpointIdentity) -> bool:
        """The guarded host:port listening socket belongs to this process group."""
        inodes = _listening_inodes(endpoint.address, endpoint.port)
        return bool(inodes) and any(
            _socket_inodes(member) & inodes for member in group_members(self.pgid)
        )

    def to_json(self) -> bytes:
        return json.dumps(asdict(self), sort_keys=True).encode()


def _serving_program(argv: list[str]) -> str | None:
    """The vLLM entry point itself, not merely an argument named `vllm`.

    Either the `vllm` console script is argv[0], or argv[0] is the Python of the
    same virtual environment whose `bin/vllm` is argv[1] (SEC-F5-L4).
    """
    if argv and Path(argv[0]).name == "vllm":
        return argv[0]
    if (
        len(argv) > 1
        and Path(argv[1]).name == "vllm"
        and Path(argv[0]).name.startswith("python")
        and Path(argv[0]).parent == Path(argv[1]).parent
    ):
        return argv[1]
    return None


def _listening_inodes(address: str, port: int) -> set[str]:
    """Socket inodes listening on `address:port` (IPv4 or IPv6 loopback)."""
    import ipaddress as _ip

    wanted = _ip.ip_address(address)
    inodes: set[str] = set()
    for table in ("/proc/net/tcp", "/proc/net/tcp6"):
        try:
            lines = Path(table).read_text().splitlines()[1:]
        except OSError:
            continue
        for line in lines:
            fields = line.split()
            local, state, inode = fields[1], fields[3], fields[9]
            if state != "0A":  # LISTEN
                continue
            hex_address, hex_port = local.split(":")
            if int(hex_port, 16) != port:
                continue
            raw = bytes.fromhex(hex_address)
            # /proc stores each 32-bit word in host (little-endian) order.
            raw = b"".join(raw[i : i + 4][::-1] for i in range(0, len(raw), 4))
            if _ip.ip_address(raw) == wanted:
                inodes.add(inode)
    return inodes


def _socket_inodes(pid: int) -> set[str]:
    found: set[str] = set()
    try:
        entries = list(Path(f"/proc/{pid}/fd").iterdir())
    except OSError:
        return found
    for entry in entries:
        try:
            target = os.readlink(entry)
        except OSError:
            continue
        if target.startswith("socket:["):
            found.add(target[8:-1])
    return found


def _cmdline(pid: int) -> list[str]:
    try:
        raw = Path(f"/proc/{pid}/cmdline").read_bytes()
    except OSError:
        return []
    return [part.decode() for part in raw.rstrip(b"\0").split(b"\0")]


def _pgid(pid: int) -> int | None:
    try:
        return os.getpgid(pid)
    except ProcessLookupError:
        return None


def record_provider(guard: HostInferenceGuard, record: ProviderRecord) -> None:
    guard._prepare_directory()
    if record.endpoint != guard.identity.canonical:
        raise GuardError("inference_endpoint_not_allowlisted")
    record.validate(guard.identity)
    _atomic_write(guard.provider_path, record.to_json())


def load_provider(guard: HostInferenceGuard) -> ProviderRecord:
    try:
        data = json.loads(guard.provider_path.read_bytes())
    except FileNotFoundError:
        raise GuardError("provider_unrecorded") from None
    record = ProviderRecord(**data)
    if record.endpoint != guard.identity.canonical:
        raise GuardError("inference_endpoint_not_allowlisted")
    # Re-checked at use: the file is a restart command and a kill target.
    record.validate(guard.identity)
    return record
