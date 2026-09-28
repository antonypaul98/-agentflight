"""Verification-aware deterministic tool replay."""

from dataclasses import dataclass

from .contract import CallContract
from .evidence import evidence_id
from .recording import RecordedToolExchange
from .result import CheckResult
from .verifier import verify_call


@dataclass(frozen=True)
class ReplayCheck:
    check: CheckResult
    result: object | None = None
    evidence_id: str = ""


def replay_exchange(contract: CallContract, exchange: RecordedToolExchange) -> ReplayCheck:
    check = verify_call(contract, exchange.name, exchange.arguments)
    identifier = evidence_id(check, tool_name=exchange.name, arguments=exchange.arguments)
    if not check.passed:
        return ReplayCheck(check, evidence_id=identifier)
    return ReplayCheck(check, exchange.result, identifier)
