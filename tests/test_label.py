"""Tests for pipewatch.label and pipewatch.cli_label."""

from __future__ import annotations

import json
import argparse
import pytest

from pipewatch.label import Labels, LabelError


# ---------------------------------------------------------------------------
# Labels unit tests
# ---------------------------------------------------------------------------

def test_empty_labels_has_zero_length():
    assert len(Labels()) == 0


def test_set_returns_new_instance():
    l1 = Labels()
    l2 = l1.set("env", "prod")
    assert l1 is not l2
    assert len(l1) == 0
    assert l2.get("env") == "prod"


def test_set_is_non_mutating():
    base = Labels().set("a", "1")
    base.set("b", "2")
    assert base.get("b") is None


def test_invalid_key_raises():
    with pytest.raises(LabelError):
        Labels().set("Bad Key!", "value")


def test_non_string_value_raises():
    with pytest.raises(LabelError):
        Labels().set("key", 42)  # type: ignore[arg-type]


def test_value_too_long_raises():
    with pytest.raises(LabelError):
        Labels().set("key", "x" * 257)


def test_remove_existing_key():
    labels = Labels().set("a", "1").set("b", "2")
    result = labels.remove("a")
    assert result.get("a") is None
    assert result.get("b") == "2"


def test_remove_absent_key_is_noop():
    labels = Labels().set("a", "1")
    assert labels.remove("z").get("a") == "1"


def test_matches_all_pairs_present():
    labels = Labels().set("env", "prod").set("region", "us-east")
    assert labels.matches({"env": "prod"})
    assert labels.matches({"env": "prod", "region": "us-east"})


def test_matches_fails_on_wrong_value():
    labels = Labels().set("env", "prod")
    assert not labels.matches({"env": "staging"})


def test_matches_fails_on_missing_key():
    labels = Labels().set("env", "prod")
    assert not labels.matches({"region": "eu-west"})


def test_to_dict_round_trip():
    original = Labels().set("a", "1").set("b", "2")
    restored = Labels.from_dict(original.to_dict())
    assert restored.to_dict() == original.to_dict()


def test_keys_are_sorted():
    labels = Labels().set("z", "last").set("a", "first")
    assert labels.keys() == ["a", "z"]


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------

from pipewatch.cli_label import cmd_label_list, cmd_label_set, cmd_label_filter, build_label_parser


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd")
    build_label_parser(sub)
    return p


def test_build_label_parser_registers_subcommands():
    p = _build_parser()
    ns = p.parse_args(["label", "list"])
    assert ns.label_cmd == "list"


def test_cmd_label_set_writes_file(tmp_path):
    f = tmp_path / "labels.json"
    ns = argparse.Namespace(file=str(f), key="env", value="prod")
    cmd_label_set(ns)
    data = json.loads(f.read_text())
    assert data["env"] == "prod"


def test_cmd_label_list_prints_entries(tmp_path, capsys):
    f = tmp_path / "labels.json"
    f.write_text(json.dumps({"env": "prod", "team": "data"}))
    ns = argparse.Namespace(file=str(f))
    cmd_label_list(ns)
    out = capsys.readouterr().out
    assert "env=prod" in out
    assert "team=data" in out


def test_cmd_label_filter_match_exits_zero(tmp_path):
    f = tmp_path / "labels.json"
    f.write_text(json.dumps({"env": "prod"}))
    ns = argparse.Namespace(file=str(f), selector=["env=prod"])
    with pytest.raises(SystemExit) as exc:
        cmd_label_filter(ns)
    assert exc.value.code == 0


def test_cmd_label_filter_no_match_exits_one(tmp_path):
    f = tmp_path / "labels.json"
    f.write_text(json.dumps({"env": "prod"}))
    ns = argparse.Namespace(file=str(f), selector=["env=staging"])
    with pytest.raises(SystemExit) as exc:
        cmd_label_filter(ns)
    assert exc.value.code == 1
