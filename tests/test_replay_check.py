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
