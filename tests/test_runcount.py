"""Tests for pipewatch.runcount."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from pipewatch.runcount import RunCount, RunCountEntry, RunCountError


@pytest.fixture()
def rc_file(tmp_path: Path) -> Path:
    return tmp_path / "runcount.json"


@pytest.fixture()
def rc(rc_file: Path) -> RunCount:
    return RunCount(rc_file)


def test_empty_returns_empty_list(rc: RunCount) -> None:
    assert rc.all() == []


def test_get_missing_returns_none(rc: RunCount) -> None:
    assert rc.get("myjob") is None


def test_record_success_increments_correctly(rc: RunCount) -> None:
    entry = rc.record("job-a", success=True)
    assert entry.total == 1
    assert entry.successes == 1
    assert entry.failures == 0


def test_record_failure_increments_correctly(rc: RunCount) -> None:
    entry = rc.record("job-a", success=False)
    assert entry.total == 1
    assert entry.successes == 0
    assert entry.failures == 1


def test_multiple_records_accumulate(rc: RunCount) -> None:
    rc.record("job-b", success=True)
    rc.record("job-b", success=True)
    rc.record("job-b", success=False)
    entry = rc.get("job-b")
    assert entry is not None
    assert entry.total == 3
    assert entry.successes == 2
    assert entry.failures == 1


def test_success_rate_none_when_no_runs() -> None:
    e = RunCountEntry(job="x", total=0, successes=0, failures=0)
    assert e.success_rate is None


def test_success_rate_calculated_correctly(rc: RunCount) -> None:
    rc.record("job-c", success=True)
    rc.record("job-c", success=True)
    rc.record("job-c", success=False)
    entry = rc.get("job-c")
    assert entry is not None
    assert abs(entry.success_rate - 2 / 3) < 1e-9


def test_persists_to_disk(rc_file: Path) -> None:
    rc1 = RunCount(rc_file)
    rc1.record("job-d", success=True)
    rc2 = RunCount(rc_file)
    entry = rc2.get("job-d")
    assert entry is not None
    assert entry.total == 1


def test_reset_removes_entry(rc: RunCount) -> None:
    rc.record("job-e", success=True)
    rc.reset("job-e")
    assert rc.get("job-e") is None


def test_reset_missing_job_is_noop(rc: RunCount) -> None:
    rc.reset("nonexistent")  # should not raise


def test_empty_job_name_raises(rc: RunCount) -> None:
    with pytest.raises(RunCountError):
        rc.record("", success=True)


def test_to_dict_round_trip() -> None:
    e = RunCountEntry(job="z", total=5, successes=3, failures=2)
    restored = RunCountEntry.from_dict(e.to_dict())
    assert restored.job == e.job
    assert restored.total == e.total
    assert restored.successes == e.successes
    assert restored.failures == e.failures


def test_all_returns_all_jobs(rc: RunCount) -> None:
    rc.record("alpha", success=True)
    rc.record("beta", success=False)
    jobs = {e.job for e in rc.all()}
    assert jobs == {"alpha", "beta"}
