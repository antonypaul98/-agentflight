"""One fixed-workload subprocess adapter for disposable synthetic crash tests.

This is NOT an OS sandbox and never runs fixture-supplied code or commands.
"""

import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import sys
import tempfile

MAX_TIMEOUT_SECONDS = 2.0
DEFAULT_TIMEOUT_SECONDS = 1.5
MAX_OUTPUT_BYTES = 1024
_IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}\Z")
_MODES = frozenset({"pass", "fail", "timeout", "stdout_overflow", "stderr_overflow", "combined_boundary", "combined_overflow", "secret"})

# Static worker, not a template. Untrusted values are never interpolated into code.
_WORKER = """import sys, time
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
"""


class SyntheticCaseError(ValueError):
    """Invalid synthetic-case input, not a subprocess test failure."""


def run_synthetic_case(case_id: str, mode: str, *, timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS) -> dict:
    """Run a single allowlisted Python worker in a disposable directory.

    Returns a deterministic redacted verdict, never worker output or exception
    text. The fixed worker's output is intrinsically bounded to 4096 bytes.
    The timeout is enforced by subprocess.run, which kills/reaps the child.
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
    try:
        with tempfile.TemporaryDirectory(prefix="agentflight-synthetic-") as directory:
            # A fixed executable and fixed script; no shell, user cwd, inherited
            # environment, secrets, fixture commands, or project paths.
            completed = subprocess.run(
                [sys.executable, "-I", "-S", "-c", _WORKER, mode],
                cwd=Path(directory), env={}, input=b"", capture_output=True,
                timeout=timeout_seconds, check=False,
            )
            stdout_bytes = len(completed.stdout)
            stderr_bytes = len(completed.stderr)
            if stdout_bytes + stderr_bytes > MAX_OUTPUT_BYTES:
                status, code = "failed", "output_limit"
            elif completed.returncode:
                status, code = "failed", "nonzero_exit"
            else:
                status, code = "passed", "ok"
    except subprocess.TimeoutExpired:
        status, code = "timeout", "timeout"
    except (OSError, subprocess.SubprocessError):
        # Paths, interpreter errors, and subprocess stderr may contain secrets.
        status, code = "error", "launch_error"

    scoped = {"schema_version": 1, "case_id": case_id, "mode": mode,
              "status": status, "code": code}
    evidence_id = hashlib.sha256(json.dumps(scoped, sort_keys=True,
                                            separators=(",", ":")).encode("utf-8")).hexdigest()
    return {"schema_version": 1, "case_id": case_id, "status": status,
            "code": code, "evidence_id": evidence_id,
            "stdout_bytes": min(stdout_bytes, MAX_OUTPUT_BYTES + 1),
            "stderr_bytes": min(stderr_bytes, MAX_OUTPUT_BYTES + 1)}
