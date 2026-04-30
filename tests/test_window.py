"""Tests for pipewatch.window."""
from datetime import datetime, timezone, timedelta
import pytest

from pipewatch.window import WindowError, WindowResult, compute_window


UTC = timezone.utc


def _ts(minutes_ago: float, now: datetime) -> str:
    return (now - timedelta(minutes=minutes_ago)).isoformat()


@pytest.fixture
def now() -> datetime:
    return datetime(2024, 6, 1, 12, 0, 0, tzinfo=UTC)


def test_zero_window_raises(now):
    with pytest.raises(WindowError, match="positive"):
        compute_window([], window_seconds=0, now=now)


def test_negative_window_raises(now):
    with pytest.raises(WindowError):
        compute_window([], window_seconds=-60, now=now)


def test_empty_outcomes_returns_zero_counts(now):
    result = compute_window([], window_seconds=3600, now=now)
    assert result.total == 0
    assert result.successes == 0
    assert result.failures == 0
    assert result.success_rate is None
    assert result.oldest_ts is None
    assert result.newest_ts is None


def test_all_within_window(now):
    outcomes = [
        {"timestamp": _ts(5, now), "success": True},
        {"timestamp": _ts(10, now), "success": True},
        {"timestamp": _ts(20, now), "success": False},
    ]
    result = compute_window(outcomes, window_seconds=3600, now=now)
    assert result.total == 3
    assert result.successes == 2
    assert result.failures == 1
    assert pytest.approx(result.success_rate) == 2 / 3


def test_entries_outside_window_excluded(now):
    outcomes = [
        {"timestamp": _ts(30, now), "success": True},   # inside 1-hour window
        {"timestamp": _ts(90, now), "success": False},  # outside 1-hour window
    ]
    result = compute_window(outcomes, window_seconds=3600, now=now)
    assert result.total == 1
    assert result.successes == 1
    assert result.failures == 0


def test_success_rate_all_failures(now):
    outcomes = [
        {"timestamp": _ts(1, now), "success": False},
        {"timestamp": _ts(2, now), "success": False},
    ]
    result = compute_window(outcomes, window_seconds=600, now=now)
    assert result.success_rate == 0.0


def test_oldest_and_newest_set_correctly(now):
    t1 = now - timedelta(minutes=50)
    t2 = now - timedelta(minutes=10)
    outcomes = [
        {"timestamp": t2.isoformat(), "success": True},
        {"timestamp": t1.isoformat(), "success": False},
    ]
    result = compute_window(outcomes, window_seconds=3600, now=now)
    assert result.oldest_ts == t1.replace(tzinfo=UTC)
    assert result.newest_ts == t2.replace(tzinfo=UTC)


def test_to_dict_contains_expected_keys(now):
    outcomes = [{"timestamp": _ts(1, now), "success": True}]
    result = compute_window(outcomes, window_seconds=300, now=now)
    d = result.to_dict()
    assert set(d.keys()) == {
        "window_seconds", "total", "successes", "failures",
        "success_rate", "oldest_ts", "newest_ts",
    }
    assert d["window_seconds"] == 300
    assert d["total"] == 1


def test_naive_datetime_treated_as_utc(now):
    naive_ts = (now - timedelta(minutes=5)).replace(tzinfo=None).isoformat()
    outcomes = [{"timestamp": naive_ts, "success": True}]
    result = compute_window(outcomes, window_seconds=600, now=now)
    assert result.total == 1
