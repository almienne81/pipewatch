"""Unit tests for pipewatch.budget."""
import pytest

from pipewatch.budget import BudgetError, BudgetPolicy, BudgetResult, check_budget


# ---------------------------------------------------------------------------
# BudgetPolicy construction
# ---------------------------------------------------------------------------

def test_default_policy_has_no_limits():
    p = BudgetPolicy()
    assert p.warn_seconds is None
    assert p.fail_seconds is None


def test_invalid_warn_seconds_raises():
    with pytest.raises(BudgetError):
        BudgetPolicy(warn_seconds=0)


def test_invalid_fail_seconds_raises():
    with pytest.raises(BudgetError):
        BudgetPolicy(fail_seconds=-1)


def test_warn_must_be_less_than_fail():
    with pytest.raises(BudgetError):
        BudgetPolicy(warn_seconds=60, fail_seconds=60)


def test_warn_less_than_fail_is_valid():
    p = BudgetPolicy(warn_seconds=30, fail_seconds=60)
    assert p.warn_seconds == 30
    assert p.fail_seconds == 60


# ---------------------------------------------------------------------------
# to_dict / from_dict
# ---------------------------------------------------------------------------

def test_to_dict_round_trip():
    p = BudgetPolicy(warn_seconds=120.0, fail_seconds=300.0)
    d = p.to_dict()
    p2 = BudgetPolicy.from_dict(d)
    assert p2.warn_seconds == p.warn_seconds
    assert p2.fail_seconds == p.fail_seconds


def test_from_dict_defaults_to_none():
    p = BudgetPolicy.from_dict({})
    assert p.warn_seconds is None
    assert p.fail_seconds is None


# ---------------------------------------------------------------------------
# check_budget
# ---------------------------------------------------------------------------

def test_within_budget_returns_ok():
    policy = BudgetPolicy(warn_seconds=60, fail_seconds=120)
    result = check_budget(policy, elapsed=30)
    assert not result.warned
    assert not result.failed
    assert result.message == ""


def test_exceeds_warn_returns_warned():
    policy = BudgetPolicy(warn_seconds=60, fail_seconds=120)
    result = check_budget(policy, elapsed=90)
    assert result.warned
    assert not result.failed
    assert "soft budget" in result.message.lower()


def test_exceeds_fail_returns_failed():
    policy = BudgetPolicy(warn_seconds=60, fail_seconds=120)
    result = check_budget(policy, elapsed=150)
    assert result.failed
    assert not result.warned
    assert "hard budget" in result.message.lower()


def test_no_limits_always_ok():
    policy = BudgetPolicy()
    result = check_budget(policy, elapsed=9999)
    assert not result.warned
    assert not result.failed


def test_only_fail_limit_no_warn():
    policy = BudgetPolicy(fail_seconds=100)
    result = check_budget(policy, elapsed=50)
    assert not result.warned
    assert not result.failed

    result2 = check_budget(policy, elapsed=100)
    assert result2.failed
