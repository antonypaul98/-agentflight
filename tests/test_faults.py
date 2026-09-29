import pytest

from agentflight.faults import (
    Fault,
    FaultKind,
    FaultPlan,
    InjectedFault,
    InjectedTimeout,
    inject,
)


def test_no_fault_preserves_original_value() -> None:
    plan = FaultPlan((Fault(at_call=2, kind=FaultKind.ERROR),))
    assert inject(plan, 0, {"ok": True}) == {"ok": True}


def test_value_fault_is_reproducible() -> None:
    plan = FaultPlan((Fault(at_call=1, kind=FaultKind.VALUE, value={"status": 503}),))
    assert inject(plan, 1, {"status": 200}) == {"status": 503}
    assert inject(plan, 1, {"status": 200}) == {"status": 503}


@pytest.mark.parametrize(
    ("kind", "exception"),
    [(FaultKind.ERROR, InjectedFault), (FaultKind.TIMEOUT, InjectedTimeout)],
)
def test_exception_faults_are_deterministic(kind: FaultKind, exception: type[Exception]) -> None:
    plan = FaultPlan((Fault(at_call=0, kind=kind, message="boom"),))
    with pytest.raises(exception, match="boom"):
        inject(plan, 0, "original")


def test_plan_rejects_duplicate_call_targets() -> None:
    with pytest.raises(ValueError, match="only one fault"):
        FaultPlan(
            (
                Fault(at_call=1, kind=FaultKind.ERROR),
                Fault(at_call=1, kind=FaultKind.TIMEOUT),
            )
        )


@pytest.mark.parametrize("index", [-1, -10])
def test_negative_call_indices_are_rejected(index: int) -> None:
    with pytest.raises(ValueError, match="at_call must be non-negative"):
        Fault(at_call=index, kind=FaultKind.ERROR)


def test_value_fault_requires_explicit_value() -> None:
    with pytest.raises(ValueError, match="value fault requires a value"):
        Fault(at_call=0, kind=FaultKind.VALUE)


def test_lookup_rejects_negative_call_index() -> None:
    with pytest.raises(ValueError, match="call_index must be non-negative"):
        FaultPlan(()).for_call(-1)
