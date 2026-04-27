"""Tests for pipewatch.runlog and pipewatch.cli_runlog."""
from __future__ import annotations

import time
from pathlib import Path

import pytest

from pipewatch.runlog import RunLog, RunLogEntry


@pytest.fixture()
def log_file(tmp_path: Path) -> Path:
    return tmp_path / "runlog.json"


@pytest.fixture()
def log(log_file: Path) -> RunLog:
    return RunLog(log_file)


def _entry(
    run_id: str = "abc123",
    command: str = "echo hi",
    exit_code: int = 0,
    stdout: str = "",
    stderr: str = "",
    tags: dict | None = None,
) -> RunLogEntry:
    now = time.time()
    return RunLogEntry(
        run_id=run_id,
        command=command,
        started_at=now - 1.5,
        finished_at=now,
        exit_code=exit_code,
        stdout=stdout,
        stderr=stderr,
        tags=tags or {},
    )


def test_empty_log_returns_empty_list(log: RunLog) -> None:
    assert log.all() == []


def test_append_and_retrieve(log: RunLog) -> None:
    e = _entry(run_id="run1")
    log.append(e)
    entries = log.all()
    assert len(entries) == 1
    assert entries[0].run_id == "run1"


def test_last_returns_most_recent(log: RunLog) -> None:
    log.append(_entry(run_id="first"))
    log.append(_entry(run_id="second"))
    assert log.last().run_id == "second"


def test_last_on_empty_returns_none(log: RunLog) -> None:
    assert log.last() is None


def test_get_by_run_id(log: RunLog) -> None:
    log.append(_entry(run_id="xyz"))
    found = log.get("xyz")
    assert found is not None
    assert found.run_id == "xyz"


def test_get_missing_returns_none(log: RunLog) -> None:
    assert log.get("nope") is None


def test_clear_removes_all_entries(log: RunLog) -> None:
    log.append(_entry())
    log.clear()
    assert log.all() == []


def test_succeeded_true_on_zero_exit(log: RunLog) -> None:
    e = _entry(exit_code=0)
    assert e.succeeded is True


def test_succeeded_false_on_nonzero_exit(log: RunLog) -> None:
    e = _entry(exit_code=1)
    assert e.succeeded is False


def test_duration_seconds(log: RunLog) -> None:
    e = _entry()
    assert e.duration_seconds is not None
    assert e.duration_seconds == pytest.approx(1.5, abs=0.1)


def test_round_trip_via_dict() -> None:
    e = _entry(run_id="rt", command="ls", tags={"env": "prod"})
    restored = RunLogEntry.from_dict(e.to_dict())
    assert restored.run_id == e.run_id
    assert restored.command == e.command
    assert restored.tags == {"env": "prod"}


def test_persists_across_instances(log_file: Path) -> None:
    RunLog(log_file).append(_entry(run_id="persist"))
    entries = RunLog(log_file).all()
    assert entries[0].run_id == "persist"
