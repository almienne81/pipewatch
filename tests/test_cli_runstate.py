"""Tests for pipewatch.cli_runstate."""

from __future__ import annotations

import argparse
import os
from datetime import datetime, timezone
from pathlib import Path

import pytest

from pipewatch.runstate import RunState, RunStateStore
from pipewatch.cli_runstate import (
    build_runstate_parser,
    cmd_runstate_clear,
    cmd_runstate_show,
    cmd_runstate_status,
)


@pytest.fixture
def state_file(tmp_path: Path) -> Path:
    return tmp_path / "runstate.json"


def _make_args(state_file: Path, runstate_cmd: str = "show") -> argparse.Namespace:
    return argparse.Namespace(state_file=str(state_file), runstate_cmd=runstate_cmd)


def _save(state_file: Path, **kwargs) -> None:
    defaults = dict(
        job="etl",
        pid=os.getpid(),
        started_at=datetime(2024, 6, 1, 8, 0, 0, tzinfo=timezone.utc),
        status="running",
        note="",
    )
    defaults.update(kwargs)
    RunStateStore(state_file).save(RunState(**defaults))


def test_build_runstate_parser_registers_subcommands():
    root = argparse.ArgumentParser()
    subs = root.add_subparsers()
    build_runstate_parser(subs)
    ns = root.parse_args(["runstate", "show"])
    assert ns.runstate_cmd == "show"


def test_show_no_state(state_file: Path, capsys):
    cmd_runstate_show(_make_args(state_file))
    out = capsys.readouterr().out
    assert "No run state found" in out


def test_show_with_state(state_file: Path, capsys):
    _save(state_file, job="loader", note="nightly")
    cmd_runstate_show(_make_args(state_file))
    out = capsys.readouterr().out
    assert "loader" in out
    assert "nightly" in out


def test_status_running(state_file: Path, capsys):
    _save(state_file, pid=os.getpid(), status="running")
    cmd_runstate_status(_make_args(state_file, "status"))
    out = capsys.readouterr().out
    assert "RUNNING" in out


def test_status_not_running(state_file: Path, capsys):
    cmd_runstate_status(_make_args(state_file, "status"))
    out = capsys.readouterr().out
    assert "NOT RUNNING" in out


def test_clear_removes_state(state_file: Path, capsys):
    _save(state_file)
    assert state_file.exists()
    cmd_runstate_clear(_make_args(state_file, "clear"))
    assert not state_file.exists()
    out = capsys.readouterr().out
    assert "cleared" in out.lower()
