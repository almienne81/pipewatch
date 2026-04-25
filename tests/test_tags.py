"""Tests for pipewatch.tags and pipewatch.cli_tags."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from pipewatch.tags import Tags, TagError, parse_tags, tags_from_dict
from pipewatch.cli_tags import build_tags_parser


# ---------------------------------------------------------------------------
# Tags unit tests
# ---------------------------------------------------------------------------

def test_empty_tags_has_zero_length():
    assert len(Tags()) == 0


def test_set_returns_new_instance_with_value():
    t = Tags().set("env", "prod")
    assert t.get("env") == "prod"
    assert len(t) == 1


def test_set_is_non_mutating():
    original = Tags()
    updated = original.set("env", "prod")
    assert "env" not in original
    assert "env" in updated


def test_invalid_key_raises_tag_error():
    with pytest.raises(TagError, match="Invalid tag key"):
        Tags().set("bad key!", "value")


def test_non_string_value_raises_tag_error():
    with pytest.raises(TagError, match="must be a string"):
        Tags().set("key", 42)  # type: ignore[arg-type]


def test_to_dict_round_trips():
    t = Tags().set("a", "1").set("b", "2")
    assert t.to_dict() == {"a": "1", "b": "2"}


def test_to_list_sorted():
    t = Tags().set("z", "last").set("a", "first")
    assert t.to_list() == ["a=first", "z=last"]


def test_parse_tags_valid():
    t = parse_tags(["env=prod", "team=data"])
    assert t.get("env") == "prod"
    assert t.get("team") == "data"


def test_parse_tags_missing_equals_raises():
    with pytest.raises(TagError, match="key=value"):
        parse_tags(["badtag"])


def test_tags_from_dict():
    t = tags_from_dict({"region": "us-east", "tier": "gold"})
    assert t.get("region") == "us-east"
    assert len(t) == 2


# ---------------------------------------------------------------------------
# CLI tags tests
# ---------------------------------------------------------------------------

@pytest.fixture()
def history_file(tmp_path: Path) -> Path:
    return tmp_path / "history.json"


def _write_history(path: Path, entries: list) -> None:
    path.write_text(json.dumps(entries))


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd")
    build_tags_parser(sub)
    return p


def test_tags_list_no_entries(history_file: Path, capsys):
    history_file.write_text(json.dumps([]))
    p = _build_parser()
    args = p.parse_args(["tags", "--history-file", str(history_file), "list"])
    args.func(args)
    out = capsys.readouterr().out
    assert "No history" in out


def test_tags_list_shows_keys(history_file: Path, capsys):
    entry = {"command": "run.sh", "exit_code": 0, "started_at": "2024-01-01T00:00:00",
             "finished_at": "2024-01-01T00:00:01", "extra": {"tags": {"env": "prod"}}}
    _write_history(history_file, [entry])
    p = _build_parser()
    args = p.parse_args(["tags", "--history-file", str(history_file), "list"])
    args.func(args)
    out = capsys.readouterr().out
    assert "env" in out


def test_tags_filter_matches(history_file: Path, capsys):
    entries = [
        {"command": "a.sh", "exit_code": 0, "started_at": "2024-01-01T00:00:00",
         "finished_at": "2024-01-01T00:00:01", "extra": {"tags": {"env": "prod"}}},
        {"command": "b.sh", "exit_code": 1, "started_at": "2024-01-01T00:00:00",
         "finished_at": "2024-01-01T00:00:01", "extra": {"tags": {"env": "dev"}}},
    ]
    _write_history(history_file, entries)
    p = _build_parser()
    args = p.parse_args(["tags", "--history-file", str(history_file), "filter", "env=prod"])
    args.func(args)
    out = capsys.readouterr().out
    assert "a.sh" in out
    assert "b.sh" not in out


def test_tags_filter_bad_format_exits(history_file: Path):
    history_file.write_text(json.dumps([]))
    p = _build_parser()
    args = p.parse_args(["tags", "--history-file", str(history_file), "filter", "badtag"])
    with pytest.raises(SystemExit):
        args.func(args)
