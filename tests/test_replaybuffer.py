"""Tests for pipewatch.replaybuffer."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from pipewatch.replaybuffer import ReplayBuffer, ReplayBufferError, ReplayEntry

TS = "2024-01-15T10:00:00Z"


@pytest.fixture()
def buf_file(tmp_path: Path) -> Path:
    return tmp_path / "replay.json"


@pytest.fixture()
def buf(buf_file: Path) -> ReplayBuffer:
    return ReplayBuffer(buf_file, capacity=5)


def _entry(job: str = "etl", outcome: str = "success", code: int = 0) -> ReplayEntry:
    return ReplayEntry(job=job, outcome=outcome, exit_code=code, timestamp=TS)


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

def test_capacity_zero_raises(buf_file: Path) -> None:
    with pytest.raises(ReplayBufferError, match="capacity"):
        ReplayBuffer(buf_file, capacity=0)


def test_empty_buffer_returns_empty_list(buf: ReplayBuffer) -> None:
    assert buf.all() == []


# ---------------------------------------------------------------------------
# Push / retrieve
# ---------------------------------------------------------------------------

def test_push_returns_entry(buf: ReplayBuffer) -> None:
    e = buf.push(_entry())
    assert e.job == "etl"


def test_push_persists_to_disk(buf: ReplayBuffer, buf_file: Path) -> None:
    buf.push(_entry())
    raw = json.loads(buf_file.read_text())
    assert len(raw) == 1
    assert raw[0]["job"] == "etl"


def test_push_empty_job_raises(buf: ReplayBuffer) -> None:
    with pytest.raises(ReplayBufferError, match="job"):
        buf.push(ReplayEntry(job="", outcome="success", exit_code=0, timestamp=TS))


def test_capacity_evicts_oldest(buf: ReplayBuffer) -> None:
    for i in range(7):
        buf.push(_entry(job=f"job{i}"))
    assert len(buf.all()) == 5
    assert buf.all()[0].job == "job2"


# ---------------------------------------------------------------------------
# Filtering
# ---------------------------------------------------------------------------

def test_for_job_filters_correctly(buf: ReplayBuffer) -> None:
    buf.push(_entry(job="a"))
    buf.push(_entry(job="b"))
    buf.push(_entry(job="a"))
    assert len(buf.for_job("a")) == 2
    assert all(e.job == "a" for e in buf.for_job("a"))


def test_latest_returns_most_recent(buf: ReplayBuffer) -> None:
    buf.push(_entry(job="a", outcome="failure", code=1))
    buf.push(_entry(job="a", outcome="success", code=0))
    assert buf.latest("a").outcome == "success"  # type: ignore[union-attr]


def test_latest_unknown_job_returns_none(buf: ReplayBuffer) -> None:
    assert buf.latest("ghost") is None


# ---------------------------------------------------------------------------
# Persistence across instances
# ---------------------------------------------------------------------------

def test_reload_from_disk(buf_file: Path) -> None:
    b1 = ReplayBuffer(buf_file, capacity=10)
    b1.push(_entry(job="pipe", note="first run"))
    b2 = ReplayBuffer(buf_file, capacity=10)
    assert len(b2.all()) == 1
    assert b2.all()[0].note == "first run"


# ---------------------------------------------------------------------------
# Clear
# ---------------------------------------------------------------------------

def test_clear_empties_buffer(buf: ReplayBuffer) -> None:
    buf.push(_entry())
    buf.clear()
    assert buf.all() == []


def test_clear_writes_empty_file(buf: ReplayBuffer, buf_file: Path) -> None:
    buf.push(_entry())
    buf.clear()
    assert json.loads(buf_file.read_text()) == []
