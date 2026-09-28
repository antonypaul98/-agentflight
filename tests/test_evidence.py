from agentflight.evidence import evidence_id
from agentflight.result import CheckResult


def test_evidence_id_is_repeatable() -> None:
    check = CheckResult(False, "missing_required", "query")
    assert evidence_id(check, tool_name="lookup", arguments={"limit": 3}) == evidence_id(
        check, tool_name="lookup", arguments={"limit": 3}
    )


def test_evidence_id_ignores_mapping_order() -> None:
    check = CheckResult(False, "unexpected_argument", "extra")
    left = evidence_id(check, arguments={"query": "x", "limit": 3})
    right = evidence_id(check, arguments={"limit": 3, "query": "x"})
    assert left == right


def test_evidence_id_changes_for_distinct_failure() -> None:
    missing = evidence_id(CheckResult(False, "missing_required", "query"))
    mismatch = evidence_id(CheckResult(False, "name_mismatch", "other"))
    assert missing != mismatch
