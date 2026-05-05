"""Tests for pipewatch.slabudget."""
from datetime import datetime, timezone, timedelta
import pytest

from pipewatch.slabudget import (
    SLABudgetError,
    SLABudgetPolicy,
    SLABudgetReport,
    evaluate_budget,
)


# ---------------------------------------------------------------------------
# Policy validation
# ---------------------------------------------------------------------------

def test_default_policy_has_expected_values():
    p = SLABudgetPolicy()
    assert p.target_success_rate == 0.99
    assert p.window_seconds == 86400


def test_invalid_success_rate_zero_raises():
    with pytest.raises(SLABudgetError):
        SLABudgetPolicy(target_success_rate=0.0)


def test_invalid_success_rate_above_one_raises():
    with pytest.raises(SLABudgetError):
        SLABudgetPolicy(target_success_rate=1.01)


def test_invalid_window_zero_raises():
    with pytest.raises(SLABudgetError):
        SLABudgetPolicy(window_seconds=0)


def test_invalid_window_negative_raises():
    with pytest.raises(SLABudgetError):
        SLABudgetPolicy(window_seconds=-60)


def test_to_dict_round_trip():
    p = SLABudgetPolicy(target_success_rate=0.95, window_seconds=3600)
    p2 = SLABudgetPolicy.from_dict(p.to_dict())
    assert p2.target_success_rate == 0.95
    assert p2.window_seconds == 3600


# ---------------------------------------------------------------------------
# evaluate_budget helpers
# ---------------------------------------------------------------------------

def _ts(seconds_ago: int, now: datetime) -> datetime:
    return now - timedelta(seconds=seconds_ago)


@pytest.fixture
def now() -> datetime:
    return datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def policy() -> SLABudgetPolicy:
    return SLABudgetPolicy(target_success_rate=0.90, window_seconds=3600)


# ---------------------------------------------------------------------------
# evaluate_budget behaviour
# ---------------------------------------------------------------------------

def test_empty_outcomes_returns_none_fields(policy, now):
    report = evaluate_budget([], policy, now=now)
    assert report.total_runs == 0
    assert report.actual_success_rate is None
    assert report.error_budget_remaining is None
    assert report.exhausted is False


def test_all_successes_budget_full(policy, now):
    outcomes = [(_ts(i * 60, now), True) for i in range(10)]
    report = evaluate_budget(outcomes, policy, now=now)
    assert report.total_runs == 10
    assert report.successful_runs == 10
    assert report.failed_runs == 0
    assert report.exhausted is False
    assert report.error_budget_remaining == 1.0


def test_budget_exhausted_when_failures_exceed_allowance(policy, now):
    # 90% target on 10 runs => 1 allowed failure; 3 failures => exhausted
    outcomes = [(_ts(i * 60, now), i >= 3) for i in range(10)]
    report = evaluate_budget(outcomes, policy, now=now)
    assert report.exhausted is True
    assert report.error_budget_remaining == 0.0


def test_outcomes_outside_window_are_excluded(policy, now):
    old = _ts(7200, now)  # 2 h ago, outside 1 h window
    recent = _ts(30, now)
    outcomes = [(old, False), (recent, True)]
    report = evaluate_budget(outcomes, policy, now=now)
    assert report.total_runs == 1
    assert report.successful_runs == 1
    assert report.exhausted is False


def test_report_to_dict_contains_expected_keys(policy, now):
    outcomes = [(_ts(10, now), True), (_ts(20, now), False)]
    report = evaluate_budget(outcomes, policy, now=now)
    d = report.to_dict()
    for key in ("total_runs", "successful_runs", "failed_runs",
                "actual_success_rate", "error_budget_remaining",
                "exhausted", "policy"):
        assert key in d


def test_partial_budget_remaining(policy, now):
    # 90% target on 10 runs => 1 allowed failure; 1 failure => 0 budget left but not exhausted
    outcomes = [(_ts(i * 60, now), i != 0) for i in range(10)]
    report = evaluate_budget(outcomes, policy, now=now)
    assert report.failed_runs == 1
    assert report.exhausted is False
    assert report.error_budget_remaining == pytest.approx(0.0, abs=1e-6)
