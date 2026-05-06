"""Tests for pipewatch.prestige streak tracking."""
import pytest
from pathlib import Path

from pipewatch.prestige import Prestige, PrestigeError, StreakState


@pytest.fixture
def streak_file(tmp_path: Path) -> Path:
    return tmp_path / "streaks.json"


@pytest.fixture
def ps(streak_file: Path) -> Prestige:
    return Prestige(streak_file)


def test_get_unknown_job_returns_none(ps: Prestige) -> None:
    assert ps.get("unknown") is None


def test_record_empty_job_raises(ps: Prestige) -> None:
    with pytest.raises(PrestigeError):
        ps.record("", success=True)


def test_first_success_starts_streak(ps: Prestige) -> None:
    state = ps.record("etl", success=True)
    assert state.current_streak == 1
    assert state.streak_type == "success"
    assert state.best_success_streak == 1
    assert state.worst_failure_streak == 0


def test_consecutive_successes_increment_streak(ps: Prestige) -> None:
    ps.record("etl", success=True)
    ps.record("etl", success=True)
    state = ps.record("etl", success=True)
    assert state.current_streak == 3
    assert state.best_success_streak == 3


def test_failure_after_success_resets_streak(ps: Prestige) -> None:
    ps.record("etl", success=True)
    ps.record("etl", success=True)
    state = ps.record("etl", success=False)
    assert state.current_streak == 1
    assert state.streak_type == "failure"
    assert state.best_success_streak == 2  # preserved


def test_worst_failure_streak_tracked(ps: Prestige) -> None:
    for _ in range(4):
        ps.record("job", success=False)
    state = ps.get("job")
    assert state.worst_failure_streak == 4


def test_best_streak_not_overwritten_by_shorter_run(ps: Prestige) -> None:
    ps.record("job", success=True)
    ps.record("job", success=True)
    ps.record("job", success=True)  # streak = 3
    ps.record("job", success=False)  # reset
    ps.record("job", success=True)  # streak = 1
    state = ps.get("job")
    assert state.best_success_streak == 3


def test_state_persists_across_instances(streak_file: Path) -> None:
    p1 = Prestige(streak_file)
    p1.record("pipe", success=True)
    p1.record("pipe", success=True)

    p2 = Prestige(streak_file)
    state = p2.get("pipe")
    assert state is not None
    assert state.current_streak == 2


def test_clear_removes_job(ps: Prestige) -> None:
    ps.record("job", success=True)
    ps.clear("job")
    assert ps.get("job") is None


def test_clear_nonexistent_job_is_safe(ps: Prestige) -> None:
    ps.clear("ghost")  # should not raise


def test_all_jobs_returns_sorted(ps: Prestige) -> None:
    ps.record("zebra", success=True)
    ps.record("alpha", success=False)
    ps.record("mango", success=True)
    assert ps.all_jobs() == ["alpha", "mango", "zebra"]


def test_streak_state_to_dict_round_trip() -> None:
    s = StreakState(
        job="test",
        current_streak=5,
        streak_type="success",
        best_success_streak=5,
        worst_failure_streak=2,
    )
    restored = StreakState.from_dict(s.to_dict())
    assert restored.job == s.job
    assert restored.current_streak == s.current_streak
    assert restored.streak_type == s.streak_type
    assert restored.best_success_streak == s.best_success_streak
    assert restored.worst_failure_streak == s.worst_failure_streak
