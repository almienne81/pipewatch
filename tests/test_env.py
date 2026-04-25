"""Tests for pipewatch.env — environment snapshot utilities."""

from __future__ import annotations

import pytest

from pipewatch.env import EnvError, EnvSnapshot, capture, diff


# ---------------------------------------------------------------------------
# EnvSnapshot
# ---------------------------------------------------------------------------

def test_snapshot_get_existing_key():
    snap = EnvSnapshot(variables={"FOO": "bar"})
    assert snap.get("FOO") == "bar"


def test_snapshot_get_missing_key_returns_default():
    snap = EnvSnapshot(variables={})
    assert snap.get("MISSING") is None
    assert snap.get("MISSING", "fallback") == "fallback"


def test_snapshot_keys_sorted():
    snap = EnvSnapshot(variables={"ZEBRA": "1", "ALPHA": "2", "MANGO": "3"})
    assert snap.keys() == ["ALPHA", "MANGO", "ZEBRA"]


def test_snapshot_to_dict_is_copy():
    original = {"A": "1"}
    snap = EnvSnapshot(variables=original)
    d = snap.to_dict()
    d["B"] = "2"
    assert "B" not in snap.variables


def test_snapshot_len():
    snap = EnvSnapshot(variables={"X": "1", "Y": "2"})
    assert len(snap) == 2


# ---------------------------------------------------------------------------
# capture
# ---------------------------------------------------------------------------

def test_capture_explicit_keys(monkeypatch):
    monkeypatch.setenv("PW_TEST_A", "hello")
    monkeypatch.setenv("PW_TEST_B", "world")
    snap = capture(keys=["PW_TEST_A", "PW_TEST_B", "PW_MISSING"])
    assert snap.get("PW_TEST_A") == "hello"
    assert snap.get("PW_TEST_B") == "world"
    assert snap.get("PW_MISSING") is None


def test_capture_by_prefix(monkeypatch):
    monkeypatch.setenv("PIPE_FOO", "1")
    monkeypatch.setenv("PIPE_BAR", "2")
    monkeypatch.setenv("OTHER_VAR", "3")
    snap = capture(prefix="PIPE_")
    assert "PIPE_FOO" in snap.variables
    assert "PIPE_BAR" in snap.variables
    assert "OTHER_VAR" not in snap.variables


def test_capture_no_args_returns_all(monkeypatch):
    monkeypatch.setenv("PW_UNIQUE_KEY_XYZ", "yes")
    snap = capture()
    assert snap.get("PW_UNIQUE_KEY_XYZ") == "yes"
    assert len(snap) > 1


def test_capture_both_keys_and_prefix_raises():
    with pytest.raises(EnvError, match="either"):
        capture(keys=["A"], prefix="B_")


# ---------------------------------------------------------------------------
# diff
# ---------------------------------------------------------------------------

def test_diff_detects_added_key():
    before = EnvSnapshot(variables={})
    after = EnvSnapshot(variables={"NEW": "value"})
    changes = diff(before, after)
    assert "NEW" in changes
    assert changes["NEW"] == {"before": None, "after": "value"}


def test_diff_detects_removed_key():
    before = EnvSnapshot(variables={"OLD": "gone"})
    after = EnvSnapshot(variables={})
    changes = diff(before, after)
    assert changes["OLD"] == {"before": "gone", "after": None}


def test_diff_detects_changed_value():
    before = EnvSnapshot(variables={"K": "v1"})
    after = EnvSnapshot(variables={"K": "v2"})
    assert diff(before, after)["K"] == {"before": "v1", "after": "v2"}


def test_diff_no_changes_returns_empty():
    snap = EnvSnapshot(variables={"A": "1", "B": "2"})
    assert diff(snap, snap) == {}
