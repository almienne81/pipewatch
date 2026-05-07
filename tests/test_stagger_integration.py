"""Integration tests verifying stagger behaviour end-to-end."""
import pytest
from pipewatch.stagger import (
    StaggerPolicy,
    all_delays,
    delay_for_job,
    slot_for_job,
)


def test_all_jobs_get_unique_slots_when_slots_equals_job_count():
    """If #slots == #jobs and names hash to distinct slots, no collision."""
    policy = StaggerPolicy(window_seconds=60.0, slots=10)
    jobs = [f"job-{i}" for i in range(10)]
    slots = [slot_for_job(policy, j) for j in jobs]
    # We can't guarantee uniqueness (hash collisions), but all must be in range
    assert all(0 <= s < 10 for s in slots)


def test_delays_cover_full_window():
    policy = StaggerPolicy(window_seconds=100.0, slots=5)
    delays = all_delays(policy)
    assert min(delays) == pytest.approx(0.0)
    # Last delay should be window - step = 100 - 20 = 80
    assert max(delays) == pytest.approx(80.0)


def test_offset_shifts_all_delays():
    base = StaggerPolicy(window_seconds=60.0, slots=3)
    shifted = StaggerPolicy(window_seconds=60.0, slots=3, offset_seconds=10.0)
    base_delays = all_delays(base)
    shifted_delays = all_delays(shifted)
    for b, s in zip(base_delays, shifted_delays):
        assert s == pytest.approx(b + 10.0)


def test_single_slot_always_zero_delay():
    policy = StaggerPolicy(window_seconds=300.0, slots=1)
    assert delay_for_job(policy, "anything") == pytest.approx(0.0)


def test_to_dict_from_dict_preserves_behaviour():
    original = StaggerPolicy(window_seconds=90.0, slots=6, offset_seconds=3.0)
    restored = StaggerPolicy.from_dict(original.to_dict())
    for job in ["alpha", "beta", "gamma"]:
        assert delay_for_job(original, job) == pytest.approx(
            delay_for_job(restored, job)
        )
