"""Result types for AgentFlight checks."""

from dataclasses import dataclass


@dataclass(frozen=True)
class CheckResult:
    passed: bool
    code: str
    detail: str = ""
