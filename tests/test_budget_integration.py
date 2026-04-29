"""Integration tests: budget policy interacts with duration parsing and monitor."""
from pipewatch.budget import BudgetPolicy, check_budget
from pipewatch.duration import parse_duration


def _policy(warn: str | None = None, fail: str | None = None) -> BudgetPolicy:
    return BudgetPolicy(
        warn_seconds=parse_duration(warn) if warn else None,
        fail_seconds=parse_duration(fail) if fail else None,
    )


def test_duration_strings_resolve_correctly():
    p = _policy(warn="5m", fail="10m")
    assert p.warn_seconds == 300
    assert p.fail_seconds == 600


def test_elapsed_just_below_warn_is_ok():
    p = _policy(warn="1m")
    result = check_budget(p, elapsed=59.9)
    assert not result.warned
    assert not result.failed


def test_elapsed_exactly_at_warn_triggers_warn():
    p = _policy(warn="1m", fail="2m")
    result = check_budget(p, elapsed=60.0)
    assert result.warned
    assert not result.failed


def test_elapsed_exactly_at_fail_triggers_fail():
    p = _policy(warn="1m", fail="2m")
    result = check_budget(p, elapsed=120.0)
    assert result.failed


def test_round_trip_via_dict_preserves_behaviour():
    original = _policy(warn="30s", fail="2m")
    restored = BudgetPolicy.from_dict(original.to_dict())
    r1 = check_budget(original, elapsed=45)
    r2 = check_budget(restored, elapsed=45)
    assert r1.warned == r2.warned
    assert r1.failed == r2.failed
    assert r1.message == r2.message
