"""Tests for pipewatch.progresslog and pipewatch.cli_progresslog."""
from __future__ import annotations

import argparse
import pytest
from pathlib import Path

from pipewatch.progresslog import ProgressEntry, ProgressLog
from pipewatch.cli_progresslog import (
    build_progress_parser,
    cmd_progress_list,
    cmd_progress_latest,
    cmd_progress_clear,
)


@pytest.fixture()
def log_file(tmp_path: Path) -> Path:
    return tmp_path / "progress.jsonl"


@pytest.fixture()
def log(log_file: Path) -> ProgressLog:
    return ProgressLog(log_file)


def test_empty_log_returns_empty_list(log: ProgressLog) -> None:
    assert log.entries() == []


def test_record_and_retrieve(log: ProgressLog) -> None:
    log.record("etl", "extract", 25.0, "reading source")
    log.record("etl", "transform", 50.0, "applying rules")
    entries = log.entries()
    assert len(entries) == 2
    assert entries[0].step == "extract"
    assert entries[1].pct == 50.0


def test_filter_by_job(log: ProgressLog) -> None:
    log.record("etl", "extract", 10.0)
    log.record("other", "load", 90.0)
    assert len(log.entries(job="etl")) == 1
    assert len(log.entries(job="other")) == 1


def test_latest_returns_last_entry(log: ProgressLog) -> None:
    log.record("etl", "extract", 10.0)
    log.record("etl", "transform", 60.0)
    e = log.latest("etl")
    assert e is not None
    assert e.step == "transform"


def test_latest_unknown_job_returns_none(log: ProgressLog) -> None:
    assert log.latest("ghost") is None


def test_invalid_pct_raises(log: ProgressLog) -> None:
    with pytest.raises(ValueError):
        log.record("etl", "step", 101.0)
    with pytest.raises(ValueError):
        log.record("etl", "step", -1.0)


def test_clear_removes_entries(log: ProgressLog) -> None:
    log.record("etl", "extract", 50.0)
    log.clear()
    assert log.entries() == []


def test_to_dict_round_trip() -> None:
    e = ProgressEntry(job="j", step="s", pct=42.5, message="ok", ts=1000.0)
    assert ProgressEntry.from_dict(e.to_dict()).pct == 42.5


def _build_parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser()
    sub = root.add_subparsers(dest="cmd")
    build_progress_parser(sub)
    return root


def test_build_progress_parser_registers_subcommands() -> None:
    p = _build_parser()
    args = p.parse_args(["progress", "clear"])
    assert args.func is cmd_progress_clear


def test_cmd_progress_list_empty(log_file: Path, capsys: pytest.CaptureFixture) -> None:
    args = argparse.Namespace(file=str(log_file), job=None, func=cmd_progress_list)
    cmd_progress_list(args)
    assert "No progress" in capsys.readouterr().out


def test_cmd_progress_latest_missing(log_file: Path, capsys: pytest.CaptureFixture) -> None:
    args = argparse.Namespace(file=str(log_file), job="missing")
    cmd_progress_latest(args)
    assert "No progress" in capsys.readouterr().out
