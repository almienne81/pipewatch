"""Tests for pipewatch.watermark."""

from __future__ import annotations

import pytest
from pathlib import Path

from pipewatch.watermark import Watermark, WatermarkEntry, WatermarkError


@pytest.fixture()
def wm_file(tmp_path: Path) -> Path:
    return tmp_path / "watermarks.json"


@pytest.fixture()
def wm(wm_file: Path) -> Watermark:
    return Watermark(wm_file)


def test_empty_watermark_returns_empty_list(wm: Watermark) -> None:
    assert wm.all() == []


def test_get_missing_returns_none(wm: Watermark) -> None:
    assert wm.get("job1", "rows") is None


def test_update_sets_initial_value(wm: Watermark) -> None:
    entry = wm.update("job1", "rows", 100.0)
    assert entry.value == 100.0
    assert entry.job == "job1"
    assert entry.key == "rows"


def test_update_replaces_lower_value(wm: Watermark) -> None:
    wm.update("job1", "rows", 50.0)
    entry = wm.update("job1", "rows", 200.0)
    assert entry.value == 200.0


def test_update_keeps_higher_existing_value(wm: Watermark) -> None:
    wm.update("job1", "rows", 200.0)
    entry = wm.update("job1", "rows", 100.0)
    assert entry.value == 200.0


def test_get_returns_stored_entry(wm: Watermark) -> None:
    wm.update("job1", "rows", 42.0)
    entry = wm.get("job1", "rows")
    assert entry is not None
    assert entry.value == 42.0


def test_persists_across_instances(wm_file: Path) -> None:
    Watermark(wm_file).update("job1", "rows", 99.0)
    reloaded = Watermark(wm_file)
    entry = reloaded.get("job1", "rows")
    assert entry is not None
    assert entry.value == 99.0


def test_different_keys_are_independent(wm: Watermark) -> None:
    wm.update("job1", "rows", 10.0)
    wm.update("job1", "bytes", 999.0)
    assert wm.get("job1", "rows").value == 10.0
    assert wm.get("job1", "bytes").value == 999.0


def test_clear_removes_entry(wm: Watermark) -> None:
    wm.update("job1", "rows", 10.0)
    wm.clear("job1", "rows")
    assert wm.get("job1", "rows") is None


def test_clear_all_removes_all_entries(wm: Watermark) -> None:
    wm.update("job1", "rows", 1.0)
    wm.update("job2", "bytes", 2.0)
    wm.clear_all()
    assert wm.all() == []


def test_empty_job_raises(wm: Watermark) -> None:
    with pytest.raises(WatermarkError, match="job"):
        wm.update("", "rows", 1.0)


def test_empty_key_raises(wm: Watermark) -> None:
    with pytest.raises(WatermarkError, match="key"):
        wm.update("job1", "", 1.0)


def test_entry_to_dict_round_trip() -> None:
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    e = WatermarkEntry(job="j", key="k", value=3.14, recorded_at=now)
    restored = WatermarkEntry.from_dict(e.to_dict())
    assert restored.job == e.job
    assert restored.key == e.key
    assert abs(restored.value - e.value) < 1e-9
