"""Tests for pipewatch.sparkline."""
import pytest

from pipewatch.sparkline import (
    SparklineError,
    SparklinePolicy,
    render,
    success_rate_sparkline,
)


# ---------------------------------------------------------------------------
# SparklinePolicy
# ---------------------------------------------------------------------------

def test_default_policy_has_expected_values():
    p = SparklinePolicy()
    assert p.width == 20
    assert p.min_value is None
    assert p.max_value is None


def test_width_zero_raises():
    with pytest.raises(SparklineError, match="width"):
        SparklinePolicy(width=0)


def test_min_ge_max_raises():
    with pytest.raises(SparklineError, match="min_value"):
        SparklinePolicy(min_value=5.0, max_value=5.0)


def test_min_greater_than_max_raises():
    with pytest.raises(SparklineError, match="min_value"):
        SparklinePolicy(min_value=10.0, max_value=1.0)


def test_to_dict_round_trip():
    p = SparklinePolicy(width=10, min_value=0.0, max_value=100.0)
    assert SparklinePolicy.from_dict(p.to_dict()) == p


def test_from_dict_defaults():
    p = SparklinePolicy.from_dict({})
    assert p.width == 20
    assert p.min_value is None


# ---------------------------------------------------------------------------
# render
# ---------------------------------------------------------------------------

def test_empty_values_returns_empty_string():
    assert render([]) == ""


def test_single_value_returns_one_char():
    result = render([42.0])
    assert len(result) == 1


def test_length_matches_input_when_within_width():
    values = [float(i) for i in range(10)]
    result = render(values, SparklinePolicy(width=20))
    assert len(result) == 10


def test_length_capped_at_width():
    values = [float(i) for i in range(50)]
    result = render(values, SparklinePolicy(width=20))
    assert len(result) == 20


def test_uniform_values_use_mid_block():
    result = render([5.0, 5.0, 5.0])
    # All characters must be identical
    assert len(set(result)) == 1


def test_ascending_series_ends_higher_than_start():
    from pipewatch.sparkline import _BLOCKS
    values = [0.0, 25.0, 50.0, 75.0, 100.0]
    result = render(values)
    assert _BLOCKS.index(result[-1]) > _BLOCKS.index(result[0])


def test_explicit_min_max_clamps_values():
    # values outside [0, 1] should be clamped, not crash
    result = render([-10.0, 0.5, 20.0], SparklinePolicy(min_value=0.0, max_value=1.0))
    assert len(result) == 3


def test_only_uses_last_width_samples():
    values = [0.0] * 5 + [100.0] * 5
    result = render(values, SparklinePolicy(width=5))
    # Only the last 5 (all 100.0) should appear
    assert len(set(result)) == 1


# ---------------------------------------------------------------------------
# success_rate_sparkline
# ---------------------------------------------------------------------------

def test_all_success_gives_high_blocks():
    from pipewatch.sparkline import _BLOCKS
    result = success_rate_sparkline([True, True, True])
    for ch in result:
        assert _BLOCKS.index(ch) > 0


def test_all_failure_gives_low_blocks():
    from pipewatch.sparkline import _BLOCKS
    result = success_rate_sparkline([False, False, False])
    for ch in result:
        assert _BLOCKS.index(ch) == 0 or ch == " "


def test_empty_outcomes_returns_empty():
    assert success_rate_sparkline([]) == ""
