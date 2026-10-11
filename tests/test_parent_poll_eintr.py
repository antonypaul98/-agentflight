"""AF-22: parent fallback bounds interrupted liveness checks."""

import os
import signal

import pytest

import agentflight.synthetic_subprocess as adapter


pytestmark = pytest.mark.skipif(os.name != "posix", reason="POSIX process groups only")


def test_parent_fallback_retries_transient_poll_interruption(monkeypatch):
    events = []

    class Parent:
        pid = 12366
        killed = False

        def poll(self):
            events.append("poll")
            if events.count("poll") == 1:
                raise InterruptedError("synthetic transient liveness interruption")
            return -signal.SIGKILL if self.killed else None

        def kill(self):
            events.append("kill")
            self.killed = True

        def wait(self):
            events.append("wait")

    def group_missing(pid, sig):
        assert (pid, sig) == (12366, signal.SIGKILL)
        events.append("group")
        raise ProcessLookupError("group absent")

    monkeypatch.setattr(adapter.os, "killpg", group_missing)
    adapter._kill_process_group(Parent())
    assert events == ["group", "poll", "poll", "kill", "wait"]


def test_parent_fallback_persistent_poll_interruptions_are_bounded(monkeypatch):
    events = []

    class Parent:
        pid = 12367

        def poll(self):
            events.append("poll")
            raise InterruptedError("SYNTHETIC_PRIVATE_TOKEN_931")

        def kill(self):
            pytest.fail("cannot signal a parent whose liveness is unknown")

        def wait(self):
            pytest.fail("cannot wait after an unknown liveness result")

    def group_missing(pid, sig):
        assert (pid, sig) == (12367, signal.SIGKILL)
        events.append("group")
        raise ProcessLookupError("group absent")

    monkeypatch.setattr(adapter.os, "killpg", group_missing)
    with pytest.raises(InterruptedError, match="liveness check repeatedly interrupted"):
        adapter._kill_process_group(Parent())
    assert events == ["group", "poll", "poll", "poll"]
