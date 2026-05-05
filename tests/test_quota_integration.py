"""Integration tests: Quota across instances with realistic workloads."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from pipewatch.quota import Quota, QuotaPolicy


@pytest.fixture()
def quota_file(tmp_path: Path) -> Path:
    return tmp_path / "quota.json"


def test_quota_enforced_across_multiple_instances(quota_file: Path) -> None:
    p = QuotaPolicy(max_runs=3, window_seconds=300)
    for _ in range(3):
        q = Quota(quota_file)
        q.record("pipeline", p)
    q_final = Quota(quota_file)
    assert q_final.is_exceeded("pipeline", p) is True
    assert q_final.remaining("pipeline", p) == 0


def test_expired_runs_allow_new_quota(quota_file: Path) -> None:
    """Inject old timestamps; they should be pruned so quota resets."""
    old = (datetime.now(timezone.utc) - timedelta(seconds=400)).isoformat()
    quota_file.write_text(json.dumps({
        "job": {"job": "job", "timestamps": [old, old, old]}
    }))
    p = QuotaPolicy(max_runs=3, window_seconds=300)
    q = Quota(quota_file)
    assert q.is_exceeded("job", p) is False
    assert q.remaining("job", p) == 3


def test_mixed_fresh_and_stale_timestamps(quota_file: Path) -> None:
    now = datetime.now(timezone.utc)
    stale = (now - timedelta(seconds=200)).isoformat()
    fresh = (now - timedelta(seconds=10)).isoformat()
    quota_file.write_text(json.dumps({
        "job": {"job": "job", "timestamps": [stale, fresh, fresh]}
    }))
    p = QuotaPolicy(max_runs=3, window_seconds=60)
    q = Quota(quota_file)
    # Only 2 fresh timestamps within 60s window
    assert q.remaining("job", p) == 1
    assert q.is_exceeded("job", p) is False


def test_reset_allows_immediate_reuse(quota_file: Path) -> None:
    p = QuotaPolicy(max_runs=1, window_seconds=3600)
    q = Quota(quota_file)
    q.record("etl", p)
    assert q.is_exceeded("etl", p) is True
    q.reset("etl")
    q2 = Quota(quota_file)
    assert q2.is_exceeded("etl", p) is False
    q2.record("etl", p)
    assert q2.is_exceeded("etl", p) is True
