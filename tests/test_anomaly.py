"""Tests for pipewatch.anomaly."""
import math
import pytest

from pipewatch.anomaly import (
    AnomalyError,
    AnomalyPolicy,
    AnomalyResult,
    check_anomaly,
)


# ---------------------------------------------------------------------------
# AnomalyPolicy validation
# ---------------------------------------------------------------------------

def test_default_policy_has_expected_values():
    p = AnomalyPolicy()
    assert p.min_samples == 5
    assert p.z_threshold == 2.5


def test_min_samples_less_than_two_raises():
    with pytest.raises(AnomalyError):
        AnomalyPolicy(min_samples=1)


def test_z_threshold_zero_raises():
    with pytest.raises(AnomalyError):
        AnomalyPolicy(z_threshold=0.0)


def test_negative_z_threshold_raises():
    with pytest.raises(AnomalyError):
        AnomalyPolicy(z_threshold=-1.0)


def test_to_dict_round_trip():
    p = AnomalyPolicy(min_samples=10, z_threshold=3.0)
    assert AnomalyPolicy.from_dict(p.to_dict()).min_samples == 10
    assert AnomalyPolicy.from_dict(p.to_dict()).z_threshold == 3.0


def test_from_dict_defaults():
    p = AnomalyPolicy.from_dict({})
    assert p.min_samples == 5
    assert p.z_threshold == 2.5


# ---------------------------------------------------------------------------
# check_anomaly — insufficient data
# ---------------------------------------------------------------------------

def test_insufficient_data_returns_not_anomaly():
    result = check_anomaly(9999.0, [1.0, 2.0], AnomalyPolicy(min_samples=5))
    assert result.sufficient_data is False
    assert result.is_anomaly is False


def test_insufficient_data_uses_value():
    result = check_anomaly(42.0, [1.0], AnomalyPolicy(min_samples=2))
    # exactly min_samples - 1 → insufficient
    assert result.sufficient_data is False
    assert result.value == 42.0


# ---------------------------------------------------------------------------
# check_anomaly — normal behaviour
# ---------------------------------------------------------------------------

def test_normal_value_not_flagged():
    history = [10.0, 10.1, 9.9, 10.2, 9.8]
    result = check_anomaly(10.05, history)
    assert result.sufficient_data is True
    assert result.is_anomaly is False


def test_extreme_value_flagged_as_anomaly():
    history = [10.0, 10.1, 9.9, 10.2, 9.8]
    result = check_anomaly(50.0, history)
    assert result.sufficient_data is True
    assert result.is_anomaly is True


def test_z_score_is_zero_for_mean_value():
    history = [10.0, 10.0, 10.0, 10.0, 10.0]
    result = check_anomaly(10.0, history)
    assert result.z_score == 0.0
    assert result.is_anomaly is False


def test_constant_history_zero_stddev_not_anomaly():
    history = [5.0] * 6
    result = check_anomaly(5.0, history)
    assert result.stddev == 0.0
    assert result.is_anomaly is False


def test_to_dict_contains_expected_keys():
    history = [1.0, 2.0, 3.0, 4.0, 5.0]
    result = check_anomaly(3.0, history)
    d = result.to_dict()
    for key in ("value", "mean", "stddev", "z_score", "is_anomaly", "sufficient_data"):
        assert key in d


def test_default_policy_used_when_none():
    history = [1.0, 2.0, 3.0, 4.0, 5.0]
    result = check_anomaly(3.0, history, policy=None)
    assert result.sufficient_data is True
