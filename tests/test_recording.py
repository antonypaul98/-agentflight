from agentflight.recording import RecordedToolExchange
from agentflight.replay import ReplayTape


def test_recorded_exchange_replays_exactly() -> None:
    exchange = RecordedToolExchange(
        name="lookup",
        arguments={"query": "agentflight"},
        result={"value": 1},
    )
    tape = ReplayTape((exchange,))
    assert tape.read(0) == exchange
