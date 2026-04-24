"""Tests for pipewatch.history module."""

import json
from pathlib import Path

import pytest

from pipewatch.history import History, HistoryEntry, record_run


@pytest.fixture
def history_file(tmp_path) -> Path:
    return tmp_path / "history.json"


@pytest.fixture
def history(history_file) -> History:
    return History(history_file)


def _entry(command="echo hi", exit_code=0, duration=1.5) -> HistoryEntry:
    return HistoryEntry(
        command=command,
        exit_code=exit_code,
        duration_seconds=duration,
        timestamp="2024-01-01T00:00:00",
        stdout_tail="output",
        stderr_tail="",
    )


def test_empty_history_returns_empty_list(history):
    assert history.all() == []


def test_append_and_retrieve(history):
    entry = _entry()
    history.append(entry)
    results = history.all()
    assert len(results) == 1
    assert results[0].command == "echo hi"
    assert results[0].exit_code == 0


def test_multiple_entries_preserved(history):
    for i in range(3):
        history.append(_entry(command=f"cmd{i}", exit_code=i))
    results = history.all()
    assert len(results) == 3
    assert [r.command for r in results] == ["cmd0", "cmd1", "cmd2"]


def test_last_returns_most_recent(history):
    for i in range(5):
        history.append(_entry(command=f"cmd{i}"))
    last = history.last(3)
    assert len(last) == 3
    assert last[-1].command == "cmd4"


def test_clear_removes_all_entries(history):
    history.append(_entry())
    history.clear()
    assert history.all() == []


def test_succeeded_property():
    assert _entry(exit_code=0).succeeded is True
    assert _entry(exit_code=1).succeeded is False


def test_record_run_writes_entry(history_file):
    entry = record_run(
        command="python pipeline.py",
        exit_code=0,
        duration_seconds=12.345,
        stdout_tail="done",
        history_path=history_file,
    )
    assert entry.command == "python pipeline.py"
    assert entry.exit_code == 0
    assert entry.duration_seconds == 12.345
    stored = History(history_file).all()
    assert len(stored) == 1
    assert stored[0].stdout_tail == "done"


def test_history_file_created_if_missing(tmp_path):
    nested = tmp_path / "a" / "b" / "history.json"
    h = History(nested)
    h.append(_entry())
    assert nested.exists()
