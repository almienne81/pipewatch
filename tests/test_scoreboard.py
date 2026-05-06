"""Tests for pipewatch.scoreboard."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from pipewatch.scoreboard import Scoreboard, ScoreEntry, ScoreboardError


@pytest.fixture()
def sb_file(tmp_path: Path) -> Path:
    return tmp_path / "scoreboard.json"


@pytest.fixture()
def sb(sb_file: Path) -> Scoreboard:
    return Scoreboard(sb_file)


def test_empty_scoreboard_returns_empty_list(sb: Scoreboard) -> None:
    assert sb.all() == []


def test_get_missing_job_returns_none(sb: Scoreboard) -> None:
    assert sb.get("no-such-job") is None


def test_record_success_increments_both_counters(sb: Scoreboard) -> None:
    entry = sb.record("etl", success=True)
    assert entry.runs == 1
    assert entry.successes == 1
    assert entry.failures == 0


def test_record_failure_increments_only_runs(sb: Scoreboard) -> None:
    entry = sb.record("etl", success=False)
    assert entry.runs == 1
    assert entry.successes == 0
    assert entry.failures == 1


def test_multiple_records_accumulate(sb: Scoreboard) -> None:
    sb.record("etl", success=True)
    sb.record("etl", success=True)
    sb.record("etl", success=False)
    entry = sb.get("etl")
    assert entry is not None
    assert entry.runs == 3
    assert entry.successes == 2
    assert entry.failures == 1


def test_success_rate_correct(sb: Scoreboard) -> None:
    sb.record("job", success=True)
    sb.record("job", success=False)
    entry = sb.get("job")
    assert entry.success_rate == pytest.approx(0.5)


def test_success_rate_none_when_no_runs() -> None:
    e = ScoreEntry(job="x", runs=0, successes=0)
    assert e.success_rate is None


def test_empty_job_name_raises(sb: Scoreboard) -> None:
    with pytest.raises(ScoreboardError, match="job name"):
        sb.record("", success=True)


def test_persists_to_disk(sb_file: Path) -> None:
    sb1 = Scoreboard(sb_file)
    sb1.record("loader", success=True)
    sb2 = Scoreboard(sb_file)
    entry = sb2.get("loader")
    assert entry is not None
    assert entry.runs == 1


def test_ranked_by_success_rate(sb: Scoreboard) -> None:
    sb.record("a", success=True)
    sb.record("b", success=True)
    sb.record("b", success=False)
    ranked = sb.ranked(by="success_rate")
    assert ranked[0].job == "a"


def test_ranked_by_runs(sb: Scoreboard) -> None:
    sb.record("a", success=True)
    sb.record("b", success=True)
    sb.record("b", success=False)
    ranked = sb.ranked(by="runs")
    assert ranked[0].job == "b"


def test_ranked_invalid_key_raises(sb: Scoreboard) -> None:
    with pytest.raises(ScoreboardError, match="unknown ranking key"):
        sb.ranked(by="banana")


def test_clear_removes_all_entries(sb: Scoreboard) -> None:
    sb.record("x", success=True)
    sb.clear()
    assert sb.all() == []


def test_to_dict_round_trip() -> None:
    e = ScoreEntry(job="pipe", runs=5, successes=4)
    assert ScoreEntry.from_dict(e.to_dict()) == e
