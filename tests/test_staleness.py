"""Tests for pipewatch.staleness."""
from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest

from pipewatch.staleness import (
    StalenessError,
    StalenessPolicy,
    StalenessTracker,
)


@pytest.fixture()
def state_file(tmp_path: Path) -> Path:
    return tmp_path / "staleness.json"


@pytest.fixture()
def tracker(state_file: Path) -> StalenessTracker:
    return StalenessTracker(path=state_file)


# ---------------------------------------------------------------------------
# StalenessPolicy
# ---------------------------------------------------------------------------

def test_default_policy_requires_max_age():
    p = StalenessPolicy(max_age_seconds=300)
    assert p.max_age_seconds == 300
    assert p.warn_age_seconds is None


def test_zero_max_age_raises():
    with pytest.raises(StalenessError):
        StalenessPolicy(max_age_seconds=0)


def test_negative_max_age_raises():
    with pytest.raises(StalenessError):
        StalenessPolicy(max_age_seconds=-1)


def test_warn_must_be_less_than_max():
    with pytest.raises(StalenessError):
        StalenessPolicy(max_age_seconds=100, warn_age_seconds=100)


def test_warn_greater_than_max_raises():
    with pytest.raises(StalenessError):
        StalenessPolicy(max_age_seconds=100, warn_age_seconds=200)


def test_valid_warn_less_than_max():
    p = StalenessPolicy(max_age_seconds=300, warn_age_seconds=150)
    assert p.warn_age_seconds == 150


def test_to_dict_round_trip():
    p = StalenessPolicy(max_age_seconds=600, warn_age_seconds=300)
    assert StalenessPolicy.from_dict(p.to_dict()).max_age_seconds == 600
    assert StalenessPolicy.from_dict(p.to_dict()).warn_age_seconds == 300


# ---------------------------------------------------------------------------
# StalenessTracker
# ---------------------------------------------------------------------------

def test_get_unknown_job_returns_none(tracker):
    assert tracker.get("missing") is None


def test_ping_records_entry(tracker):
    entry = tracker.ping("etl-job")
    assert entry.job == "etl-job"
    assert tracker.get("etl-job") is not None


def test_ping_empty_job_raises(tracker):
    with pytest.raises(StalenessError):
        tracker.ping("")


def test_ping_persists_to_disk(state_file):
    t = StalenessTracker(path=state_file)
    t.ping("job-a")
    t2 = StalenessTracker(path=state_file)
    assert t2.get("job-a") is not None


def test_check_fresh_job_is_ok(tracker):
    tracker.ping("job-b")
    policy = StalenessPolicy(max_age_seconds=3600)
    assert tracker.check("job-b", policy) == "ok"


def test_check_missing_job_is_stale(tracker):
    policy = StalenessPolicy(max_age_seconds=60)
    assert tracker.check("nonexistent", policy) == "stale"


def test_check_old_entry_is_stale(state_file):
    t = StalenessTracker(path=state_file)
    t.ping("old-job")
    # Manually backdate the entry
    entry = t.get("old-job")
    entry.last_seen = datetime.now(timezone.utc) - timedelta(seconds=7200)
    t._entries["old-job"] = entry
    t._save()
    policy = StalenessPolicy(max_age_seconds=3600)
    assert t.check("old-job", policy) == "stale"


def test_check_warn_zone(state_file):
    t = StalenessTracker(path=state_file)
    t.ping("warn-job")
    entry = t.get("warn-job")
    entry.last_seen = datetime.now(timezone.utc) - timedelta(seconds=200)
    t._entries["warn-job"] = entry
    t._save()
    policy = StalenessPolicy(max_age_seconds=300, warn_age_seconds=100)
    assert t.check("warn-job", policy) == "warn"


def test_clear_removes_entry(tracker):
    tracker.ping("to-clear")
    tracker.clear("to-clear")
    assert tracker.get("to-clear") is None


def test_all_entries_returns_list(tracker):
    tracker.ping("a")
    tracker.ping("b")
    assert len(tracker.all_entries()) == 2
