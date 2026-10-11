"""AF-22: cleanup reaping remains bounded across wait interruptions."""

import os
import signal

import pytest

import agentflight.synthetic_subprocess as adapter


pytestmark = pytest.mark.skipif(os.name != "posix", reason="POSIX process groups only")


def test_cleanup_retries_transient_wait_interruption(monkeypatch):
    events = []

    class Process:
        pid = 12364

        def wait(self):
            events.append("wait")
            if events.count("wait") == 1:
                raise InterruptedError("synthetic transient reap interruption")
            return -signal.SIGKILL

    def kill_group(pid, sig):
        assert (pid, sig) == (12364, signal.SIGKILL)
        events.append("group")

    monkeypatch.setattr(adapter.os, "killpg", kill_group)
    adapter._kill_process_group(Process())
    assert events == ["group", "wait", "wait"]


def test_cleanup_persistent_wait_interruptions_are_bounded(monkeypatch):
    events = []

    class Process:
        pid = 12365

        def wait(self):
            events.append("wait")
            raise InterruptedError("SYNTHETIC_PRIVATE_TOKEN_931")

    def kill_group(pid, sig):
        assert (pid, sig) == (12365, signal.SIGKILL)
        events.append("group")

    monkeypatch.setattr(adapter.os, "killpg", kill_group)
    with pytest.raises(InterruptedError, match="reaping repeatedly interrupted"):
        adapter._kill_process_group(Process())
    assert events == ["group", "wait", "wait", "wait"]
