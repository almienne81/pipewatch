"""Tests for pipewatch.cooldown."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from pipewatch.cooldown import Cooldown, CooldownEntry, CooldownError


@pytest.fixture()
def state_file(tmp_path: Path) -> Path:
    return tmp_path / "cooldown.json"


@pytest.fixture()
def cd(state_file: Path) -> Cooldown:
    return Cooldown(path=state_file, default_seconds=60.0)


# ---------------------------------------------------------------------------
# CooldownEntry serialisation
# ---------------------------------------------------------------------------

def test_entry_to_dict_round_trip() -> None:
    entry = CooldownEntry(key="job.a", last_alerted=1_700_000_000.0, alert_count=3)
    restored = CooldownEntry.from_dict(entry.to_dict())
    assert restored.key == entry.key
    assert restored.last_alerted == entry.last_alerted
    assert restored.alert_count == entry.alert_count


def test_entry_from_dict_missing_alert_count_defaults_one() -> None:
    data = {"key": "job.b", "last_alerted": 1_700_000_000.0}
    entry = CooldownEntry.from_dict(data)
    assert entry.alert_count == 1


# ---------------------------------------------------------------------------
# Cooldown.is_suppressed
# ---------------------------------------------------------------------------

def test_new_key_is_not_suppressed(cd: Cooldown) -> None:
    assert cd.is_suppressed("new.key") is False


def test_suppressed_immediately_after_record(cd: Cooldown) -> None:
    cd.record("job.x")
    assert cd.is_suppressed("job.x") is True


def test_not_suppressed_after_cooldown_expires(cd: Cooldown, state_file: Path) -> None:
    # Use a very short cooldown so we can expire it artificially.
    cd2 = Cooldown(path=state_file, default_seconds=0.01)
    cd2.record("job.y")
    time.sleep(0.05)
    assert cd2.is_suppressed("job.y") is False


def test_override_seconds_takes_precedence(cd: Cooldown) -> None:
    cd.record("job.z")
    # default is 60 s — but override with 0 means never suppressed
    assert cd.is_suppressed("job.z", cooldown_seconds=0.0) is False


# ---------------------------------------------------------------------------
# Cooldown.record
# ---------------------------------------------------------------------------

def test_record_increments_alert_count(cd: Cooldown) -> None:
    cd.record("job.a")
    entry = cd.record("job.a")
    assert entry.alert_count == 2


def test_record_persists_to_disk(cd: Cooldown, state_file: Path) -> None:
    cd.record("persist.key")
    reloaded = Cooldown(path=state_file, default_seconds=60.0)
    assert reloaded.is_suppressed("persist.key") is True


# ---------------------------------------------------------------------------
# Cooldown.reset
# ---------------------------------------------------------------------------

def test_reset_removes_entry(cd: Cooldown) -> None:
    cd.record("job.r")
    cd.reset("job.r")
    assert cd.is_suppressed("job.r") is False


def test_reset_nonexistent_key_is_noop(cd: Cooldown) -> None:
    cd.reset("does.not.exist")  # should not raise


# ---------------------------------------------------------------------------
# all_entries
# ---------------------------------------------------------------------------

def test_all_entries_returns_all_keys(cd: Cooldown) -> None:
    cd.record("a")
    cd.record("b")
    keys = {e.key for e in cd.all_entries()}
    assert keys == {"a", "b"}


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

def test_load_corrupted_file_raises(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text("not valid json{{{")
    with pytest.raises(CooldownError):
        Cooldown(path=bad)
