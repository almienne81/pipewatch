"""Unit tests for pipewatch.stagger."""
import pytest
from pipewatch.stagger import (
    StaggerError,
    StaggerPolicy,
    all_delays,
    delay_for_job,
    slot_delay,
    slot_for_job,
)


def test_default_policy_has_expected_values():
    p = StaggerPolicy()
    assert p.window_seconds == 60.0
    assert p.slots == 1
    assert p.offset_seconds == 0.0


def test_window_zero_raises():
    with pytest.raises(StaggerError, match="window_seconds"):
        StaggerPolicy(window_seconds=0)


def test_window_negative_raises():
    with pytest.raises(StaggerError, match="window_seconds"):
        StaggerPolicy(window_seconds=-5.0)


def test_slots_zero_raises():
    with pytest.raises(StaggerError, match="slots"):
        StaggerPolicy(slots=0)


def test_negative_offset_raises():
    with pytest.raises(StaggerError, match="offset_seconds"):
        StaggerPolicy(offset_seconds=-1.0)


def test_to_dict_round_trip():
    p = StaggerPolicy(window_seconds=120.0, slots=4, offset_seconds=5.0)
    d = p.to_dict()
    p2 = StaggerPolicy.from_dict(d)
    assert p2.window_seconds == 120.0
    assert p2.slots == 4
    assert p2.offset_seconds == 5.0


def test_from_dict_defaults():
    p = StaggerPolicy.from_dict({})
    assert p.window_seconds == 60.0
    assert p.slots == 1
    assert p.offset_seconds == 0.0


def test_slot_delay_single_slot():
    p = StaggerPolicy(window_seconds=60.0, slots=1)
    assert slot_delay(p, 0) == pytest.approx(0.0)


def test_slot_delay_multiple_slots():
    p = StaggerPolicy(window_seconds=60.0, slots=4)
    assert slot_delay(p, 0) == pytest.approx(0.0)
    assert slot_delay(p, 1) == pytest.approx(15.0)
    assert slot_delay(p, 2) == pytest.approx(30.0)
    assert slot_delay(p, 3) == pytest.approx(45.0)


def test_slot_delay_with_offset():
    p = StaggerPolicy(window_seconds=60.0, slots=2, offset_seconds=10.0)
    assert slot_delay(p, 0) == pytest.approx(10.0)
    assert slot_delay(p, 1) == pytest.approx(40.0)


def test_slot_delay_out_of_range_raises():
    p = StaggerPolicy(slots=3)
    with pytest.raises(StaggerError, match="out of range"):
        slot_delay(p, 3)
    with pytest.raises(StaggerError, match="out of range"):
        slot_delay(p, -1)


def test_all_delays_length_matches_slots():
    p = StaggerPolicy(window_seconds=100.0, slots=5)
    delays = all_delays(p)
    assert len(delays) == 5


def test_all_delays_are_sorted():
    p = StaggerPolicy(window_seconds=90.0, slots=3)
    delays = all_delays(p)
    assert delays == sorted(delays)


def test_slot_for_job_is_deterministic():
    p = StaggerPolicy(slots=8)
    s1 = slot_for_job(p, "etl-job")
    s2 = slot_for_job(p, "etl-job")
    assert s1 == s2


def test_slot_for_job_within_bounds():
    p = StaggerPolicy(slots=5)
    for name in ["a", "b", "c", "pipeline-x", "nightly-export"]:
        assert 0 <= slot_for_job(p, name) < 5


def test_delay_for_job_returns_valid_delay():
    p = StaggerPolicy(window_seconds=60.0, slots=6)
    d = delay_for_job(p, "my-job")
    assert 0.0 <= d < 60.0
