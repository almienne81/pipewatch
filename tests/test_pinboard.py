"""Tests for pipewatch.pinboard and pipewatch.cli_pinboard."""
from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from pipewatch.pinboard import Pinboard, PinboardError, PinEntry


@pytest.fixture()
def pb_file(tmp_path: Path) -> Path:
    return tmp_path / "pins.json"


@pytest.fixture()
def pb(pb_file: Path) -> Pinboard:
    return Pinboard(pb_file)


# ---------------------------------------------------------------------------
# PinEntry
# ---------------------------------------------------------------------------

def test_entry_to_dict_round_trip() -> None:
    e = PinEntry(key="k", value="v", pinned_at="2024-01-01T00:00:00+00:00")
    assert PinEntry.from_dict(e.to_dict()) == e


# ---------------------------------------------------------------------------
# Pinboard
# ---------------------------------------------------------------------------

def test_empty_pinboard_returns_empty_list(pb: Pinboard) -> None:
    assert pb.all() == []
    assert len(pb) == 0


def test_pin_and_retrieve(pb: Pinboard) -> None:
    pb.pin("run_id", "abc123")
    entry = pb.get("run_id")
    assert entry is not None
    assert entry.value == "abc123"


def test_pin_overwrites_existing(pb: Pinboard) -> None:
    pb.pin("stage", "extract")
    pb.pin("stage", "transform")
    assert pb.get("stage").value == "transform"  # type: ignore[union-attr]
    assert len(pb) == 1


def test_empty_key_raises(pb: Pinboard) -> None:
    with pytest.raises(PinboardError):
        pb.pin("", "value")


def test_whitespace_key_raises(pb: Pinboard) -> None:
    with pytest.raises(PinboardError):
        pb.pin("   ", "value")


def test_non_string_value_raises(pb: Pinboard) -> None:
    with pytest.raises(PinboardError):
        pb.pin("key", 42)  # type: ignore[arg-type]


def test_get_missing_key_returns_none(pb: Pinboard) -> None:
    assert pb.get("missing") is None


def test_remove_existing_key(pb: Pinboard) -> None:
    pb.pin("x", "1")
    assert pb.remove("x") is True
    assert pb.get("x") is None


def test_remove_missing_key_returns_false(pb: Pinboard) -> None:
    assert pb.remove("nope") is False


def test_all_returns_sorted_by_key(pb: Pinboard) -> None:
    pb.pin("z", "last")
    pb.pin("a", "first")
    pb.pin("m", "mid")
    keys = [e.key for e in pb.all()]
    assert keys == ["a", "m", "z"]


def test_clear_removes_all(pb: Pinboard) -> None:
    pb.pin("a", "1")
    pb.pin("b", "2")
    pb.clear()
    assert len(pb) == 0


def test_persists_across_instances(pb_file: Path) -> None:
    Pinboard(pb_file).pin("env", "production")
    reloaded = Pinboard(pb_file)
    assert reloaded.get("env") is not None
    assert reloaded.get("env").value == "production"  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------

def _build_parser(pb_file: Path) -> argparse.ArgumentParser:
    from pipewatch.cli_pinboard import build_pinboard_parser
    root = argparse.ArgumentParser()
    sub = root.add_subparsers(dest="cmd")
    build_pinboard_parser(sub)
    return root


def test_build_pinboard_parser_registers_subcommands(pb_file: Path) -> None:
    parser = _build_parser(pb_file)
    ns = parser.parse_args(["pinboard", "--file", str(pb_file), "list"])
    assert ns.pin_cmd == "list"


def test_cmd_pin_set_and_list(pb_file: Path, capsys: pytest.CaptureFixture) -> None:
    from pipewatch.cli_pinboard import cmd_pin_set, cmd_pin_list

    ns_set = argparse.Namespace(file=str(pb_file), key="region", value="us-east-1")
    cmd_pin_set(ns_set)
    ns_list = argparse.Namespace(file=str(pb_file))
    cmd_pin_list(ns_list)
    out = capsys.readouterr().out
    assert "region=us-east-1" in out


def test_cmd_pin_get_missing(pb_file: Path, capsys: pytest.CaptureFixture) -> None:
    from pipewatch.cli_pinboard import cmd_pin_get
    ns = argparse.Namespace(file=str(pb_file), key="ghost")
    cmd_pin_get(ns)
    assert "not found" in capsys.readouterr().out


def test_cmd_pin_remove(pb_file: Path, capsys: pytest.CaptureFixture) -> None:
    from pipewatch.cli_pinboard import cmd_pin_set, cmd_pin_remove
    cmd_pin_set(argparse.Namespace(file=str(pb_file), key="tmp", value="yes"))
    cmd_pin_remove(argparse.Namespace(file=str(pb_file), key="tmp"))
    assert "Removed" in capsys.readouterr().out
