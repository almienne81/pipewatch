"""Tests for pipewatch.backoff."""
import pytest

from pipewatch.backoff import BackoffError, BackoffPolicy, format_delay


# ---------------------------------------------------------------------------
# BackoffPolicy construction
# ---------------------------------------------------------------------------

def test_default_policy_has_expected_values():
    p = BackoffPolicy()
    assert p.base_seconds == 1.0
    assert p.multiplier == 2.0
    assert p.max_seconds == 300.0
    assert p.jitter is False


def test_invalid_base_seconds_raises():
    with pytest.raises(BackoffError, match="base_seconds"):
        BackoffPolicy(base_seconds=0)


def test_invalid_multiplier_raises():
    with pytest.raises(BackoffError, match="multiplier"):
        BackoffPolicy(multiplier=0.5)


def test_max_less_than_base_raises():
    with pytest.raises(BackoffError, match="max_seconds"):
        BackoffPolicy(base_seconds=10.0, max_seconds=5.0)


# ---------------------------------------------------------------------------
# delay calculations
# ---------------------------------------------------------------------------

def test_attempt_zero_returns_base():
    p = BackoffPolicy(base_seconds=2.0, multiplier=3.0)
    assert p.delay(0) == 2.0


def test_exponential_growth():
    p = BackoffPolicy(base_seconds=1.0, multiplier=2.0)
    assert p.delay(0) == 1.0
    assert p.delay(1) == 2.0
    assert p.delay(2) == 4.0
    assert p.delay(3) == 8.0


def test_delay_capped_at_max():
    p = BackoffPolicy(base_seconds=1.0, multiplier=2.0, max_seconds=10.0)
    assert p.delay(10) == 10.0


def test_negative_attempt_raises():
    p = BackoffPolicy()
    with pytest.raises(BackoffError, match="attempt"):
        p.delay(-1)


def test_delays_list_length():
    p = BackoffPolicy(base_seconds=1.0, multiplier=2.0)
    result = p.delays(5)
    assert len(result) == 5
    assert result == [1.0, 2.0, 4.0, 8.0, 16.0]


# ---------------------------------------------------------------------------
# serialisation round-trip
# ---------------------------------------------------------------------------

def test_to_dict_round_trip():
    p = BackoffPolicy(base_seconds=3.0, multiplier=1.5, max_seconds=60.0, jitter=True)
    restored = BackoffPolicy.from_dict(p.to_dict())
    assert restored == p


def test_from_dict_uses_defaults_for_missing_keys():
    p = BackoffPolicy.from_dict({})
    assert p.base_seconds == 1.0
    assert p.multiplier == 2.0


# ---------------------------------------------------------------------------
# format_delay
# ---------------------------------------------------------------------------

def test_format_delay_seconds():
    assert format_delay(5.0) == "5.0s"


def test_format_delay_minutes():
    assert format_delay(90.0) == "1.5m"


def test_format_delay_hours():
    assert format_delay(7200.0) == "2.0h"
