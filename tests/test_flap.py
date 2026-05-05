"""Tests for pipewatch.flap — flap detection module."""
import pytest

from pipewatch.flap import (
    FlapError,
    FlapPolicy,
    FlapResult,
    count_flips,
    detect_flap,
)


# ---------------------------------------------------------------------------
# FlapPolicy validation
# ---------------------------------------------------------------------------

def test_default_policy_has_expected_values():
    p = FlapPolicy()
    assert p.window == 10
    assert p.min_flips == 4


def test_window_less_than_two_raises():
    with pytest.raises(FlapError, match="window"):
        FlapPolicy(window=1)


def test_min_flips_less_than_two_raises():
    with pytest.raises(FlapError, match="min_flips"):
        FlapPolicy(min_flips=1)


def test_min_flips_equal_to_window_raises():
    with pytest.raises(FlapError, match="less than window"):
        FlapPolicy(window=5, min_flips=5)


def test_min_flips_greater_than_window_raises():
    with pytest.raises(FlapError, match="less than window"):
        FlapPolicy(window=5, min_flips=6)


def test_valid_policy_does_not_raise():
    p = FlapPolicy(window=6, min_flips=3)
    assert p.window == 6
    assert p.min_flips == 3


# ---------------------------------------------------------------------------
# FlapPolicy serialisation
# ---------------------------------------------------------------------------

def test_to_dict_round_trip():
    p = FlapPolicy(window=8, min_flips=3)
    assert FlapPolicy.from_dict(p.to_dict()) == p


def test_from_dict_uses_defaults_for_missing_keys():
    p = FlapPolicy.from_dict({})
    assert p == FlapPolicy()


# ---------------------------------------------------------------------------
# count_flips
# ---------------------------------------------------------------------------

def test_count_flips_empty_returns_zero():
    assert count_flips([]) == 0


def test_count_flips_single_element_returns_zero():
    assert count_flips([True]) == 0


def test_count_flips_all_same_returns_zero():
    assert count_flips([True, True, True]) == 0


def test_count_flips_alternating():
    assert count_flips([True, False, True, False]) == 3


def test_count_flips_partial_alternation():
    # T F T T F  → flips at positions 1,2,4 = 3
    assert count_flips([True, False, True, True, False]) == 3


# ---------------------------------------------------------------------------
# detect_flap
# ---------------------------------------------------------------------------

def test_stable_success_is_not_flapping():
    outcomes = [True] * 10
    result = detect_flap(outcomes)
    assert not result.is_flapping
    assert result.flips == 0


def test_alternating_outcomes_detected_as_flapping():
    outcomes = [True, False] * 5  # 10 outcomes, 9 flips
    result = detect_flap(outcomes)
    assert result.is_flapping
    assert result.flips == 9


def test_window_limits_inspection():
    # Only last 4 outcomes are stable; earlier ones flip a lot
    policy = FlapPolicy(window=4, min_flips=3)
    outcomes = [True, False] * 10 + [True, True, True, True]
    result = detect_flap(outcomes, policy)
    assert not result.is_flapping
    assert result.window_size == 4


def test_result_contains_windowed_outcomes():
    policy = FlapPolicy(window=4, min_flips=3)
    outcomes = [True, False, True, False, True, False]
    result = detect_flap(outcomes, policy)
    assert result.outcomes == [True, False, True, False]


def test_detect_flap_uses_default_policy_when_none():
    outcomes = [True, False] * 5
    result = detect_flap(outcomes, policy=None)
    assert isinstance(result, FlapResult)
    assert result.is_flapping


def test_result_to_dict_contains_expected_keys():
    result = detect_flap([True, False, True])
    d = result.to_dict()
    assert set(d.keys()) == {"is_flapping", "flips", "window_size", "outcomes"}
