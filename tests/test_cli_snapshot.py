"""Tests for pipewatch.cli_snapshot."""

from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from pipewatch.cli_snapshot import build_snapshot_parser, cmd_snapshot_clear, cmd_snapshot_get, cmd_snapshot_show
from pipewatch.snapshot import Snapshot


@pytest.fixture
def snap_file(tmp_path: Path) -> Path:
    return tmp_path / "snapshot.json"


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd")
    build_snapshot_parser(sub)
    return p


def _parse(args: list) -> argparse.Namespace:
    return _build_parser().parse_args(args)


def test_build_snapshot_parser_registers_subcommands() -> None:
    p = _build_parser()
    ns = p.parse_args(["snapshot", "show"])
    assert ns.snapshot_cmd == "show"


def test_show_empty(snap_file: Path, capsys) -> None:
    args = argparse.Namespace(file=str(snap_file), snapshot_cmd="show", func=cmd_snapshot_show)
    cmd_snapshot_show(args)
    out = capsys.readouterr().out
    assert "No snapshots" in out


def test_show_with_entries(snap_file: Path, capsys) -> None:
    Snapshot(snap_file).capture("myjob", "ok", exit_code=0, note="done")
    args = argparse.Namespace(file=str(snap_file), snapshot_cmd="show", func=cmd_snapshot_show)
    cmd_snapshot_show(args)
    out = capsys.readouterr().out
    assert "myjob" in out
    assert "OK" in out


def test_get_missing_job(snap_file: Path, capsys) -> None:
    args = argparse.Namespace(file=str(snap_file), job="ghost", func=cmd_snapshot_get)
    cmd_snapshot_get(args)
    out = capsys.readouterr().out
    assert "No snapshot found" in out


def test_get_existing_job(snap_file: Path, capsys) -> None:
    Snapshot(snap_file).capture("etl", "fail", exit_code=1, tags={"env": "staging"})
    args = argparse.Namespace(file=str(snap_file), job="etl", func=cmd_snapshot_get)
    cmd_snapshot_get(args)
    out = capsys.readouterr().out
    assert "fail" in out
    assert "1" in out


def test_clear_specific_job(snap_file: Path, capsys) -> None:
    s = Snapshot(snap_file)
    s.capture("a", "ok")
    s.capture("b", "ok")
    args = argparse.Namespace(file=str(snap_file), job="a", func=cmd_snapshot_clear)
    cmd_snapshot_clear(args)
    out = capsys.readouterr().out
    assert "a" in out
    assert Snapshot(snap_file).get("a") is None
    assert Snapshot(snap_file).get("b") is not None


def test_clear_all(snap_file: Path, capsys) -> None:
    Snapshot(snap_file).capture("x", "ok")
    args = argparse.Namespace(file=str(snap_file), job=None, func=cmd_snapshot_clear)
    cmd_snapshot_clear(args)
    out = capsys.readouterr().out
    assert "All snapshots cleared" in out
    assert Snapshot(snap_file).all() == []
