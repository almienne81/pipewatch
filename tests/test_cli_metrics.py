"""Tests for pipewatch.cli_metrics."""
import argparse
import json
import time
from pathlib import Path

import pytest

from pipewatch.cli_metrics import build_metrics_parser, cmd_metrics_last, cmd_metrics_summary
from pipewatch.history import History, HistoryEntry


@pytest.fixture()
def history_file(tmp_path: Path) -> Path:
    return tmp_path / "history.json"


def _make_entry(command: str, exit_code: int, elapsed: float) -> HistoryEntry:
    now = time.time()
    entry = HistoryEntry(
        command=command,
        exit_code=exit_code,
        timestamp=now,
        stdout="line1\nline2\n",
        stderr="",
    )
    # Inject serialised metrics directly into the dict representation
    raw = entry.to_dict()
    raw["metrics"] = {
        "start_time": now - elapsed,
        "end_time": now,
        "elapsed_seconds": elapsed,
        "peak_memory_mb": None,
        "exit_code": exit_code,
        "stdout_lines": 2,
        "stderr_lines": 0,
    }
    return entry  # tests use History directly; metrics stored via history file


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd")
    build_metrics_parser(sub)
    return p


def test_build_metrics_parser_registers_subcommands():
    p = _build_parser()
    args = p.parse_args(["metrics", "last"])
    assert args.func == cmd_metrics_last


def test_build_metrics_parser_summary_subcommand():
    p = _build_parser()
    args = p.parse_args(["metrics", "summary"])
    assert args.func == cmd_metrics_summary


def test_cmd_metrics_last_no_history_exits(history_file, capsys):
    p = _build_parser()
    args = p.parse_args(["metrics", "--history-file", str(history_file), "last"])
    with pytest.raises(SystemExit) as exc:
        cmd_metrics_last(args)
    assert exc.value.code == 1
    captured = capsys.readouterr()
    assert "No history" in captured.err


def test_cmd_metrics_summary_empty(history_file, capsys):
    p = _build_parser()
    args = p.parse_args(["metrics", "--history-file", str(history_file), "summary"])
    cmd_metrics_summary(args)
    captured = capsys.readouterr()
    assert "No metrics" in captured.out
