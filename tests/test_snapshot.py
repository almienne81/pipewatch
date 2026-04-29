"""Tests for pipewatch.snapshot."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from pipewatch.snapshot import Snapshot, SnapshotEntry


@pytest.fixture
def snap_file(tmp_path: Path) -> Path:
    return tmp_path / "snapshot.json"


@pytest.fixture
def snap(snap_file: Path) -> Snapshot:
    return Snapshot(snap_file)


def test_empty_snapshot_returns_empty_list(snap: Snapshot) -> None:
    assert snap.all() == []


def test_get_missing_job_returns_none(snap: Snapshot) -> None:
    assert snap.get("nonexistent") is None


def test_capture_records_entry(snap: Snapshot) -> None:
    entry = snap.capture("etl", "ok", exit_code=0)
    assert entry.job == "etl"
    assert entry.status == "ok"
    assert entry.exit_code == 0


def test_capture_overwrites_previous_entry(snap: Snapshot) -> None:
    snap.capture("etl", "ok", exit_code=0)
    snap.capture("etl", "fail", exit_code=1)
    assert len(snap.all()) == 1
    assert snap.get("etl").status == "fail"


def test_capture_persists_to_disk(snap_file: Path) -> None:
    s1 = Snapshot(snap_file)
    s1.capture("job-a", "ok", exit_code=0, note="done", tags={"env": "prod"})
    s2 = Snapshot(snap_file)
    entry = s2.get("job-a")
    assert entry is not None
    assert entry.status == "ok"
    assert entry.note == "done"
    assert entry.tags == {"env": "prod"}


def test_multiple_jobs_stored_independently(snap: Snapshot) -> None:
    snap.capture("job-a", "ok")
    snap.capture("job-b", "fail", exit_code=2)
    assert len(snap.all()) == 2
    assert snap.get("job-a").status == "ok"
    assert snap.get("job-b").exit_code == 2


def test_clear_specific_job(snap: Snapshot) -> None:
    snap.capture("job-a", "ok")
    snap.capture("job-b", "ok")
    snap.clear("job-a")
    assert snap.get("job-a") is None
    assert snap.get("job-b") is not None


def test_clear_all_jobs(snap: Snapshot) -> None:
    snap.capture("job-a", "ok")
    snap.capture("job-b", "fail")
    snap.clear()
    assert snap.all() == []


def test_entry_to_dict_round_trip() -> None:
    entry = SnapshotEntry(job="x", timestamp=1234.5, status="ok",
                          exit_code=0, note="hi", tags={"k": "v"})
    restored = SnapshotEntry.from_dict(entry.to_dict())
    assert restored.job == entry.job
    assert restored.timestamp == entry.timestamp
    assert restored.tags == {"k": "v"}


def test_entry_timestamp_is_recent(snap: Snapshot) -> None:
    before = time.time()
    entry = snap.capture("t", "ok")
    after = time.time()
    assert before <= entry.timestamp <= after
