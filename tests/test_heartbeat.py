"""Tests for pipewatch.heartbeat."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from pipewatch.heartbeat import Heartbeat, HeartbeatEntry


@pytest.fixture()
def hb_file(tmp_path: Path) -> Path:
    return tmp_path / "heartbeat.json"


@pytest.fixture()
def hb(hb_file: Path) -> Heartbeat:
    return Heartbeat(hb_file)


# ---------------------------------------------------------------------------
# HeartbeatEntry serialisation
# ---------------------------------------------------------------------------

def test_entry_to_dict_round_trip() -> None:
    entry = HeartbeatEntry(job="etl", timestamp=1_700_000_000.5, note="ok")
    assert HeartbeatEntry.from_dict(entry.to_dict()) == entry


def test_entry_from_dict_missing_note_defaults_empty() -> None:
    entry = HeartbeatEntry.from_dict({"job": "etl", "timestamp": 1.0})
    assert entry.note == ""


# ---------------------------------------------------------------------------
# Heartbeat.ping / last
# ---------------------------------------------------------------------------

def test_ping_returns_entry_with_correct_job(hb: Heartbeat) -> None:
    entry = hb.ping("my-job")
    assert entry.job == "my-job"


def test_last_returns_none_for_unknown_job(hb: Heartbeat) -> None:
    assert hb.last("ghost") is None


def test_last_returns_most_recent(hb: Heartbeat) -> None:
    hb.ping("job", note="first")
    second = hb.ping("job", note="second")
    assert hb.last("job") == second


# ---------------------------------------------------------------------------
# Heartbeat.is_stale
# ---------------------------------------------------------------------------

def test_stale_when_no_entry(hb: Heartbeat) -> None:
    assert hb.is_stale("missing", max_age_seconds=60) is True


def test_not_stale_immediately_after_ping(hb: Heartbeat) -> None:
    hb.ping("job")
    assert hb.is_stale("job", max_age_seconds=60) is False


def test_stale_after_max_age_exceeded(hb: Heartbeat) -> None:
    entry = hb.ping("job")
    # Manually backdate the timestamp so it appears old.
    entry.timestamp -= 120
    hb._entries[-1] = entry
    hb._save()
    assert hb.is_stale("job", max_age_seconds=60) is True


# ---------------------------------------------------------------------------
# Heartbeat.all_entries / clear
# ---------------------------------------------------------------------------

def test_all_entries_returns_all_when_no_filter(hb: Heartbeat) -> None:
    hb.ping("a")
    hb.ping("b")
    assert len(hb.all_entries()) == 2


def test_all_entries_filters_by_job(hb: Heartbeat) -> None:
    hb.ping("a")
    hb.ping("b")
    hb.ping("a")
    assert len(hb.all_entries(job="a")) == 2


def test_clear_specific_job_leaves_others(hb: Heartbeat) -> None:
    hb.ping("a")
    hb.ping("b")
    hb.clear(job="a")
    assert hb.all_entries(job="a") == []
    assert len(hb.all_entries(job="b")) == 1


def test_clear_all_removes_everything(hb: Heartbeat) -> None:
    hb.ping("a")
    hb.ping("b")
    hb.clear()
    assert hb.all_entries() == []


# ---------------------------------------------------------------------------
# Persistence across instances
# ---------------------------------------------------------------------------

def test_entries_persist_across_instances(hb_file: Path) -> None:
    hb1 = Heartbeat(hb_file)
    hb1.ping("job", note="saved")

    hb2 = Heartbeat(hb_file)
    assert hb2.last("job") is not None
    assert hb2.last("job").note == "saved"  # type: ignore[union-attr]
