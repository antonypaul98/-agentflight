"""Keep missing/unexpected argument evidence bounded and deterministic."""

from agentflight.contract import CallContract
from agentflight.result import CheckResult
from agentflight.verifier import MAX_ARGUMENT_MISMATCH_DETAIL, verify_call


def test_short_missing_and_unexpected_details_are_unchanged():
    missing = verify_call(CallContract('lookup', required=frozenset({'b', 'a'})), 'lookup', {})
    unexpected = verify_call(CallContract('lookup'), 'lookup', {'b': 1, 'a': 2})
    assert missing == CheckResult(False, 'missing_required', 'a,b')
    assert unexpected == CheckResult(False, 'unexpected_argument', 'a,b')


def test_long_missing_required_name_is_truncated_without_large_evidence():
    long_name = 'x' * 10000
    result = verify_call(CallContract('lookup', required=frozenset({long_name})), 'lookup', {})
    assert result.code == 'missing_required'
    assert result.detail == 'x' * (MAX_ARGUMENT_MISMATCH_DETAIL - len('<truncated>')) + '<truncated>'
    assert len(result.detail) == MAX_ARGUMENT_MISMATCH_DETAIL


def test_long_unexpected_name_is_truncated_without_large_evidence():
    long_name = 'x' * 10000
    result = verify_call(CallContract('lookup'), 'lookup', {long_name: 1})
    assert result.code == 'unexpected_argument'
    assert result.detail == 'x' * (MAX_ARGUMENT_MISMATCH_DETAIL - len('<truncated>')) + '<truncated>'
    assert len(result.detail) == MAX_ARGUMENT_MISMATCH_DETAIL


def test_many_names_have_order_independent_bounded_evidence():
    names = [f'field_{i:04d}' for i in range(64)]
    first = verify_call(CallContract('lookup'), 'lookup', dict.fromkeys(names))
    second = verify_call(CallContract('lookup'), 'lookup', dict.fromkeys(reversed(names)))
    assert first == second
    assert first.code == 'unexpected_argument'
    assert len(first.detail) == MAX_ARGUMENT_MISMATCH_DETAIL
    assert first.detail.endswith('<truncated>')
    assert first.detail.startswith('field_0000,field_0001,')


def test_boundary_and_validation_precedence():
    exact = 'x' * MAX_ARGUMENT_MISMATCH_DETAIL
    contract = CallContract('lookup', required=frozenset({exact}))
    assert verify_call(contract, 'lookup', {}).detail == exact
    result = verify_call(CallContract('lookup', required=frozenset({exact, 'a'})), 'lookup', {})
    assert len(result.detail) == MAX_ARGUMENT_MISMATCH_DETAIL
    assert result.detail.endswith('<truncated>')
    assert verify_call(contract, 'wrong', {}).code == 'name_mismatch'
    assert verify_call(contract, 'lookup', {'a': 1, 'b': 2}, max_arguments=1).code == 'too_many_arguments'
