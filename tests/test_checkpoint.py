"""Unit tests for pipewatch.checkpoint."""

from __future__ import annotations

import pytest
from pathlib import Path

from pipewatch.checkpoint import Checkpoint, CheckpointEntry


@pytest.fixture()
def cp_file(tmp_path: Path) -> Path:
    return tmp_path / "checkpoints.json"


@pytest.fixture()
def cp(cp_file: Path) -> Checkpoint:
    return Checkpoint(cp_file)


def test_empty_checkpoint_returns_empty_list(cp: Checkpoint) -> None:
    assert cp.all() == []


def test_mark_ok_records_entry(cp: Checkpoint) -> None:
    entry = cp.mark("extract", "ok")
    assert entry.stage == "extract"
    assert entry.status == "ok"
    assert len(cp.all()) == 1


def test_mark_persists_to_disk(cp_file: Path) -> None:
    cp = Checkpoint(cp_file)
    cp.mark("load", "ok", message="rows=1000")
    cp2 = Checkpoint(cp_file)
    assert len(cp2.all()) == 1
    assert cp2.all()[0].message == "rows=1000"


def test_last_returns_most_recent(cp: Checkpoint) -> None:
    cp.mark("transform", "failed", message="first")
    cp.mark("transform", "ok", message="second")
    entry = cp.last("transform")
    assert entry is not None
    assert entry.message == "second"


def test_last_returns_none_for_unknown_stage(cp: Checkpoint) -> None:
    assert cp.last("nonexistent") is None


def test_stages_returns_unique_ordered_names(cp: Checkpoint) -> None:
    cp.mark("extract", "ok")
    cp.mark("transform", "ok")
    cp.mark("extract", "ok")
    assert cp.stages() == ["extract", "transform"]


def test_invalid_status_raises(cp: Checkpoint) -> None:
    with pytest.raises(ValueError, match="Invalid status"):
        cp.mark("extract", "bad_status")


def test_clear_removes_entries_and_file(cp: Checkpoint, cp_file: Path) -> None:
    cp.mark("extract", "ok")
    cp.clear()
    assert cp.all() == []
    assert not cp_file.exists()


def test_entry_roundtrip() -> None:
    e = CheckpointEntry(stage="load", status="skipped", timestamp=1234.5, message="dry-run")
    assert CheckpointEntry.from_dict(e.to_dict()) == e


def test_multiple_stages_all_returned(cp: Checkpoint) -> None:
    for stage, status in [("extract", "ok"), ("transform", "failed"), ("load", "skipped")]:
        cp.mark(stage, status)
    assert len(cp.all()) == 3
