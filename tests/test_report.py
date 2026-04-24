"""Tests for pipewatch.report module."""

from pipewatch.history import HistoryEntry
from pipewatch.report import format_entry, format_summary, last_failed


def _entry(command="cmd", exit_code=0, duration=1.0, ts="2024-06-01T12:00:00"):
    return HistoryEntry(
        command=command,
        exit_code=exit_code,
        duration_seconds=duration,
        timestamp=ts,
        stdout_tail="",
        stderr_tail="",
    )


def test_format_entry_success():
    line = format_entry(_entry(exit_code=0))
    assert "\u2705" in line
    assert "exit=0" in line
    assert "cmd" in line


def test_format_entry_failure():
    line = format_entry(_entry(exit_code=1))
    assert "\u274c" in line
    assert "exit=1" in line


def test_format_summary_empty():
    result = format_summary([])
    assert "No history" in result


def test_format_summary_counts():
    entries = [
        _entry(exit_code=0),
        _entry(exit_code=0),
        _entry(exit_code=1),
    ]
    result = format_summary(entries)
    assert "3 total" in result
    assert "2 succeeded" in result
    assert "1 failed" in result


def test_last_failed_empty(tmp_path):
    from pipewatch.history import History
    hp = tmp_path / "h.json"
    History(hp).clear()
    result = last_failed(history_path=hp)
    assert result == []


def test_last_failed_returns_streak(tmp_path):
    from pipewatch.history import History
    hp = tmp_path / "h.json"
    h = History(hp)
    h.append(_entry(command="ok", exit_code=0, ts="2024-01-01T00:00:00"))
    h.append(_entry(command="fail1", exit_code=1, ts="2024-01-02T00:00:00"))
    h.append(_entry(command="fail2", exit_code=2, ts="2024-01-03T00:00:00"))
    streak = last_failed(history_path=hp)
    assert len(streak) == 2
    assert streak[0].command == "fail1"
    assert streak[1].command == "fail2"


def test_last_failed_stops_at_success(tmp_path):
    from pipewatch.history import History
    hp = tmp_path / "h.json"
    h = History(hp)
    h.append(_entry(command="fail", exit_code=1, ts="2024-01-01T00:00:00"))
    h.append(_entry(command="ok", exit_code=0, ts="2024-01-02T00:00:00"))
    streak = last_failed(history_path=hp)
    assert streak == []
