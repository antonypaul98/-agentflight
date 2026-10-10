"""AF-22: parent exit between poll and fallback kill is not a launch error."""

import os
import signal

import pytest

import agentflight.synthetic_subprocess as adapter


class RacingParent:
    pid = 56789

    def __init__(self):
        self.events = []

    def poll(self):
        self.events.append("poll")
        return None  # Worker exited immediately after this observation.

    def kill(self):
        self.events.append("kill")
        raise ProcessLookupError("worker already exited")

    def wait(self):
        self.events.append("wait")
        return 0


@pytest.mark.skipif(os.name != "posix", reason="POSIX process groups only")
def test_missing_group_parent_exit_race_is_reaped(monkeypatch):
    parent = RacingParent()

    def missing_group(pid, sig):
        assert (pid, sig) == (parent.pid, signal.SIGKILL)
        parent.events.append("group")
        raise ProcessLookupError("group already exited")

    monkeypatch.setattr(adapter.os, "killpg", missing_group)
    adapter._kill_process_group(parent)
    assert parent.events == ["group", "poll", "kill", "wait"]


@pytest.mark.skipif(os.name != "posix", reason="POSIX process groups only")
def test_persistent_group_eintr_parent_exit_race_is_reaped(monkeypatch):
    parent = RacingParent()

    def interrupted_group(pid, sig):
        assert (pid, sig) == (parent.pid, signal.SIGKILL)
        parent.events.append("group")
        raise InterruptedError()

    monkeypatch.setattr(adapter.os, "killpg", interrupted_group)
    adapter._kill_process_group(parent)
    assert parent.events == ["group", "group", "group", "poll", "kill", "wait"]
