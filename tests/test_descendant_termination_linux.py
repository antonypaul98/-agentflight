"""AF-22 Linux regressions: actual descendants stop executing after group cleanup.

A killed orphan may briefly remain a zombie until reaped by its new parent;
this verifies termination, not orphan reaping or sandbox isolation.
"""
import os
from pathlib import Path
import sys
import time

import pytest

import agentflight.synthetic_subprocess as adapter


pytestmark = pytest.mark.skipif(
    sys.platform != "linux" or not Path("/proc/self/stat").is_file(),
    reason="requires Linux /proc process-group observations",
)


def _process_identity(pid):
    """Return (group ID, state, start time), or None for a vanished PID."""
    try:
        # Split after the final ')' because the comm field may contain spaces.
        fields = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()
    except (FileNotFoundError, ProcessLookupError):
        return None
    return int(fields[2]), fields[0], fields[19]


def _live_group_descendants(group_id):
    children = {}
    for entry in Path("/proc").iterdir():
        if not entry.name.isdecimal() or int(entry.name) == group_id:
            continue
        identity = _process_identity(int(entry.name))
        if identity is not None and identity[0] == group_id and identity[1] not in {"Z", "X", "x"}:
            children[int(entry.name)] = identity[2]
    return children


def _terminated(pid, start_time):
    identity = _process_identity(pid)
    return identity is None or identity[2] != start_time or identity[1] in {"Z", "X", "x"}


@pytest.mark.parametrize("mode,code,timeout", [
    ("orphan_closed_pipes", "ok", 0.5),
    ("orphan_pipe", "timeout", 0.25),
])
def test_real_orphan_stops_after_group_cleanup(monkeypatch, mode, code, timeout):
    real_cleanup = adapter._kill_process_group
    observed = []

    def verify_cleanup(process):
        descendants = _live_group_descendants(process.pid)
        try:
            assert descendants, "fixed worker did not leave an observable live descendant"
        finally:
            # Always terminate the fixed worker, even when the assertion fails.
            real_cleanup(process)
        deadline = time.monotonic() + 0.4
        while time.monotonic() < deadline:
            if all(_terminated(pid, start) for pid, start in descendants.items()):
                break
            time.sleep(0.01)
        assert all(_terminated(pid, start) for pid, start in descendants.items())
        observed.append(True)

    monkeypatch.setattr(adapter, "_kill_process_group", verify_cleanup)
    result = adapter.run_synthetic_case("real-descendant-" + mode, mode, timeout_seconds=timeout)
    assert result["code"] == code
    assert observed == [True]
