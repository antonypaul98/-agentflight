import pytest

from agentflight.replay import ReplayTape


def test_replay_returns_recorded_values_in_order() -> None:
    tape = ReplayTape(("first", "second", "third"))
    assert [tape.read(i) for i in range(3)] == ["first", "second", "third"]


def test_replay_is_repeatable() -> None:
    tape = ReplayTape(({"result": 1}, {"result": 2}))
    first = [tape.read(i) for i in range(2)]
    second = [tape.read(i) for i in range(2)]
    assert first == second


@pytest.mark.parametrize("index", [-1, 2])
def test_replay_rejects_out_of_range_index(index: int) -> None:
    tape = ReplayTape(("first", "second"))
    with pytest.raises(IndexError, match="replay index out of range"):
        tape.read(index)
