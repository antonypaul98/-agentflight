from agentflight.contract import CallContract


def test_call_contract_is_immutable() -> None:
    contract = CallContract("lookup", frozenset({"query"}), frozenset({"limit"}))
    assert contract.name == "lookup"
    assert contract.required == frozenset({"query"})
    assert contract.optional == frozenset({"limit"})
