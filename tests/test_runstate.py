"""Tests for pipewatch.runstate."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

import pytest

from pipewatch.runstate import (
    RunState,
    RunStateError,
    RunStateStore,
    create_state,
)


@pytest.fixture
def state_file(tmp_path: Path) -> Path:
    return tmp_path / "runstate.json"


@pytest.fixture
def store(state_file: Path) -> RunStateStore:
    return RunStateStore(state_file)


def _make_state(**kwargs) -> RunState:
    defaults = dict(
        job="etl",
        pid=1234,
        started_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        status="running",
        note="",
    )
    defaults.update(kwargs)
    return RunState(**defaults)


def test_to_dict_contains_all_keys():
    s = _make_state()
    d = s.to_dict()
    assert set(d.keys()) == {"job", "pid", "started_at", "status", "note"}


def test_from_dict_round_trip():
    s = _make_state(note="batch run")
    assert RunState.from_dict(s.to_dict()).note == "batch run"


def test_from_dict_missing_key_raises():
    with pytest.raises(RunStateError):
        RunState.from_dict({"job": "x"})


def test_store_save_and_load(store: RunStateStore):
    s = _make_state(job="ingest")
    store.save(s)
    loaded = store.load()
    assert loaded is not None
    assert loaded.job == "ingest"
    assert loaded.pid == 1234


def test_store_load_missing_returns_none(store: RunStateStore):
    assert store.load() is None


def test_store_clear_removes_file(store: RunStateStore, state_file: Path):
    store.save(_make_state())
    assert state_file.exists()
    store.clear()
    assert not state_file.exists()


def test_store_clear_noop_when_no_file(store: RunStateStore):
    store.clear()  # should not raise


def test_is_running_with_current_pid(store: RunStateStore):
    s = _make_state(pid=os.getpid(), status="running")
    store.save(s)
    assert store.is_running() is True


def test_is_running_false_when_no_state(store: RunStateStore):
    assert store.is_running() is False


def test_is_running_false_for_done_status(store: RunStateStore):
    s = _make_state(pid=os.getpid(), status="done")
    store.save(s)
    assert store.is_running() is False


def test_create_state_uses_current_pid():
    s = create_state("myjob")
    assert s.pid == os.getpid()
    assert s.job == "myjob"
    assert s.status == "running"
