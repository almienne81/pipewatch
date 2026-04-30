"""Tests for pipewatch.steplog."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from pipewatch.steplog import StepEntry, StepLog, from_dict, to_dict


def _dt(ts: str) -> datetime:
    return datetime.fromisoformat(ts)


@pytest.fixture()
def log_file(tmp_path: Path) -> Path:
    return tmp_path / "steplog.json"


@pytest.fixture()
def log(log_file: Path) -> StepLog:
    return StepLog(log_file)


def _entry(**kwargs) -> StepEntry:
    defaults = dict(
        job="etl",
        step="extract",
        status="ok",
        started_at=_dt("2024-01-01T10:00:00+00:00"),
        ended_at=_dt("2024-01-01T10:00:05+00:00"),
    )
    defaults.update(kwargs)
    return StepEntry(**defaults)


def test_empty_log_returns_empty_list(log: StepLog) -> None:
    assert log.all() == []


def test_record_and_retrieve(log: StepLog) -> None:
    log.record("etl", "extract", "ok", note="all good")
    entries = log.all()
    assert len(entries) == 1
    assert entries[0].job == "etl"
    assert entries[0].step == "extract"
    assert entries[0].status == "ok"
    assert entries[0].note == "all good"


def test_for_job_filters_correctly(log: StepLog) -> None:
    log.record("etl", "extract", "ok")
    log.record("etl", "load", "fail")
    log.record("other", "run", "ok")
    assert len(log.for_job("etl")) == 2
    assert len(log.for_job("other")) == 1
    assert log.for_job("missing") == []


def test_latest_returns_most_recent(log: StepLog) -> None:
    log.record("etl", "extract", "fail")
    log.record("etl", "extract", "ok")
    entry = log.latest("etl", "extract")
    assert entry is not None
    assert entry.status == "ok"


def test_latest_missing_returns_none(log: StepLog) -> None:
    assert log.latest("etl", "ghost") is None


def test_clear_removes_all_entries(log: StepLog) -> None:
    log.record("etl", "extract", "ok")
    log.clear()
    assert log.all() == []


def test_duration_seconds(log: StepLog) -> None:
    e = log.record(
        "etl",
        "load",
        "ok",
        started_at=_dt("2024-01-01T10:00:00+00:00"),
        ended_at=_dt("2024-01-01T10:00:07+00:00"),
    )
    assert e.duration_seconds() == pytest.approx(7.0)


def test_to_dict_round_trip() -> None:
    e = _entry(note="hi", meta={"rows": 42})
    d = to_dict(e)
    e2 = from_dict(d)
    assert e2.job == e.job
    assert e2.step == e.step
    assert e2.status == e.status
    assert e2.note == e.note
    assert e2.meta == e.meta


def test_succeeded_true_for_ok() -> None:
    assert _entry(status="ok").succeeded() is True


def test_succeeded_false_for_fail() -> None:
    assert _entry(status="fail").succeeded() is False


def test_meta_persists(log: StepLog) -> None:
    log.record("etl", "transform", "ok", meta={"rows": 100})
    entry = log.latest("etl", "transform")
    assert entry is not None
    assert entry.meta == {"rows": 100}
