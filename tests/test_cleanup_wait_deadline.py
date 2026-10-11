"""AF-22: post-signal worker reaping has a deterministic deadline."""

import os
import signal
import subprocess

import pytest

import agentflight.synthetic_subprocess as adapter


pytestmark = pytest.mark.skipif(os.name != "posix", reason="POSIX process groups only")


def test_cleanup_wait_timeout_is_bounded(monkeypatch):
    timeouts = []

    class Process:
        pid = 12401

        def wait(self, *, timeout):
            timeouts.append(timeout)
            raise subprocess.TimeoutExpired("fixed-worker", timeout)

    monkeypatch.setattr(adapter.os, "killpg", lambda pid, sig: (
        pid == 12401 and sig == signal.SIGKILL
    ))

    with pytest.raises(subprocess.TimeoutExpired):
        adapter._kill_process_group(Process())

    assert len(timeouts) == 1
    assert 0 < timeouts[0] <= adapter.MAX_TIMEOUT_SECONDS


def test_cleanup_wait_interruptions_share_original_deadline(monkeypatch):
    timeouts = []

    class Process:
        pid = 12402

        def wait(self, *, timeout):
            timeouts.append(timeout)
            if len(timeouts) == 1:
                raise InterruptedError("synthetic interruption")
            return -signal.SIGKILL

    monkeypatch.setattr(adapter.os, "killpg", lambda pid, sig: (
        pid == 12402 and sig == signal.SIGKILL
    ))

    adapter._kill_process_group(Process())

    assert len(timeouts) == 2
    assert 0 < timeouts[1] <= timeouts[0] <= adapter.MAX_TIMEOUT_SECONDS
