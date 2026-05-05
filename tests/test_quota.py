"""Unit tests for pipewatch.quota."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from pipewatch.quota import Quota, QuotaError, QuotaPolicy


@pytest.fixture()
def quota_file(tmp_path: Path) -> Path:
    return tmp_path / "quota.json"


@pytest.fixture()
def q(quota_file: Path) -> Quota:
    return Quota(quota_file)


def _policy(max_runs: int = 3, window_seconds: int = 60) -> QuotaPolicy:
    return QuotaPolicy(max_runs=max_runs, window_seconds=window_seconds)


# --- QuotaPolicy validation ---

def test_invalid_max_runs_raises() -> None:
    with pytest.raises(QuotaError):
        QuotaPolicy(max_runs=0, window_seconds=60)


def test_invalid_window_raises() -> None:
    with pytest.raises(QuotaError):
        QuotaPolicy(max_runs=5, window_seconds=0)


def test_policy_to_dict_round_trip() -> None:
    p = _policy()
    assert QuotaPolicy.from_dict(p.to_dict()) == p


# --- Quota logic ---

def test_new_job_is_not_exceeded(q: Quota) -> None:
    assert q.is_exceeded("etl", _policy()) is False


def test_remaining_full_for_new_job(q: Quota) -> None:
    assert q.remaining("etl", _policy(max_runs=5)) == 5


def test_record_increments_count(q: Quota) -> None:
    p = _policy(max_runs=3)
    q.record("etl", p)
    assert q.remaining("etl", p) == 2


def test_quota_exceeded_after_max_runs(q: Quota) -> None:
    p = _policy(max_runs=2)
    q.record("etl", p)
    q.record("etl", p)
    assert q.is_exceeded("etl", p) is True


def test_remaining_never_negative(q: Quota) -> None:
    p = _policy(max_runs=1)
    q.record("etl", p)
    q.record("etl", p)  # over limit
    assert q.remaining("etl", p) == 0


def test_reset_clears_state(q: Quota, quota_file: Path) -> None:
    p = _policy(max_runs=1)
    q.record("etl", p)
    q.reset("etl")
    assert q.is_exceeded("etl", p) is False
    data = json.loads(quota_file.read_text())
    assert "etl" not in data


def test_stale_timestamps_are_pruned(q: Quota, quota_file: Path) -> None:
    """Timestamps outside the window should not count toward the quota."""
    old_ts = (datetime.now(timezone.utc) - timedelta(seconds=7200)).isoformat()
    quota_file.write_text(json.dumps({"etl": {"job": "etl", "timestamps": [old_ts]}}))
    q2 = Quota(quota_file)
    p = _policy(max_runs=1, window_seconds=60)
    assert q2.is_exceeded("etl", p) is False


def test_different_jobs_are_independent(q: Quota) -> None:
    p = _policy(max_runs=1)
    q.record("job_a", p)
    assert q.is_exceeded("job_a", p) is True
    assert q.is_exceeded("job_b", p) is False


def test_state_persists_across_instances(quota_file: Path) -> None:
    p = _policy(max_runs=3)
    q1 = Quota(quota_file)
    q1.record("etl", p)
    q2 = Quota(quota_file)
    assert q2.remaining("etl", p) == 2
