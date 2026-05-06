"""Tests for pipewatch.banlist."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from pipewatch.banlist import Banlist, BanEntry, BanlistError


@pytest.fixture()
def bl_file(tmp_path: Path) -> Path:
    return tmp_path / "banlist.json"


@pytest.fixture()
def bl(bl_file: Path) -> Banlist:
    return Banlist(bl_file)


def test_empty_banlist_returns_empty_list(bl: Banlist) -> None:
    assert bl.all() == []


def test_ban_creates_entry(bl: Banlist) -> None:
    entry = bl.ban("etl-job", "repeated failures")
    assert isinstance(entry, BanEntry)
    assert entry.job == "etl-job"
    assert entry.reason == "repeated failures"
    assert entry.banned_by == "system"


def test_ban_persists_to_disk(bl_file: Path) -> None:
    bl = Banlist(bl_file)
    bl.ban("job-a", "too slow")
    bl2 = Banlist(bl_file)
    assert bl2.is_banned("job-a")


def test_ban_empty_job_raises(bl: Banlist) -> None:
    with pytest.raises(BanlistError, match="job name"):
        bl.ban("", "some reason")


def test_ban_empty_reason_raises(bl: Banlist) -> None:
    with pytest.raises(BanlistError, match="reason"):
        bl.ban("job-x", "")


def test_duplicate_ban_returns_existing_entry(bl: Banlist) -> None:
    first = bl.ban("dup-job", "first ban")
    second = bl.ban("dup-job", "second ban")
    assert first.banned_at == second.banned_at
    assert len(bl.all()) == 1


def test_is_banned_true_after_ban(bl: Banlist) -> None:
    bl.ban("check-job", "reason")
    assert bl.is_banned("check-job") is True


def test_is_banned_false_for_unknown(bl: Banlist) -> None:
    assert bl.is_banned("unknown") is False


def test_unban_returns_true_and_removes(bl: Banlist) -> None:
    bl.ban("rm-job", "reason")
    result = bl.unban("rm-job")
    assert result is True
    assert bl.is_banned("rm-job") is False


def test_unban_unknown_returns_false(bl: Banlist) -> None:
    assert bl.unban("ghost") is False


def test_get_returns_entry(bl: Banlist) -> None:
    bl.ban("get-job", "test", banned_by="ops")
    entry = bl.get("get-job")
    assert entry is not None
    assert entry.banned_by == "ops"


def test_get_missing_returns_none(bl: Banlist) -> None:
    assert bl.get("nope") is None


def test_clear_removes_all(bl: Banlist) -> None:
    bl.ban("a", "r1")
    bl.ban("b", "r2")
    bl.clear()
    assert bl.all() == []


def test_entry_to_dict_round_trip() -> None:
    from datetime import datetime, timezone
    ts = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
    e = BanEntry(job="j", reason="r", banned_at=ts, banned_by="ci")
    d = e.to_dict()
    e2 = BanEntry.from_dict(d)
    assert e2.job == e.job
    assert e2.reason == e.reason
    assert e2.banned_by == e.banned_by
    assert e2.banned_at == e.banned_at
