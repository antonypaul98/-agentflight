"""AF-22 bounded process-group signal interruption regressions."""

import os
import signal

import pytest

import agentflight.synthetic_subprocess as adapter


@pytest.mark.skipif(os.name != "posix", reason="POSIX process groups only")
def test_interrupted_group_kill_retries_for_exited_parent(monkeypatch):
    """A transient EINTR must not strand an orphan after its parent exits."""
    calls = []

    class ExitedParent:
        pid = 12345

        def poll(self):
            return 0

        def kill(self):
            pytest.fail("parent kill cannot replace descendant group cleanup")

        def wait(self):
            calls.append("wait")

    def interrupted_once(pid, sig):
        assert (pid, sig) == (12345, signal.SIGKILL)
        calls.append("group")
        if calls.count("group") == 1:
            raise InterruptedError()

    monkeypatch.setattr(adapter.os, "killpg", interrupted_once)
    adapter._kill_process_group(ExitedParent())
    assert calls == ["group", "group", "wait"]


@pytest.mark.skipif(os.name != "posix", reason="POSIX process groups only")
def test_persistent_group_kill_interruptions_are_bounded(monkeypatch):
    """Persistent EINTR must not spin forever; reap the live worker."""
    calls = []

    class LiveParent:
        pid = 12346

        def poll(self):
            return None

        def kill(self):
            calls.append("kill-parent")

        def wait(self):
            calls.append("wait")

    def always_interrupted(pid, sig):
        assert (pid, sig) == (12346, signal.SIGKILL)
        calls.append("group")
        raise InterruptedError()

    monkeypatch.setattr(adapter.os, "killpg", always_interrupted)
    adapter._kill_process_group(LiveParent())
    assert calls == ["group", "group", "group", "kill-parent", "wait"]
