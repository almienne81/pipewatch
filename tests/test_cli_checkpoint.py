"""Tests for pipewatch.cli_checkpoint sub-commands."""

from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from pipewatch.checkpoint import Checkpoint
from pipewatch.cli_checkpoint import (
    build_checkpoint_parser,
    cmd_checkpoint_show,
    cmd_checkpoint_last,
    cmd_checkpoint_clear,
)


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd")
    build_checkpoint_parser(sub)
    return p


@pytest.fixture()
def cp_file(tmp_path: Path) -> Path:
    return tmp_path / "checkpoints.json"


def _make_args(cp_file: Path, **kwargs) -> argparse.Namespace:
    return argparse.Namespace(file=str(cp_file), **kwargs)


def test_build_checkpoint_parser_registers_subcommands() -> None:
    p = _build_parser()
    assert p is not None


def test_show_empty(cp_file: Path, capsys: pytest.CaptureFixture) -> None:
    cmd_checkpoint_show(_make_args(cp_file))
    out = capsys.readouterr().out
    assert "No checkpoints" in out


def test_show_lists_entries(cp_file: Path, capsys: pytest.CaptureFixture) -> None:
    cp = Checkpoint(cp_file)
    cp.mark("extract", "ok")
    cp.mark("load", "failed", message="timeout")
    cmd_checkpoint_show(_make_args(cp_file))
    out = capsys.readouterr().out
    assert "extract" in out
    assert "load" in out
    assert "timeout" in out


def test_last_found(cp_file: Path, capsys: pytest.CaptureFixture) -> None:
    cp = Checkpoint(cp_file)
    cp.mark("transform", "ok", message="done")
    cmd_checkpoint_last(_make_args(cp_file, stage="transform"))
    out = capsys.readouterr().out
    assert "transform" in out
    assert "ok" in out


def test_last_not_found(cp_file: Path, capsys: pytest.CaptureFixture) -> None:
    cmd_checkpoint_last(_make_args(cp_file, stage="missing"))
    out = capsys.readouterr().out
    assert "No checkpoint found" in out


def test_clear_removes_all(cp_file: Path, capsys: pytest.CaptureFixture) -> None:
    cp = Checkpoint(cp_file)
    cp.mark("extract", "ok")
    cmd_checkpoint_clear(_make_args(cp_file))
    out = capsys.readouterr().out
    assert "cleared" in out.lower()
    assert not cp_file.exists()
