from agentflight.contract import CallContract
from agentflight.recording import RecordedToolExchange
from agentflight.replay_check import replay_exchange


def test_replay_exchange_returns_recorded_result_after_verification() -> None:
    contract = CallContract(name="lookup", required=frozenset({"query"}))
    exchange = RecordedToolExchange("lookup", {"query": "agentflight"}, {"value": 1})
    replayed = replay_exchange(contract, exchange)
    assert replayed.check.passed is True
    assert replayed.result == {"value": 1}


def test_replay_exchange_rejects_invalid_recording() -> None:
    contract = CallContract(name="lookup", required=frozenset({"query"}))
    exchange = RecordedToolExchange("lookup", {}, {"value": 1})
    replayed = replay_exchange(contract, exchange)
    assert replayed.check.passed is False
    assert replayed.check.code == "missing_required"
    assert replayed.result is None


def test_replay_exchange_success_evidence_id_is_stable() -> None:
    contract = CallContract(name="lookup", required=frozenset({"query"}))
    exchange = RecordedToolExchange("lookup", {"query": "agentflight"}, {"value": 1})
    first = replay_exchange(contract, exchange)
    second = replay_exchange(contract, exchange)
    assert first.evidence_id
    assert first.evidence_id == second.evidence_id


def test_replay_exchange_failure_evidence_id_is_stable() -> None:
    contract = CallContract(name="lookup", required=frozenset({"query"}))
    exchange = RecordedToolExchange("lookup", {}, {"value": 1})
    first = replay_exchange(contract, exchange)
    second = replay_exchange(contract, exchange)
    assert first.evidence_id
    assert first.evidence_id == second.evidence_id


def test_replay_exchange_evidence_id_ignores_argument_order() -> None:
    contract = CallContract(
        name="lookup",
        required=frozenset({"query"}),
        optional=frozenset({"limit"}),
    )
    first = replay_exchange(
        contract,
        RecordedToolExchange("lookup", {"query": "agentflight", "limit": 3}, {"value": 1}),
    )
    second = replay_exchange(
        contract,
        RecordedToolExchange("lookup", {"limit": 3, "query": "agentflight"}, {"value": 1}),
    )
    assert first.evidence_id == second.evidence_id
