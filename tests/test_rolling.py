"""Tests for pipewatch.rolling."""
import pytest

from pipewatch.rolling import (
    RollingError,
    RollingWindow,
    RollingStats,
    compute_rolling,
)


# ---------------------------------------------------------------------------
# RollingWindow
# ---------------------------------------------------------------------------

def test_default_window_size_is_ten():
    w = RollingWindow()
    assert w.size == 10


def test_size_zero_raises():
    with pytest.raises(RollingError):
        RollingWindow(size=0)


def test_negative_size_raises():
    with pytest.raises(RollingError):
        RollingWindow(size=-3)


def test_to_dict_round_trip():
    w = RollingWindow(size=5)
    assert RollingWindow.from_dict(w.to_dict()) == w


def test_from_dict_defaults():
    w = RollingWindow.from_dict({})
    assert w.size == 10


# ---------------------------------------------------------------------------
# compute_rolling — empty input
# ---------------------------------------------------------------------------

def test_empty_durations_returns_none_stats():
    stats = compute_rolling([], RollingWindow(size=5))
    assert stats.count == 0
    assert stats.mean is None
    assert stats.minimum is None
    assert stats.maximum is None
    assert stats.p50 is None
    assert stats.p95 is None


# ---------------------------------------------------------------------------
# compute_rolling — single value
# ---------------------------------------------------------------------------

def test_single_value_all_stats_equal():
    stats = compute_rolling([42.0], RollingWindow(size=5))
    assert stats.count == 1
    assert stats.mean == pytest.approx(42.0)
    assert stats.minimum == pytest.approx(42.0)
    assert stats.maximum == pytest.approx(42.0)
    assert stats.p50 == pytest.approx(42.0)
    assert stats.p95 == pytest.approx(42.0)


# ---------------------------------------------------------------------------
# compute_rolling — window truncation
# ---------------------------------------------------------------------------

def test_window_limits_to_most_recent_entries():
    durations = [100.0, 200.0, 1.0, 2.0, 3.0]
    stats = compute_rolling(durations, RollingWindow(size=3))
    assert stats.count == 3
    assert stats.minimum == pytest.approx(1.0)
    assert stats.maximum == pytest.approx(3.0)


def test_window_larger_than_data_uses_all():
    durations = [10.0, 20.0]
    stats = compute_rolling(durations, RollingWindow(size=100))
    assert stats.count == 2


# ---------------------------------------------------------------------------
# compute_rolling — statistics correctness
# ---------------------------------------------------------------------------

def test_mean_is_correct():
    stats = compute_rolling([1.0, 2.0, 3.0, 4.0, 5.0], RollingWindow(size=5))
    assert stats.mean == pytest.approx(3.0)


def test_p50_median_even_count():
    stats = compute_rolling([1.0, 2.0, 3.0, 4.0], RollingWindow(size=4))
    assert stats.p50 == pytest.approx(2.5)


def test_p95_is_near_maximum_for_large_window():
    durations = list(range(1, 101))  # 1..100
    stats = compute_rolling(durations, RollingWindow(size=100))
    assert stats.p95 == pytest.approx(95.05)


def test_to_dict_contains_all_keys():
    stats = compute_rolling([5.0, 10.0], RollingWindow(size=5))
    d = stats.to_dict()
    assert set(d.keys()) == {"count", "mean", "minimum", "maximum", "p50", "p95"}
