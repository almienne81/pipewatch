"""Tests for pipewatch.correlation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from pipewatch.correlation import CorrelationEntry, CorrelationError, CorrelationStore


@pytest.fixture
def store_file(tmp_path: Path) -> Path:
    return tmp_path / "correlation.json"


@pytest.fixture
def store(store_file: Path) -> CorrelationStore:
    return CorrelationStore(store_file)


def test_generate_returns_entry_with_uuid(store: CorrelationStore) -> None:
    entry = store.generate("etl-job")
    assert len(entry.correlation_id) == 36
    assert "-" in entry.correlation_id
    assert entry.job == "etl-job"
    assert entry.parent_id is None
    assert entry.note == ""


def test_generate_empty_job_raises(store: CorrelationStore) -> None:
    with pytest.raises(CorrelationError):
        store.generate("")


def test_generate_with_parent_id(store: CorrelationStore) -> None:
    parent = store.generate("parent-job")
    child = store.generate("child-job", parent_id=parent.correlation_id)
    assert child.parent_id == parent.correlation_id


def test_generate_with_note(store: CorrelationStore) -> None:
    entry = store.generate("my-job", note="triggered by scheduler")
    assert entry.note == "triggered by scheduler"


def test_generate_persists_to_disk(store: CorrelationStore, store_file: Path) -> None:
    store.generate("persist-job")
    data = json.loads(store_file.read_text())
    assert len(data) == 1
    assert data[0]["job"] == "persist-job"


def test_list_returns_all_entries(store: CorrelationStore) -> None:
    store.generate("job-a")
    store.generate("job-b")
    entries = store.list()
    assert len(entries) == 2


def test_list_filtered_by_job(store: CorrelationStore) -> None:
    store.generate("job-a")
    store.generate("job-b")
    store.generate("job-a")
    results = store.list(job="job-a")
    assert len(results) == 2
    assert all(e.job == "job-a" for e in results)


def test_get_returns_entry_by_id(store: CorrelationStore) -> None:
    entry = store.generate("lookup-job")
    found = store.get(entry.correlation_id)
    assert found is not None
    assert found.correlation_id == entry.correlation_id


def test_get_missing_id_returns_none(store: CorrelationStore) -> None:
    assert store.get("nonexistent-id") is None


def test_clear_removes_all_entries(store: CorrelationStore) -> None:
    store.generate("job-x")
    store.generate("job-y")
    store.clear()
    assert store.list() == []


def test_to_dict_round_trip() -> None:
    from datetime import datetime, timezone
    entry = CorrelationEntry(
        correlation_id="abc-123",
        job="round-trip",
        parent_id="parent-456",
        created_at=datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
        note="test",
    )
    restored = CorrelationEntry.from_dict(entry.to_dict())
    assert restored.correlation_id == entry.correlation_id
    assert restored.job == entry.job
    assert restored.parent_id == entry.parent_id
    assert restored.note == entry.note


def test_list_empty_store_returns_empty(store: CorrelationStore) -> None:
    assert store.list() == []
