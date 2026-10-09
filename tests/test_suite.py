from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys

import pytest

import agentflight.suite as suite
from agentflight.suite import FixtureError, MAX_CASES, MAX_FIXTURE_BYTES, run_suite


def fixture():
    return {
        "schema_version": 1, "suite_id": "synthetic",
        "cases": [
            {"case_id": "valid", "contract": {"name": "lookup", "required": ["query"], "optional": ["limit"]},
             "exchange": {"name": "lookup", "arguments": {"query": "synthetic", "limit": 2}, "result": {"value": 1}},
             "expected": {"passed": True, "code": "ok"}},
            {"case_id": "rejection", "contract": {"name": "lookup", "required": ["query"]},
             "exchange": {"name": "lookup", "arguments": {}},
             "expected": {"passed": False, "code": "missing_required"}},
        ],
    }


def invoke(tmp_path, content):
    path = tmp_path / "suite.json"
    path.write_bytes(content if isinstance(content, bytes) else json.dumps(content).encode())
    # Exercise the installed CLI from a separate synthetic directory, not a
    # modified cwd/sys.path or mocked command invocation.
    return subprocess.run([sys.executable, "-m", "agentflight.suite", str(path)],
                          cwd=tmp_path, text=True, capture_output=True, timeout=10)


def test_expected_rejections_are_verified_passing_test_cases():
    report = run_suite(fixture())
    assert report["status"] == "passed"
    assert report["summary"] == {"total": 2, "passed": 2, "failed": 0, "error": 0}
    rejection = report["cases"][0]
    assert rejection["observed"] == {"passed": False, "code": "missing_required"}
    assert rejection["status"] == "passed"


def test_wrong_rejection_reason_fails_even_when_both_verdicts_are_false():
    data = fixture()
    data["cases"][1]["expected"]["code"] = "unexpected_argument"
    report = run_suite(data)
    assert report["status"] == "failed"
    assert report["summary"] == {"total": 2, "passed": 1, "failed": 1, "error": 0}
    failure = report["cases"][0]
    assert failure["expected"]["code"] == "unexpected_argument"
    assert failure["observed"]["code"] == "missing_required"
    assert failure["diagnostic"]
    assert len(failure["evidence_id"]) == 64


def test_unexpected_success_cannot_pass_a_negative_case():
    data = fixture()
    data["cases"][1]["exchange"]["arguments"] = {"query": "synthetic"}
    failure = run_suite(data)["cases"][0]
    assert failure["status"] == "failed"
    assert failure["observed"] == {"passed": True, "code": "ok"}


def test_reports_stable_under_case_argument_and_declaration_ordering():
    data = fixture()
    before = deepcopy(data)
    data["cases"][0]["exchange"]["arguments"] = {"limit": 2, "query": "synthetic"}
    data["cases"].reverse()
    assert run_suite(data) == run_suite(before)
    assert before == fixture()  # Running never mutates the recording.
    assert run_suite(before) == run_suite(before)


def test_evidence_is_scoped_to_suite_case_and_observed_recording():
    first = fixture()
    original = run_suite(first)["cases"][1]["evidence_id"]
    other_suite = deepcopy(first)
    other_suite["suite_id"] = "other-project"
    assert run_suite(other_suite)["cases"][1]["evidence_id"] != original
    other_case = deepcopy(first)
    other_case["cases"][0]["case_id"] = "valid-other"
    assert run_suite(other_case)["cases"][1]["evidence_id"] != original
    changed = deepcopy(first)
    changed["cases"][0]["exchange"]["arguments"]["query"] = "different-recording"
    assert run_suite(changed)["cases"][1]["evidence_id"] != original


def test_reports_do_not_echo_private_arguments_results_or_mismatch_detail():
    data = fixture()
    secret = "SYNTHETIC_PRIVATE_TOKEN_917"
    data["cases"][0]["exchange"]["arguments"]["query"] = secret
    data["cases"][0]["exchange"]["result"] = {"private_result": secret}
    data["cases"][1]["exchange"]["name"] = secret
    text = json.dumps(run_suite(data))
    assert secret not in text
    assert "private_result" not in text
    assert "arguments" not in text
    assert "result" not in text


def test_replay_exception_is_a_redacted_error_and_never_an_expected_rejection(monkeypatch):
    def broken(*args):
        raise RuntimeError("SYNTHETIC_SECRET_EXCEPTION_918")
    monkeypatch.setattr(suite, "replay_exchange", broken)
    report = run_suite(fixture())
    assert report["status"] == "failed"
    assert report["summary"] == {"total": 2, "passed": 0, "failed": 0, "error": 2}
    assert all(c["observed"] is None and c["evidence_id"] is None for c in report["cases"])
    assert "SYNTHETIC_SECRET_EXCEPTION_918" not in json.dumps(report)


def test_keyboard_interrupt_is_not_swallowed(monkeypatch):
    def interrupted(*args):
        raise KeyboardInterrupt
    monkeypatch.setattr(suite, "replay_exchange", interrupted)
    with pytest.raises(KeyboardInterrupt):
        run_suite(fixture())


@pytest.mark.parametrize("change", [
    lambda d: d.update(schema_version=True),
    lambda d: d.update(schema_version=2),
    lambda d: d.update(cases=[]),
    lambda d: d.update(suite_id="../other-repository"),
    lambda d: d.update(command="execute forbidden content"),
    lambda d: d["cases"].append(deepcopy(d["cases"][0])),
    lambda d: d["cases"][0]["expected"].update(passed=1),
    lambda d: d["cases"][0]["expected"].update(code="invented_success"),
    lambda d: d["cases"][0]["expected"].update(passed=False),
    lambda d: d["cases"][0]["contract"].update(required=["query", "query"]),
    lambda d: d["cases"][0]["exchange"].update(arguments=[]),
])
def test_invalid_fixture_is_rejected_before_any_replay(change, monkeypatch):
    data = fixture()
    change(data)
    calls = []
    monkeypatch.setattr(suite, "replay_exchange", lambda *args: calls.append(args))
    with pytest.raises(FixtureError):
        run_suite(data)
    assert calls == []


def test_case_count_boundary():
    base = fixture()["cases"][0]
    data = {"schema_version": 1, "suite_id": "bounded", "cases": []}
    for i in range(MAX_CASES):
        case = deepcopy(base)
        case["case_id"] = f"case-{i:03d}"
        data["cases"].append(case)
    assert run_suite(data)["summary"]["passed"] == MAX_CASES
    extra = deepcopy(base)
    extra["case_id"] = "over-limit"
    data["cases"].append(extra)
    with pytest.raises(FixtureError, match="case_count_limit"):
        run_suite(data)


def test_custom_serialization_hooks_are_never_executed():
    class Unsafe(dict):
        def items(self):
            raise AssertionError("custom mapping must not be read")
    data = fixture()
    data["cases"][0]["exchange"]["result"] = Unsafe()
    with pytest.raises(FixtureError, match="invalid_json_type"):
        run_suite(data)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), 1 << 5000])
def test_invalid_json_numbers_fail_closed(value):
    data = fixture()
    data["cases"][0]["exchange"]["result"] = value
    with pytest.raises(FixtureError, match="invalid_json_number"):
        run_suite(data)


def test_json_depth_and_node_bounds():
    data = fixture()
    nested = []
    for _ in range(40):
        nested = [nested]
    data["cases"][0]["exchange"]["result"] = nested
    with pytest.raises(FixtureError, match="json_structure_limit"):
        run_suite(data)
    data["cases"][0]["exchange"]["result"] = [None] * (suite.MAX_JSON_NODES + 1)
    with pytest.raises(FixtureError, match="json_structure_limit"):
        run_suite(data)


def test_cli_pass_and_failure_exit_codes_and_stable_bytes(tmp_path):
    data = fixture()
    first = invoke(tmp_path, data)
    assert first.returncode == 0 and first.stderr == ""
    data["cases"].reverse()
    assert invoke(tmp_path, data).stdout == first.stdout
    data["cases"][0]["expected"]["code"] = "name_mismatch"
    failed = invoke(tmp_path, data)
    assert failed.returncode == 1
    assert json.loads(failed.stdout)["summary"]["failed"] == 1


@pytest.mark.parametrize("content", [b"{", b"\xff", b'{"schema_version":1,"schema_version":2}',
                                      b" " * (MAX_FIXTURE_BYTES + 1), b"[]", b"NaN"],
                         ids=["malformed", "invalid-utf8", "duplicate-keys", "oversized", "wrong-root", "nan"])
def test_cli_invalid_input_returns_diagnostic_exit_two(tmp_path, content):
    result = invoke(tmp_path, content)
    assert result.returncode == 2
    report = json.loads(result.stdout)
    assert report["status"] == "invalid_fixture" and report["diagnostic"]
    assert "Traceback" not in result.stderr


def test_cli_fixture_strings_cannot_execute_commands_or_read_environment(tmp_path, monkeypatch):
    marker = tmp_path / "other-repository-marker"
    data = fixture()
    data["cases"][0]["exchange"]["arguments"]["query"] = f"__import__('pathlib').Path({str(marker)!r}).write_text('executed')"
    monkeypatch.setenv("AGENTFLIGHT_SYNTHETIC_SECRET", "SECRET_ENVIRONMENT_919")
    result = invoke(tmp_path, data)
    assert result.returncode == 0
    assert not marker.exists()
    assert "SECRET_ENVIRONMENT_919" not in result.stdout
    assert "__import__" not in result.stdout


def test_checked_in_synthetic_example(tmp_path):
    example = Path(__file__).resolve().parents[1] / "examples/replay-suite.json"
    result = invoke(tmp_path, example.read_bytes())
    assert result.returncode == 0
    assert json.loads(result.stdout)["summary"]["passed"] == 2
