"""AF-22: parent-only fallback handles interrupted kill without unbounded waits."""

import os
import signal

import pytest

import agentflight.synthetic_subprocess as adapter


@pytest.mark.skipif(os.name != "posix", reason="POSIX process groups only")
def test_parent_fallback_recovers_from_transient_kill_interruption(monkeypatch):
    events = []

    class Parent:
        pid = 12361
        killed = False

        def poll(self):
            events.append("poll")
            return None if not self.killed else -signal.SIGKILL

        def kill(self):
            events.append("kill")
            if events.count("kill") == 1:
                raise InterruptedError("transient parent signal interruption")
            self.killed = True

        def wait(self):
            assert self.killed, "must kill live parent before wait"
            events.append("wait")

    def group_missing(pid, sig):
        assert (pid, sig) == (12361, signal.SIGKILL)
        events.append("group")
        raise ProcessLookupError("group absent")

    monkeypatch.setattr(adapter.os, "killpg", group_missing)
    adapter._kill_process_group(Parent())
    assert events == ["group", "poll", "kill", "poll", "kill", "wait"]


@pytest.mark.skipif(os.name != "posix", reason="POSIX process groups only")
def test_parent_fallback_persistent_interruptions_are_bounded(monkeypatch):
    events = []

    class Parent:
        pid = 12362

        def poll(self):
            events.append("poll")
            return None

        def kill(self):
            events.append("kill")
            raise InterruptedError("parent signal still interrupted")

        def wait(self):
            pytest.fail("cannot wait on a live worker without a delivered kill")

    def group_missing(pid, sig):
        assert (pid, sig) == (12362, signal.SIGKILL)
        events.append("group")
        raise ProcessLookupError("group absent")

    monkeypatch.setattr(adapter.os, "killpg", group_missing)
    with pytest.raises(InterruptedError):
        adapter._kill_process_group(Parent())
    assert events == ["group", "poll", "kill", "poll", "kill", "poll", "kill"]


@pytest.mark.skipif(os.name != "posix", reason="POSIX process groups only")
def test_parent_exit_during_interrupted_kill_is_not_signaled_twice(monkeypatch):
    events = []

    class Parent:
        pid = 12363
        exited = False

        def poll(self):
            events.append("poll")
            return 0 if self.exited else None

        def kill(self):
            events.append("kill")
            self.exited = True
            raise InterruptedError("signal raced with exit")

        def wait(self):
            assert self.exited
            events.append("wait")

    def group_missing(pid, sig):
        assert (pid, sig) == (12363, signal.SIGKILL)
        events.append("group")
        raise ProcessLookupError("group absent")

    monkeypatch.setattr(adapter.os, "killpg", group_missing)
    adapter._kill_process_group(Parent())
    assert events == ["group", "poll", "kill", "poll", "wait"]
