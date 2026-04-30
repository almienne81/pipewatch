"""Tests for pipewatch.wavg."""
import pytest

from pipewatch.wavg import (
    WAvgError,
    WeightedSample,
    duration_weighted_average,
    from_pairs,
    success_rate_trend,
    weighted_average,
)


# ---------------------------------------------------------------------------
# WeightedSample
# ---------------------------------------------------------------------------

def test_weighted_sample_negative_weight_raises():
    with pytest.raises(WAvgError, match="non-negative"):
        WeightedSample(value=1.0, weight=-0.1)


def test_weighted_sample_zero_weight_is_valid():
    s = WeightedSample(value=5.0, weight=0.0)
    assert s.weight == 0.0


# ---------------------------------------------------------------------------
# weighted_average
# ---------------------------------------------------------------------------

def test_weighted_average_empty_returns_none():
    assert weighted_average([]) is None


def test_weighted_average_all_zero_weights_returns_none():
    samples = from_pairs([(1.0, 0.0), (2.0, 0.0)])
    assert weighted_average(samples) is None


def test_weighted_average_equal_weights():
    samples = from_pairs([(2.0, 1.0), (4.0, 1.0)])
    result = weighted_average(samples)
    assert result == pytest.approx(3.0)


def test_weighted_average_unequal_weights():
    # value=10 weight=1, value=0 weight=9  -> (10+0)/10 = 1.0
    samples = from_pairs([(10.0, 1.0), (0.0, 9.0)])
    result = weighted_average(samples)
    assert result == pytest.approx(1.0)


def test_weighted_average_single_sample():
    samples = from_pairs([(42.0, 3.0)])
    assert weighted_average(samples) == pytest.approx(42.0)


# ---------------------------------------------------------------------------
# from_pairs
# ---------------------------------------------------------------------------

def test_from_pairs_builds_correct_samples():
    samples = from_pairs([(1.0, 2.0), (3.0, 4.0)])
    assert len(samples) == 2
    assert samples[0].value == 1.0
    assert samples[1].weight == 4.0


# ---------------------------------------------------------------------------
# duration_weighted_average
# ---------------------------------------------------------------------------

def test_duration_weighted_average_empty_returns_none():
    assert duration_weighted_average([]) is None


def test_duration_weighted_average_single_element():
    assert duration_weighted_average([7.0]) == pytest.approx(7.0)


def test_duration_weighted_average_recent_bias():
    # [1.0, 100.0] — later value has weight 2 vs 1
    result = duration_weighted_average([1.0, 100.0])
    # (1*1 + 100*2) / 3 = 201/3 = 67.0
    assert result == pytest.approx(67.0)


# ---------------------------------------------------------------------------
# success_rate_trend
# ---------------------------------------------------------------------------

def test_success_rate_trend_empty_returns_none():
    assert success_rate_trend([]) is None


def test_success_rate_trend_all_success():
    result = success_rate_trend([True, True, True])
    assert result == pytest.approx(1.0)


def test_success_rate_trend_all_failure():
    result = success_rate_trend([False, False, False])
    assert result == pytest.approx(0.0)


def test_success_rate_trend_window_limits_samples():
    # 5 failures then 5 successes; window=5 should only see successes
    outcomes = [False] * 5 + [True] * 5
    result = success_rate_trend(outcomes, window=5)
    assert result == pytest.approx(1.0)


def test_success_rate_trend_recent_success_outweighs_old_failure():
    # [False, True] weights [1, 2] -> (0*1 + 1*2)/3 = 2/3
    result = success_rate_trend([False, True])
    assert result == pytest.approx(2 / 3)
