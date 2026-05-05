"""Integration tests for TraceLog across multiple operations."""
from __future__ import annotations

from pathlib import Path

import pytest

from pipewatch.tracelog import TraceLog


@pytest.fixture()
def log(tmp_path: Path) -> TraceLog:
    return TraceLog(tmp_path / "tracelog.json")


def test_state_persists_across_instances(tmp_path: Path) -> None:
    path = tmp_path / "tl.json"
    TraceLog(path).record("job", "span-a", status="ok")
    loaded = TraceLog(path).all()
    assert len(loaded) == 1
    assert loaded[0].span == "span-a"


def test_multiple_jobs_are_independent(log: TraceLog) -> None:
    log.record("job-a", "fetch")
    log.record("job-b", "fetch")
    log.record("job-a", "store")
    assert len(log.filter_job("job-a")) == 2
    assert len(log.filter_job("job-b")) == 1


def test_clear_then_rerecord(log: TraceLog) -> None:
    log.record("j", "s")
    log.clear()
    log.record("j", "s2")
    entries = log.all()
    assert len(entries) == 1
    assert entries[0].span == "s2"


def test_status_error_is_preserved(log: TraceLog) -> None:
    log.record("j", "s", status="error", meta={"reason": "timeout"})
    e = log.all()[0]
    assert e.status == "error"
    assert e.meta["reason"] == "timeout"


def test_duration_is_non_negative(log: TraceLog) -> None:
    log.record("j", "s")
    dur = log.all()[0].duration_seconds()
    assert dur is not None
    assert dur >= 0.0
