"""Call contract model."""

from dataclasses import dataclass


@dataclass(frozen=True)
class CallContract:
    name: str
    required: frozenset[str] = frozenset()
    optional: frozenset[str] = frozenset()
