"""Verification-aware deterministic tool replay."""

from dataclasses import dataclass

from .contract import CallContract
from .recording import RecordedToolExchange
from .result import CheckResult
from .verifier import verify_call


@dataclass(frozen=True)
class ReplayCheck:
    check: CheckResult
    result: object | None = None


def replay_exchange(
    contract: CallContract,
    exchange: RecordedToolExchange,
) -> ReplayCheck:
    check = verify_call(contract, exchange.name, exchange.arguments)
    if not check.passed:
        return ReplayCheck(check)
    return ReplayCheck(check, exchange.result)
