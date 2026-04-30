"""Tests for pipewatch.eventlog and pipewatch.cli_eventlog."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

import pytest

from pipewatch.eventlog import EventEntry, EventLog
from pipewatch.cli_eventlog import build_eventlog_parser


@pytest.fixture()
def log_file(tmp_path: Path) -> Path:
    return tmp_path / "events.json"


@pytest.fixture()
def log(log_file: Path) -> EventLog:
    return EventLog(log_file)


def _ts() -> datetime:
    return datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)


def test_empty_log_returns_empty_list(log: EventLog) -> None:
    assert log.all() == []


def test_record_and_retrieve(log: EventLog) -> None:
    log.record("etl", "started", timestamp=_ts())
    entries = log.all()
    assert len(entries) == 1
    assert entries[0].job == "etl"
    assert entries[0].event == "started"


def test_record_default_level_is_info(log: EventLog) -> None:
    log.record("etl", "done")
    assert log.all()[0].level == "info"


def test_record_invalid_level_raises(log: EventLog) -> None:
    with pytest.raises(ValueError, match="Invalid level"):
        log.record("etl", "oops", level="critical")


def test_for_job_filters_correctly(log: EventLog) -> None:
    log.record("etl", "started")
    log.record("loader", "done")
    assert len(log.for_job("etl")) == 1
    assert log.for_job("etl")[0].event == "started"


def test_by_level_filters_correctly(log: EventLog) -> None:
    log.record("etl", "warn_event", level="warning")
    log.record("etl", "info_event", level="info")
    assert len(log.by_level("warning")) == 1


def test_meta_round_trips(log: EventLog) -> None:
    log.record("etl", "step", meta={"rows": "100"})
    assert log.all()[0].meta == {"rows": "100"}


def test_clear_removes_all_entries(log: EventLog) -> None:
    log.record("etl", "started")
    log.clear()
    assert log.all() == []


def test_entry_to_dict_round_trip() -> None:
    entry = EventEntry(
        job="j", event="e", timestamp=_ts(), level="error",
        message="boom", meta={"k": "v"}
    )
    restored = EventEntry.from_dict(entry.to_dict())
    assert restored.job == entry.job
    assert restored.level == entry.level
    assert restored.meta == entry.meta


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd")
    build_eventlog_parser(sub)
    return p


def test_build_eventlog_parser_registers_subcommands() -> None:
    p = _build_parser()
    args = p.parse_args(["eventlog", "list"])
    assert args.eventlog_cmd == "list"


def test_record_subcommand_parsed(log_file: Path) -> None:
    p = _build_parser()
    args = p.parse_args(["eventlog", "--file", str(log_file), "record", "myjob", "myevent", "--level", "warning"])
    assert args.job == "myjob"
    assert args.event == "myevent"
    assert args.level == "warning"
