"""Tests for pipewatch.cli_tracelog."""
from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from pipewatch.cli_tracelog import (
    build_tracelog_parser,
    cmd_tracelog_clear,
    cmd_tracelog_list,
    cmd_tracelog_stats,
)
from pipewatch.tracelog import TraceLog


@pytest.fixture()
def log_file(tmp_path: Path) -> Path:
    return tmp_path / "tracelog.json"


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd")
    build_tracelog_parser(sub)
    return p


def _parse(args_list: list[str]) -> argparse.Namespace:
    return _build_parser().parse_args(args_list)


def test_build_tracelog_parser_registers_subcommands() -> None:
    p = _build_parser()
    assert p is not None


def test_list_empty(log_file: Path, capsys: pytest.CaptureFixture) -> None:
    args = argparse.Namespace(file=str(log_file), job=None, span=None)
    cmd_tracelog_list(args)
    out = capsys.readouterr().out
    assert "No trace entries" in out


def test_list_shows_entries(log_file: Path, capsys: pytest.CaptureFixture) -> None:
    log = TraceLog(log_file)
    log.record("myjob", "myspan", status="ok")
    args = argparse.Namespace(file=str(log_file), job=None, span=None)
    cmd_tracelog_list(args)
    out = capsys.readouterr().out
    assert "myjob" in out
    assert "myspan" in out


def test_list_filter_by_job(log_file: Path, capsys: pytest.CaptureFixture) -> None:
    log = TraceLog(log_file)
    log.record("alpha", "s1")
    log.record("beta", "s2")
    args = argparse.Namespace(file=str(log_file), job="alpha", span=None)
    cmd_tracelog_list(args)
    out = capsys.readouterr().out
    assert "alpha" in out
    assert "beta" not in out


def test_clear_removes_entries(log_file: Path, capsys: pytest.CaptureFixture) -> None:
    log = TraceLog(log_file)
    log.record("j", "s")
    args = argparse.Namespace(file=str(log_file))
    cmd_tracelog_clear(args)
    assert log.all() == []
    out = capsys.readouterr().out
    assert "cleared" in out.lower()


def test_stats_empty(log_file: Path, capsys: pytest.CaptureFixture) -> None:
    args = argparse.Namespace(file=str(log_file))
    cmd_tracelog_stats(args)
    out = capsys.readouterr().out
    assert "Total spans" in out
    assert "0" in out


def test_stats_counts_correctly(log_file: Path, capsys: pytest.CaptureFixture) -> None:
    log = TraceLog(log_file)
    log.record("j", "s1", status="ok")
    log.record("j", "s2", status="error")
    args = argparse.Namespace(file=str(log_file))
    cmd_tracelog_stats(args)
    out = capsys.readouterr().out
    assert "OK          : 1" in out
    assert "Failed      : 1" in out
