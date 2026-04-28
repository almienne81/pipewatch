"""Integration tests: RunStateStore interacts correctly with create_state."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from pipewatch.runstate import RunStateStore, create_state


@pytest.fixture
def store(tmp_path: Path) -> RunStateStore:
    return RunStateStore(tmp_path / "runstate.json")


def test_create_and_persist(store: RunStateStore):
    s = create_state("pipeline-a")
    store.save(s)
    loaded = store.load()
    assert loaded.job == "pipeline-a"
    assert loaded.pid == os.getpid()
    assert loaded.status == "running"


def test_update_status_persists(store: RunStateStore):
    s = create_state("pipeline-b")
    store.save(s)
    loaded = store.load()
    loaded.status = "done"
    loaded.note = "finished cleanly"
    store.save(loaded)
    reloaded = store.load()
    assert reloaded.status == "done"
    assert reloaded.note == "finished cleanly"


def test_is_running_reflects_live_process(store: RunStateStore):
    s = create_state("pipeline-c")
    store.save(s)
    assert store.is_running() is True


def test_is_running_false_after_clear(store: RunStateStore):
    s = create_state("pipeline-d")
    store.save(s)
    store.clear()
    assert store.is_running() is False


def test_stale_pid_is_not_running(store: RunStateStore):
    s = create_state("pipeline-e")
    s.pid = 99999999  # very unlikely to exist
    store.save(s)
    assert store.is_running() is False


def test_nested_directory_created_automatically(tmp_path: Path):
    deep = tmp_path / "a" / "b" / "c" / "state.json"
    s = RunStateStore(deep)
    entry = create_state("deep-job")
    s.save(entry)
    assert deep.exists()
