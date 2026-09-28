"""Recorded tool exchanges for deterministic replay."""

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class RecordedToolExchange:
    name: str
    arguments: Mapping[str, object]
    result: object
