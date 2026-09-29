"""Deterministic fault-injection primitives for reproducible agent tests."""

from dataclasses import dataclass
from enum import Enum
from typing import Generic, TypeVar

T = TypeVar("T")


class FaultKind(str, Enum):
    ERROR = "error"
    TIMEOUT = "timeout"
    VALUE = "value"


@dataclass(frozen=True)
class Fault(Generic[T]):
    at_call: int
    kind: FaultKind
    value: T | None = None
    message: str = "injected fault"

    def __post_init__(self) -> None:
        if self.at_call < 0:
            raise ValueError("at_call must be non-negative")
        if self.kind is FaultKind.VALUE and self.value is None:
            raise ValueError("value fault requires a value")


@dataclass(frozen=True)
class FaultPlan(Generic[T]):
    faults: tuple[Fault[T], ...]

    def __post_init__(self) -> None:
        calls = [fault.at_call for fault in self.faults]
        if len(calls) != len(set(calls)):
            raise ValueError("only one fault may be configured per call")

    def for_call(self, call_index: int) -> Fault[T] | None:
        if call_index < 0:
            raise ValueError("call_index must be non-negative")
        return next((fault for fault in self.faults if fault.at_call == call_index), None)


class InjectedFault(RuntimeError):
    """Raised when a deterministic error fault is activated."""


class InjectedTimeout(TimeoutError):
    """Raised when a deterministic timeout fault is activated."""


def inject(plan: FaultPlan[T], call_index: int, original: T) -> T:
    """Apply the configured fault for one call without mutable hidden state."""
    fault = plan.for_call(call_index)
    if fault is None:
        return original
    if fault.kind is FaultKind.ERROR:
        raise InjectedFault(fault.message)
    if fault.kind is FaultKind.TIMEOUT:
        raise InjectedTimeout(fault.message)
    return fault.value  # type: ignore[return-value]
