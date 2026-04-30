"""Tests for pipewatch.debounce."""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from pipewatch.debounce import Debounce, DebounceError, DebounceState


@pytest.fixture()
def state_file(tmp_path: Path) -> Path:
    return tmp_path / "debounce.json"


@pytest.fixture()
def db(state_file: Path) -> Debounce:
    return Debounce(quiet_seconds=30.0, state_file=state_file)


# ---------------------------------------------------------------------------
# construction
# ---------------------------------------------------------------------------

def test_zero_quiet_seconds_raises(state_file: Path) -> None:
    with pytest.raises(DebounceError):
        Debounce(quiet_seconds=0, state_file=state_file)


def test_negative_quiet_seconds_raises(state_file: Path) -> None:
    with pytest.raises(DebounceError):
        Debounce(quiet_seconds=-5, state_file=state_file)


# ---------------------------------------------------------------------------
# first trigger is always allowed
# ---------------------------------------------------------------------------

def test_first_trigger_is_allowed(db: Debounce) -> None:
    assert db.trigger("job.a") is True


def test_first_trigger_creates_state(db: Debounce) -> None:
    now = time.time()
    db.trigger("job.a", now=now)
    entry = db.state_for("job.a")
    assert entry is not None
    assert entry.count == 1
    assert entry.last_trigger == pytest.approx(now)


# ---------------------------------------------------------------------------
# suppression within quiet window
# ---------------------------------------------------------------------------

def test_second_trigger_within_window_suppressed(db: Debounce) -> None:
    t0 = time.time()
    db.trigger("job.b", now=t0)
    assert db.trigger("job.b", now=t0 + 10) is False


def test_suppressed_trigger_increments_count(db: Debounce) -> None:
    t0 = time.time()
    db.trigger("job.b", now=t0)
    db.trigger("job.b", now=t0 + 5)
    db.trigger("job.b", now=t0 + 10)
    assert db.state_for("job.b").count == 3  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# allowed after quiet period
# ---------------------------------------------------------------------------

def test_trigger_after_quiet_period_is_allowed(db: Debounce) -> None:
    t0 = time.time()
    db.trigger("job.c", now=t0)
    assert db.trigger("job.c", now=t0 + 31) is True


def test_trigger_after_quiet_period_resets_count(db: Debounce) -> None:
    t0 = time.time()
    db.trigger("job.c", now=t0)
    db.trigger("job.c", now=t0 + 31)
    assert db.state_for("job.c").count == 1  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# persistence
# ---------------------------------------------------------------------------

def test_state_persists_across_instances(state_file: Path) -> None:
    t0 = time.time()
    db1 = Debounce(quiet_seconds=30, state_file=state_file)
    db1.trigger("job.d", now=t0)

    db2 = Debounce(quiet_seconds=30, state_file=state_file)
    assert db2.trigger("job.d", now=t0 + 5) is False


# ---------------------------------------------------------------------------
# reset
# ---------------------------------------------------------------------------

def test_reset_clears_state(db: Debounce) -> None:
    t0 = time.time()
    db.trigger("job.e", now=t0)
    db.reset("job.e")
    assert db.state_for("job.e") is None


def test_reset_allows_next_trigger(db: Debounce) -> None:
    t0 = time.time()
    db.trigger("job.e", now=t0)
    db.reset("job.e")
    assert db.trigger("job.e", now=t0 + 1) is True


# ---------------------------------------------------------------------------
# independent keys
# ---------------------------------------------------------------------------

def test_different_keys_are_independent(db: Debounce) -> None:
    t0 = time.time()
    db.trigger("key.x", now=t0)
    assert db.trigger("key.y", now=t0 + 1) is True
