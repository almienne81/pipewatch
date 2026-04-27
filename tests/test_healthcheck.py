"""Tests for pipewatch.healthcheck."""

import pytest

from pipewatch.healthcheck import (
    HealthThresholds,
    HealthReport,
    evaluate_health,
)


# ---------------------------------------------------------------------------
# HealthThresholds validation
# ---------------------------------------------------------------------------

def test_default_thresholds_are_valid():
    t = HealthThresholds()
    assert t.min_success_rate == 0.8
    assert t.max_consecutive_failures == 3
    assert t.min_runs == 1


def test_invalid_success_rate_raises():
    with pytest.raises(ValueError, match="min_success_rate"):
        HealthThresholds(min_success_rate=1.5)


def test_invalid_consecutive_failures_raises():
    with pytest.raises(ValueError, match="max_consecutive_failures"):
        HealthThresholds(max_consecutive_failures=0)


def test_invalid_min_runs_raises():
    with pytest.raises(ValueError, match="min_runs"):
        HealthThresholds(min_runs=0)


# ---------------------------------------------------------------------------
# evaluate_health – insufficient data
# ---------------------------------------------------------------------------

def test_empty_outcomes_is_unhealthy():
    report = evaluate_health([])
    assert report.healthy is False
    assert report.total_runs == 0
    assert report.success_rate is None
    assert "insufficient runs" in report.reasons[0]


def test_below_min_runs_threshold_is_unhealthy():
    report = evaluate_health([True], thresholds=HealthThresholds(min_runs=5))
    assert report.healthy is False
    assert report.success_rate is None


# ---------------------------------------------------------------------------
# evaluate_health – healthy scenarios
# ---------------------------------------------------------------------------

def test_all_successes_is_healthy():
    report = evaluate_health([True, True, True])
    assert report.healthy is True
    assert report.success_rate == pytest.approx(1.0)
    assert report.consecutive_failures == 0
    assert report.reasons == []


def test_exactly_at_threshold_is_healthy():
    # 4 successes out of 5 = 0.8 == default min_success_rate
    outcomes = [True, True, True, True, False]
    report = evaluate_health(outcomes)
    assert report.healthy is True
    assert report.success_rate == pytest.approx(0.8)


# ---------------------------------------------------------------------------
# evaluate_health – unhealthy scenarios
# ---------------------------------------------------------------------------

def test_low_success_rate_is_unhealthy():
    outcomes = [False, False, False, True]  # 25 %
    report = evaluate_health(outcomes)
    assert report.healthy is False
    assert any("success rate" in r for r in report.reasons)


def test_too_many_consecutive_failures_is_unhealthy():
    outcomes = [True, True, False, False, False]  # 3 trailing failures
    report = evaluate_health(outcomes, thresholds=HealthThresholds(max_consecutive_failures=3))
    assert report.healthy is False
    assert any("consecutive" in r for r in report.reasons)


def test_multiple_reasons_reported():
    # Low rate AND consecutive failures
    outcomes = [False, False, False, False]
    report = evaluate_health(outcomes, thresholds=HealthThresholds(max_consecutive_failures=3))
    assert report.healthy is False
    assert len(report.reasons) == 2


# ---------------------------------------------------------------------------
# HealthReport.to_dict
# ---------------------------------------------------------------------------

def test_to_dict_contains_expected_keys():
    report = evaluate_health([True, False, True])
    d = report.to_dict()
    assert set(d.keys()) == {"healthy", "total_runs", "success_rate", "consecutive_failures", "reasons"}


def test_to_dict_reasons_is_copy():
    report = evaluate_health([False, False, False])
    d = report.to_dict()
    d["reasons"].clear()
    assert len(report.reasons) > 0  # original unchanged
