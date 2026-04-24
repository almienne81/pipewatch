"""Render human-readable reports from run history."""

from __future__ import annotations

from typing import List

from pipewatch.history import History, HistoryEntry


def _status_symbol(entry: HistoryEntry) -> str:
    return "\u2705" if entry.succeeded else "\u274c"


def format_entry(entry: HistoryEntry) -> str:
    status = _status_symbol(entry)
    return (
        f"{status} [{entry.timestamp}] "
        f"exit={entry.exit_code} "
        f"duration={entry.duration_seconds}s "
        f"cmd={entry.command!r}"
    )


def format_summary(entries: List[HistoryEntry]) -> str:
    if not entries:
        return "No history recorded yet."

    total = len(entries)
    passed = sum(1 for e in entries if e.succeeded)
    failed = total - passed
    lines = [f"Run history ({total} total, {passed} succeeded, {failed} failed):"]
    lines.extend(format_entry(e) for e in entries)
    return "\n".join(lines)


def print_history(n: int = 20, history_path=None) -> None:
    history = History(history_path)
    entries = history.last(n)
    print(format_summary(entries))


def last_failed(history_path=None) -> List[HistoryEntry]:
    """Return all entries from the most recent contiguous failure streak."""
    history = History(history_path)
    entries = list(reversed(history.all()))
    streak: List[HistoryEntry] = []
    for entry in entries:
        if entry.succeeded:
            break
        streak.append(entry)
    return list(reversed(streak))
