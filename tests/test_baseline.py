"""Tests for pipewatch.baseline."""

import pytest
from pathlib import Path

from pipewatch.baseline import Baseline, BaselineEntry, BaselineError


@pytest.fixture
def bl_file(tmp_path: Path) -> Path:
    return tmp_path / "baseline.json"


@pytest.fixture
def bl(bl_file: Path) -> Baseline:
    return Baseline(bl_file)


def test_empty_baseline_returns_empty_list(bl: Baseline) -> None:
    assert bl.all_entries() == []


def test_get_missing_returns_none(bl: Baseline) -> None:
    assert bl.get("job1", "duration") is None


def test_set_returns_entry(bl: Baseline) -> None:
    entry = bl.set("job1", "duration", 42.0)
    assert isinstance(entry, BaselineEntry)
    assert entry.job == "job1"
    assert entry.metric == "duration"
    assert entry.value == 42.0


def test_set_and_get_round_trip(bl: Baseline) -> None:
    bl.set("etl", "rows", 1000.0)
    result = bl.get("etl", "rows")
    assert result is not None
    assert result.value == 1000.0


def test_set_empty_job_raises(bl: Baseline) -> None:
    with pytest.raises(BaselineError, match="job"):
        bl.set("", "duration", 1.0)


def test_set_empty_metric_raises(bl: Baseline) -> None:
    with pytest.raises(BaselineError, match="metric"):
        bl.set("job1", "", 1.0)


def test_persists_across_instances(bl_file: Path) -> None:
    Baseline(bl_file).set("job1", "latency", 5.5)
    result = Baseline(bl_file).get("job1", "latency")
    assert result is not None
    assert result.value == 5.5


def test_compare_returns_none_when_no_baseline(bl: Baseline) -> None:
    assert bl.compare("job1", "duration", 100.0) is None


def test_compare_positive_deviation(bl: Baseline) -> None:
    bl.set("job1", "duration", 100.0)
    deviation = bl.compare("job1", "duration", 120.0)
    assert deviation == pytest.approx(20.0)


def test_compare_negative_deviation(bl: Baseline) -> None:
    bl.set("job1", "duration", 100.0)
    deviation = bl.compare("job1", "duration", 80.0)
    assert deviation == pytest.approx(-20.0)


def test_compare_zero_baseline_returns_none(bl: Baseline) -> None:
    bl.set("job1", "duration", 0.0)
    assert bl.compare("job1", "duration", 5.0) is None


def test_clear_removes_job(bl: Baseline) -> None:
    bl.set("job1", "duration", 10.0)
    bl.clear("job1")
    assert bl.get("job1", "duration") is None


def test_clear_missing_job_is_noop(bl: Baseline) -> None:
    bl.clear("nonexistent")  # should not raise


def test_all_entries_returns_all(bl: Baseline) -> None:
    bl.set("job1", "duration", 1.0)
    bl.set("job1", "rows", 2.0)
    bl.set("job2", "latency", 3.0)
    entries = bl.all_entries()
    assert len(entries) == 3
    jobs = {e.job for e in entries}
    assert jobs == {"job1", "job2"}


def test_entry_to_dict_round_trip() -> None:
    e = BaselineEntry(job="j", metric="m", value=9.9)
    assert BaselineEntry.from_dict(e.to_dict()) == e


def test_overwrite_existing_baseline(bl: Baseline) -> None:
    bl.set("job1", "duration", 50.0)
    bl.set("job1", "duration", 75.0)
    result = bl.get("job1", "duration")
    assert result is not None
    assert result.value == 75.0
