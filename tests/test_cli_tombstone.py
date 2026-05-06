"""Tests for pipewatch.cli_tombstone."""
from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from pipewatch.cli_tombstone import (
    build_tombstone_parser,
    cmd_tombstone_check,
    cmd_tombstone_list,
    cmd_tombstone_retire,
    cmd_tombstone_remove,
)
from pipewatch.tombstone import Tombstone


@pytest.fixture()
def ts_file(tmp_path: Path) -> Path:
    return tmp_path / "tombstones.json"


def _build_parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser()
    sub = root.add_subparsers(dest="cmd")
    build_tombstone_parser(sub)
    return root


def _parse(args: list[str]) -> argparse.Namespace:
    return _build_parser().parse_args(args)


def test_build_tombstone_parser_registers_subcommands() -> None:
    p = _build_parser()
    ns = p.parse_args(["tombstone", "list"])
    assert ns.tombstone_cmd == "list"


def test_list_empty(ts_file: Path, capsys: pytest.CaptureFixture[str]) -> None:
    ns = argparse.Namespace(file=str(ts_file))
    cmd_tombstone_list(ns)
    assert "No retired" in capsys.readouterr().out


def test_list_shows_entries(ts_file: Path, capsys: pytest.CaptureFixture[str]) -> None:
    Tombstone(ts_file).retire("pipeline_old", "sunset")
    ns = argparse.Namespace(file=str(ts_file))
    cmd_tombstone_list(ns)
    assert "pipeline_old" in capsys.readouterr().out


def test_check_active(ts_file: Path, capsys: pytest.CaptureFixture[str]) -> None:
    ns = argparse.Namespace(file=str(ts_file), job="unknown_job")
    cmd_tombstone_check(ns)
    assert "active" in capsys.readouterr().out


def test_check_retired(ts_file: Path, capsys: pytest.CaptureFixture[str]) -> None:
    Tombstone(ts_file).retire("old_job", "no longer needed")
    ns = argparse.Namespace(file=str(ts_file), job="old_job")
    cmd_tombstone_check(ns)
    assert "RETIRED" in capsys.readouterr().out


def test_retire_cmd_success(ts_file: Path, capsys: pytest.CaptureFixture[str]) -> None:
    ns = argparse.Namespace(file=str(ts_file), job="etl_v1", reason="replaced", by="alice", note="")
    cmd_tombstone_retire(ns)
    assert "etl_v1" in capsys.readouterr().out
    assert Tombstone(ts_file).is_retired("etl_v1")


def test_retire_cmd_duplicate_exits(ts_file: Path) -> None:
    Tombstone(ts_file).retire("dup_job", "first")
    ns = argparse.Namespace(file=str(ts_file), job="dup_job", reason="second", by="", note="")
    with pytest.raises(SystemExit):
        cmd_tombstone_retire(ns)


def test_remove_cmd_existing(ts_file: Path, capsys: pytest.CaptureFixture[str]) -> None:
    Tombstone(ts_file).retire("to_remove", "old")
    ns = argparse.Namespace(file=str(ts_file), job="to_remove")
    cmd_tombstone_remove(ns)
    assert "removed" in capsys.readouterr().out
    assert not Tombstone(ts_file).is_retired("to_remove")


def test_remove_cmd_missing(ts_file: Path, capsys: pytest.CaptureFixture[str]) -> None:
    ns = argparse.Namespace(file=str(ts_file), job="ghost")
    cmd_tombstone_remove(ns)
    assert "No tombstone" in capsys.readouterr().out
