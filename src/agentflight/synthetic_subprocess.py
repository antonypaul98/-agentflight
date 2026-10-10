"""One fixed-workload subprocess adapter for disposable synthetic crash tests.

This is NOT an OS sandbox and never runs fixture-supplied code or commands.
"""

import hashlib
import json
import math
import os
from pathlib import Path
import re
import selectors
import signal
import subprocess
import sys
import tempfile
import time

MAX_TIMEOUT_SECONDS = 2.0
DEFAULT_TIMEOUT_SECONDS = 1.5
MAX_OUTPUT_BYTES = 1024
_IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}\Z")
_MODES = frozenset({"pass", "fail", "timeout", "stdout_overflow", "stderr_overflow", "combined_boundary", "combined_overflow", "secret", "burst_overflow", "timeout_secret", "orphan_pipe", "orphan_closed_pipes"})

# Static worker, not a template. Untrusted values are never interpolated into code.
_WORKER = """import os, subprocess, sys, time
mode = sys.argv[1]
if mode == 'pass':
    print('synthetic-ok')
elif mode == 'fail':
    sys.stderr.write('synthetic-error\\n')
    sys.exit(7)
elif mode == 'timeout':
    time.sleep(1.0)
elif mode == 'stdout_overflow':
    sys.stdout.write('x' * 4096)
elif mode == 'stderr_overflow':
    sys.stderr.write('y' * 4096)
elif mode == 'combined_boundary':
    sys.stdout.write('x' * 512)
    sys.stderr.write('y' * 512)
elif mode == 'combined_overflow':
    sys.stdout.write('x' * 512)
    sys.stderr.write('y' * 513)
elif mode == 'secret':
    print('SYNTHETIC_PRIVATE_TOKEN_931')
elif mode == 'burst_overflow':
    os.write(1, b'x' * 65536)
elif mode == 'timeout_secret':
    print('SYNTHETIC_PRIVATE_TOKEN_931', flush=True)
    time.sleep(1.0)
elif mode == 'orphan_pipe':
    # A fixed child inherits both pipes after its short-lived parent exits.
    subprocess.Popen([sys.executable, '-I', '-S', '-c', 'import time; time.sleep(1.0)'])
elif mode == 'orphan_closed_pipes':
    # Descendant stays in the process group but does not hold output pipes.
    subprocess.Popen([sys.executable, '-I', '-S', '-c', 'import time; time.sleep(1.0)'],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
"""


class SyntheticCaseError(ValueError):
    """Invalid synthetic-case input, not a subprocess test failure."""


def _kill_process_group(process):
    """Reap the fixed worker and any same-session descendants on POSIX."""
    if os.name == "posix":
        # EINTR does not establish whether the signal reached the group.
        # Retry a bounded number of times before falling back to the parent.
        for _ in range(3):
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except InterruptedError:
                continue
            except ProcessLookupError:
                # An absent group does not prove the worker exited. Avoid an
                # unbounded wait if the worker is still alive.
                if process.poll() is None:
                    process.kill()
                break
            except OSError:
                if process.poll() is None:
                    process.kill()
                break
            else:
                break
        else:
            if process.poll() is None:
                process.kill()
    elif process.poll() is None:
        process.kill()
    process.wait()


def _capture_bounded(process, timeout_seconds):
    """Read at most MAX_OUTPUT_BYTES+1 bytes TOTAL; never buffer worker text."""
    counts = [0, 0]
    deadline = time.monotonic() + timeout_seconds
    with selectors.DefaultSelector() as selector:
        for index, stream in enumerate((process.stdout, process.stderr)):
            os.set_blocking(stream.fileno(), False)
            selector.register(stream, selectors.EVENT_READ, index)
        while selector.get_map():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return "timeout", (0, 0)
            try:
                ready = selector.select(remaining)
            except InterruptedError:
                # EINTR is recoverable; the monotonic deadline is unchanged.
                continue
            for key, _ in ready:
                # +1 makes an overflow observable without retaining its content.
                allowance = MAX_OUTPUT_BYTES + 1 - sum(counts)
                try:
                    data = os.read(key.fileobj.fileno(), allowance)
                except (InterruptedError, BlockingIOError):
                    # EINTR or a spurious EAGAIN on a nonblocking pipe is
                    # recoverable; keep the original monotonic deadline.
                    continue
                if not data:
                    selector.unregister(key.fileobj)
                else:
                    counts[key.data] += len(data)
                    if sum(counts) > MAX_OUTPUT_BYTES:
                        return "output_limit", tuple(counts)
        remaining = deadline - time.monotonic()
        if remaining <= 0 and process.poll() is None:
            return "timeout", (0, 0)
        try:
            process.wait(timeout=max(0.001, remaining))
        except subprocess.TimeoutExpired:
            return "timeout", (0, 0)
    return "completed", tuple(counts)


def run_synthetic_case(case_id: str, mode: str, *, timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS) -> dict:
    """Run a fixed Python worker with bounded pipe capture and redacted verdicts.

    POSIX only: a new session allows timeout/output-limit cleanup of the worker
    process group. This is not a security sandbox or an arbitrary-code runner.
    """
    if type(case_id) is not str or not _IDENTIFIER.fullmatch(case_id):
        raise SyntheticCaseError("invalid_case_id")
    if type(mode) is not str or mode not in _MODES:
        raise SyntheticCaseError("invalid_mode")
    if (type(timeout_seconds) not in (int, float) or not math.isfinite(timeout_seconds)
            or not 0.05 <= timeout_seconds <= MAX_TIMEOUT_SECONDS):
        raise SyntheticCaseError("invalid_timeout")

    status, code = "error", "launch_error"
    stdout_bytes = stderr_bytes = 0
    process = None
    try:
        if os.name != "posix":
            raise OSError("POSIX subprocess isolation required")
        with tempfile.TemporaryDirectory(prefix="agentflight-synthetic-") as directory:
            # Fixed executable and script; no shell, inherited environment,
            # fixture commands, user cwd or project paths.
            process = subprocess.Popen(
                [sys.executable, "-I", "-S", "-c", _WORKER, mode],
                cwd=Path(directory), env={}, stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                start_new_session=True,
            )
            try:
                outcome, (stdout_bytes, stderr_bytes) = _capture_bounded(process, timeout_seconds)
                if outcome == "timeout":
                    status, code = "timeout", "timeout"
                elif outcome == "output_limit":
                    status, code = "failed", "output_limit"
                elif process.returncode:
                    status, code = "failed", "nonzero_exit"
                else:
                    status, code = "passed", "ok"
            finally:
                # A completed parent can leave live descendants with closed pipes.
                # Always terminate its isolated group, including after success.
                try:
                    _kill_process_group(process)
                finally:
                    try:
                        process.stdout.close()
                    finally:
                        process.stderr.close()
    except (OSError, subprocess.SubprocessError, ValueError):
        # Selector/pipe setup can raise ValueError for invalid descriptors.
        # Paths, interpreter errors and subprocess output may contain secrets.
        status, code = "error", "launch_error"
        stdout_bytes = stderr_bytes = 0

    if status == "timeout":
        stdout_bytes = stderr_bytes = 0
    scoped = {"schema_version": 1, "case_id": case_id, "mode": mode,
              "status": status, "code": code}
    evidence_id = hashlib.sha256(json.dumps(scoped, sort_keys=True,
                                            separators=(",", ":")).encode("utf-8")).hexdigest()
    return {"schema_version": 1, "case_id": case_id, "status": status,
            "code": code, "evidence_id": evidence_id,
            "stdout_bytes": min(stdout_bytes, MAX_OUTPUT_BYTES + 1),
            "stderr_bytes": min(stderr_bytes, MAX_OUTPUT_BYTES + 1)}
