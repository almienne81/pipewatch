"""Tests for pipewatch.tombstone."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from pipewatch.tombstone import Tombstone, TombstoneEntry, TombstoneError


@pytest.fixture()
def ts_file(tmp_path: Path) -> Path:
    return tmp_path / "tombstones.json"


@pytest.fixture()
def ts(ts_file: Path) -> Tombstone:
    return Tombstone(ts_file)


def test_empty_tombstone_returns_empty_list(ts: Tombstone) -> None:
    assert ts.all() == []


def test_retire_creates_entry(ts: Tombstone) -> None:
    entry = ts.retire("etl_v1", "replaced by etl_v2")
    assert entry.job == "etl_v1"
    assert entry.reason == "replaced by etl_v2"
    assert entry.retired_at is not None


def test_retire_persists_to_disk(ts: Tombstone, ts_file: Path) -> None:
    ts.retire("job_a", "sunset")
    raw = json.loads(ts_file.read_text())
    assert len(raw) == 1
    assert raw[0]["job"] == "job_a"


def test_retire_duplicate_raises(ts: Tombstone) -> None:
    ts.retire("job_a", "reason one")
    with pytest.raises(TombstoneError, match="already retired"):
        ts.retire("job_a", "reason two")


def test_retire_empty_job_raises(ts: Tombstone) -> None:
    with pytest.raises(TombstoneError, match="job name"):
        ts.retire("", "some reason")


def test_retire_empty_reason_raises(ts: Tombstone) -> None:
    with pytest.raises(TombstoneError, match="reason"):
        ts.retire("job_x", "")


def test_is_retired_true_after_retire(ts: Tombstone) -> None:
    ts.retire("job_b", "old")
    assert ts.is_retired("job_b") is True


def test_is_retired_false_for_unknown(ts: Tombstone) -> None:
    assert ts.is_retired("ghost") is False


def test_get_returns_entry(ts: Tombstone) -> None:
    ts.retire("job_c", "deprecated", retired_by="alice", note="see ticket 42")
    entry = ts.get("job_c")
    assert entry is not None
    assert entry.retired_by == "alice"
    assert entry.note == "see ticket 42"


def test_get_missing_returns_none(ts: Tombstone) -> None:
    assert ts.get("no_such_job") is None


def test_remove_existing_returns_true(ts: Tombstone) -> None:
    ts.retire("job_d", "old")
    assert ts.remove("job_d") is True
    assert ts.is_retired("job_d") is False


def test_remove_missing_returns_false(ts: Tombstone) -> None:
    assert ts.remove("ghost") is False


def test_clear_removes_all_entries(ts: Tombstone) -> None:
    ts.retire("j1", "r1")
    ts.retire("j2", "r2")
    count = ts.clear()
    assert count == 2
    assert ts.all() == []


def test_entry_to_dict_round_trip() -> None:
    from datetime import datetime, timezone
    e = TombstoneEntry(job="x", reason="y", retired_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
                       retired_by="bob", note="hi")
    assert TombstoneEntry.from_dict(e.to_dict()).job == "x"
    assert TombstoneEntry.from_dict(e.to_dict()).retired_by == "bob"
