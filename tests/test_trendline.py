"""Unit tests for pipewatch.trendline."""
import pytest

from pipewatch.trendline import (
    TrendlineError,
    TrendlinePolicy,
    TrendResult,
    compute_trend,
)


# ---------------------------------------------------------------------------
# Policy validation
# ---------------------------------------------------------------------------

def test_default_policy_has_expected_values():
    p = TrendlinePolicy()
    assert p.min_samples == 5
    assert p.slope_warn_threshold == 0.1
    assert p.slope_fail_threshold == 0.5


def test_min_samples_less_than_two_raises():
    with pytest.raises(TrendlineError, match="min_samples"):
        TrendlinePolicy(min_samples=1)


def test_negative_warn_threshold_raises():
    with pytest.raises(TrendlineError, match="slope_warn_threshold"):
        TrendlinePolicy(slope_warn_threshold=-0.1)


def test_fail_less_than_warn_raises():
    with pytest.raises(TrendlineError, match="slope_fail_threshold"):
        TrendlinePolicy(slope_warn_threshold=0.5, slope_fail_threshold=0.2)


def test_equal_warn_and_fail_is_valid():
    p = TrendlinePolicy(slope_warn_threshold=0.3, slope_fail_threshold=0.3)
    assert p.slope_warn_threshold == 0.3


def test_to_dict_round_trip():
    p = TrendlinePolicy(min_samples=3, slope_warn_threshold=0.2, slope_fail_threshold=0.8)
    p2 = TrendlinePolicy.from_dict(p.to_dict())
    assert p2.min_samples == 3
    assert p2.slope_warn_threshold == 0.2
    assert p2.slope_fail_threshold == 0.8


def test_from_dict_uses_defaults_for_missing_keys():
    p = TrendlinePolicy.from_dict({})
    assert p.min_samples == 5


# ---------------------------------------------------------------------------
# compute_trend
# ---------------------------------------------------------------------------

def _policy(**kw):
    return TrendlinePolicy(**kw)


def test_insufficient_data_when_below_min_samples():
    result = compute_trend([1.0, 2.0], _policy(min_samples=5))
    assert result.status == "insufficient_data"
    assert result.n == 2


def test_flat_series_is_ok():
    durations = [2.0] * 10
    result = compute_trend(durations, _policy())
    assert result.status == "ok"
    assert abs(result.slope) < 1e-9


def test_gently_rising_series_warns():
    # slope ≈ 0.2 s/run — above warn (0.1) but below fail (0.5)
    durations = [1.0 + 0.2 * i for i in range(10)]
    result = compute_trend(durations, _policy())
    assert result.status == "warn"
    assert abs(result.slope - 0.2) < 0.01


def test_steeply_rising_series_fails():
    # slope ≈ 1.0 s/run — above fail threshold (0.5)
    durations = [1.0 + 1.0 * i for i in range(10)]
    result = compute_trend(durations, _policy())
    assert result.status == "fail"


def test_result_to_dict_contains_all_keys():
    durations = [float(i) for i in range(10)]
    result = compute_trend(durations, _policy())
    d = result.to_dict()
    assert set(d.keys()) == {"slope", "intercept", "n", "status"}


def test_exactly_min_samples_is_accepted():
    durations = [1.0] * 5
    result = compute_trend(durations, _policy(min_samples=5))
    assert result.status == "ok"
    assert result.n == 5
