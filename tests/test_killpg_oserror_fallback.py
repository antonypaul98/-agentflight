"""AF-22: unexpected process-group signal errors preserve bounded parent cleanup."""

import os
import signal

import pytest

import agentflight.synthetic_subprocess as adapter


@pytest.mark.skipif(os.name != "posix", reason="POSIX process groups only")
def test_group_oserror_fallback_kills_live_parent_before_wait(monkeypatch):
    calls = []

    class LiveParent:
        pid = 12349
        killed = False

        def poll(self):
            calls.append("poll")
            return None if not self.killed else -signal.SIGKILL

        def kill(self):
            calls.append("kill-parent")
            self.killed = True

        def wait(self):
            assert self.killed, "cannot wait indefinitely for a live worker"
            calls.append("wait")

    def group_failure(pid, sig):
        assert (pid, sig) == (12349, signal.SIGKILL)
        calls.append("group")
        raise PermissionError("synthetic group permission failure")

    monkeypatch.setattr(adapter.os, "killpg", group_failure)
    adapter._kill_process_group(LiveParent())
    assert calls == ["group", "poll", "kill-parent", "wait"]


@pytest.mark.skipif(os.name != "posix", reason="POSIX process groups only")
def test_group_oserror_fallback_does_not_kill_exited_parent(monkeypatch):
    calls = []

    class ExitedParent:
        pid = 12350

        def poll(self):
            calls.append("poll")
            return 0

        def kill(self):
            pytest.fail("exited worker must not receive fallback kill")

        def wait(self):
            calls.append("wait")

    def group_failure(pid, sig):
        assert (pid, sig) == (12350, signal.SIGKILL)
        calls.append("group")
        raise PermissionError("synthetic group permission failure")

    monkeypatch.setattr(adapter.os, "killpg", group_failure)
    adapter._kill_process_group(ExitedParent())
    assert calls == ["group", "poll", "wait"]
