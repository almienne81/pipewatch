"""Tests for pipewatch.peaktracker."""
import pytest
from pathlib import Path

from pipewatch.peaktracker import PeakEntry, PeakTracker, PeakTrackerError


@pytest.fixture()
def peaks_file(tmp_path: Path) -> Path:
    return tmp_path / "peaks.json"


@pytest.fixture()
def tracker(peaks_file: Path) -> PeakTracker:
    return PeakTracker(peaks_file)


# ---------------------------------------------------------------------------
# PeakEntry serialisation
# ---------------------------------------------------------------------------

def test_entry_to_dict_round_trip():
    entry = PeakEntry(job="etl", metric="rows", min_value=10.0, max_value=500.0, sample_count=5)
    assert PeakEntry.from_dict(entry.to_dict()) == entry


# ---------------------------------------------------------------------------
# Basic recording
# ---------------------------------------------------------------------------

def test_get_missing_returns_none(tracker: PeakTracker):
    assert tracker.get("etl", "rows") is None


def test_first_record_sets_min_and_max(tracker: PeakTracker):
    entry = tracker.record("etl", "rows", 42.0)
    assert entry.min_value == 42.0
    assert entry.max_value == 42.0
    assert entry.sample_count == 1


def test_second_record_updates_max(tracker: PeakTracker):
    tracker.record("etl", "rows", 10.0)
    entry = tracker.record("etl", "rows", 99.0)
    assert entry.max_value == 99.0
    assert entry.min_value == 10.0
    assert entry.sample_count == 2


def test_second_record_updates_min(tracker: PeakTracker):
    tracker.record("etl", "rows", 50.0)
    entry = tracker.record("etl", "rows", 3.0)
    assert entry.min_value == 3.0
    assert entry.max_value == 50.0


def test_sample_count_increments(tracker: PeakTracker):
    for i in range(5):
        tracker.record("etl", "rows", float(i))
    assert tracker.get("etl", "rows").sample_count == 5


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def test_empty_job_raises(tracker: PeakTracker):
    with pytest.raises(PeakTrackerError):
        tracker.record("", "rows", 1.0)


def test_empty_metric_raises(tracker: PeakTracker):
    with pytest.raises(PeakTrackerError):
        tracker.record("etl", "", 1.0)


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

def test_state_persists_across_instances(peaks_file: Path):
    t1 = PeakTracker(peaks_file)
    t1.record("etl", "rows", 100.0)
    t2 = PeakTracker(peaks_file)
    entry = t2.get("etl", "rows")
    assert entry is not None
    assert entry.max_value == 100.0


# ---------------------------------------------------------------------------
# Multiple jobs / metrics
# ---------------------------------------------------------------------------

def test_different_metrics_are_independent(tracker: PeakTracker):
    tracker.record("etl", "rows", 1.0)
    tracker.record("etl", "duration", 999.0)
    assert tracker.get("etl", "rows").max_value == 1.0
    assert tracker.get("etl", "duration").max_value == 999.0


def test_all_entries_sorted(tracker: PeakTracker):
    tracker.record("z_job", "rows", 1.0)
    tracker.record("a_job", "rows", 2.0)
    tracker.record("a_job", "bytes", 3.0)
    entries = tracker.all_entries()
    keys = [(e.job, e.metric) for e in entries]
    assert keys == sorted(keys)


# ---------------------------------------------------------------------------
# Reset
# ---------------------------------------------------------------------------

def test_reset_removes_entry(tracker: PeakTracker):
    tracker.record("etl", "rows", 5.0)
    tracker.reset("etl", "rows")
    assert tracker.get("etl", "rows") is None


def test_reset_missing_key_is_noop(tracker: PeakTracker):
    tracker.reset("nonexistent", "metric")  # should not raise
