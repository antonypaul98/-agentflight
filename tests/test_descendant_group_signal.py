"""AF-22 Linux descendant cleanup: signal the whole worker session, not only its parent."""
import os
import signal

import pytest

import agentflight.synthetic_subprocess as adapter


@pytest.mark.skipif(os.name != "posix", reason="POSIX process groups required")
@pytest.mark.parametrize("mode,expected_code", [
    ("orphan_closed_pipes", "ok"),
    ("orphan_pipe", "timeout"),
])
def test_descendant_cleanup_uses_group_sigkill(monkeypatch, mode, expected_code):
    real_killpg = adapter.os.killpg
    signals = []

    def observed_killpg(pgid, sig):
        signals.append((pgid, sig))
        return real_killpg(pgid, sig)

    monkeypatch.setattr(adapter.os, "killpg", observed_killpg)
    result = adapter.run_synthetic_case(
        "group-" + mode.replace("_", "-"), mode, timeout_seconds=0.25
    )

    assert result["code"] == expected_code
    assert len(signals) == 1
    assert signals[0][0] > 0
    assert signals[0][1] == signal.SIGKILL
