import json
import pytest
import agentflight.synthetic_subprocess as adapter

@pytest.mark.parametrize('error_type', [OSError, ValueError])
def test_cleanup_exception_always_closes_pipes_and_redacts(monkeypatch, error_type):
    real_popen = adapter.subprocess.Popen
    real_cleanup = adapter._kill_process_group
    seen = []

    def observed_popen(*args, **kwargs):
        process = real_popen(*args, **kwargs)
        seen.append(process)
        return process

    def failing_cleanup(process):
        real_cleanup(process)
        raise error_type('SYNTHETIC_PRIVATE_TOKEN_931')

    monkeypatch.setattr(adapter.subprocess, 'Popen', observed_popen)
    monkeypatch.setattr(adapter, '_kill_process_group', failing_cleanup)
    result = adapter.run_synthetic_case('cleanup-failure', 'pass')
    assert result['status'] == 'error' and result['code'] == 'launch_error'
    assert (result['stdout_bytes'], result['stderr_bytes']) == (0, 0)
    assert 'PRIVATE_TOKEN' not in json.dumps(result)
    assert len(seen) == 1
    assert seen[0].poll() is not None
    assert seen[0].stdout.closed and seen[0].stderr.closed
