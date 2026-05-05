"""Unit tests for pipewatch.tracelog."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from pipewatch.tracelog import TraceEntry, TraceLog


@pytest.fixture()
def log_file(tmp_path: Path) -> Path:
    return tmp_path / "tracelog.json"


@pytest.fixture()
def log(log_file: Path) -> TraceLog:
    return TraceLog(log_file)


def _dt(iso: str) -> datetime:
    return datetime.fromisoformat(iso)


def test_empty_log_returns_empty_list(log: TraceLog) -> None:
    assert log.all() == []


def test_record_and_retrieve(log: TraceLog) -> None:
    entry = log.record("etl", "extract", status="ok")
    all_entries = log.all()
    assert len(all_entries) == 1
    assert all_entries[0].job == "etl"
    assert all_entries[0].span == "extract"
    assert all_entries[0].status == "ok"


def test_record_with_meta(log: TraceLog) -> None:
    log.record("etl", "load", meta={"rows": 42})
    e = log.all()[0]
    assert e.meta == {"rows": 42}


def test_filter_by_job(log: TraceLog) -> None:
    log.record("etl", "extract")
    log.record("report", "render")
    results = log.filter_job("etl")
    assert len(results) == 1
    assert results[0].job == "etl"


def test_filter_by_span(log: TraceLog) -> None:
    log.record("etl", "extract")
    log.record("etl", "transform")
    results = log.filter_span("transform")
    assert len(results) == 1
    assert results[0].span == "transform"


def test_clear_removes_all_entries(log: TraceLog) -> None:
    log.record("etl", "extract")
    log.clear()
    assert log.all() == []


def test_duration_seconds_with_both_timestamps() -> None:
    e = TraceEntry(
        job="j",
        span="s",
        started_at=_dt("2024-01-01T10:00:00+00:00"),
        ended_at=_dt("2024-01-01T10:00:02.500000+00:00"),
    )
    assert e.duration_seconds() == pytest.approx(2.5)


def test_duration_seconds_none_when_no_end() -> None:
    e = TraceEntry(job="j", span="s", started_at=datetime.now(timezone.utc))
    assert e.duration_seconds() is None


def test_to_dict_round_trip() -> None:
    e = TraceEntry(
        job="j",
        span="s",
        started_at=_dt("2024-03-15T12:00:00+00:00"),
        ended_at=_dt("2024-03-15T12:00:01+00:00"),
        status="error",
        meta={"key": "val"},
    )
    restored = TraceEntry.from_dict(e.to_dict())
    assert restored.job == e.job
    assert restored.span == e.span
    assert restored.status == e.status
    assert restored.meta == e.meta
    assert restored.ended_at == e.ended_at


def test_multiple_records_persist(log: TraceLog) -> None:
    log.record("a", "s1")
    log.record("b", "s2")
    log.record("c", "s3")
    assert len(log.all()) == 3
