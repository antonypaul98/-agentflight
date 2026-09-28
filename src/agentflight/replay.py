"""Deterministic recorded-value replay."""

from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class ReplayTape(Generic[T]):
    values: tuple[T, ...]

    def read(self, index: int) -> T:
        if index < 0 or index >= len(self.values):
            raise IndexError("replay index out of range")
        return self.values[index]
