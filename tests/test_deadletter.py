"""Tests for pipewatch.deadletter."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from pipewatch.deadletter import DeadLetterEntry, DeadLetterQueue


@pytest.fixture()
def dlq_file(tmp_path: Path) -> Path:
    return tmp_path / "deadletter.json"


@pytest.fixture()
def dlq(dlq_file: Path) -> DeadLetterQueue:
    return DeadLetterQueue(dlq_file)


def test_empty_queue_returns_empty_list(dlq: DeadLetterQueue) -> None:
    assert dlq.all() == []


def test_push_returns_entry(dlq: DeadLetterQueue) -> None:
    entry = dlq.push("ingest", "timeout", {"url": "http://example.com"})
    assert isinstance(entry, DeadLetterEntry)
    assert entry.job == "ingest"
    assert entry.reason == "timeout"
    assert entry.attempts == 1


def test_push_persists_to_disk(dlq: DeadLetterQueue, dlq_file: Path) -> None:
    dlq.push("etl", "connection refused", {})
    raw = json.loads(dlq_file.read_text())
    assert len(raw) == 1
    assert raw[0]["job"] == "etl"


def test_all_returns_all_entries(dlq: DeadLetterQueue) -> None:
    dlq.push("job-a", "err", {})
    dlq.push("job-b", "err", {})
    assert len(dlq.all()) == 2


def test_for_job_filters_by_job(dlq: DeadLetterQueue) -> None:
    dlq.push("job-a", "err", {})
    dlq.push("job-b", "err", {})
    dlq.push("job-a", "timeout", {})
    results = dlq.for_job("job-a")
    assert len(results) == 2
    assert all(e.job == "job-a" for e in results)


def test_for_job_unknown_returns_empty(dlq: DeadLetterQueue) -> None:
    dlq.push("job-a", "err", {})
    assert dlq.for_job("unknown") == []


def test_clear_all_removes_everything(dlq: DeadLetterQueue) -> None:
    dlq.push("job-a", "err", {})
    dlq.push("job-b", "err", {})
    removed = dlq.clear()
    assert removed == 2
    assert dlq.all() == []


def test_clear_by_job_removes_only_that_job(dlq: DeadLetterQueue) -> None:
    dlq.push("job-a", "err", {})
    dlq.push("job-b", "err", {})
    removed = dlq.clear(job="job-a")
    assert removed == 1
    remaining = dlq.all()
    assert len(remaining) == 1
    assert remaining[0].job == "job-b"


def test_entry_to_dict_round_trip() -> None:
    from datetime import datetime, timezone

    ts = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
    entry = DeadLetterEntry(job="j", reason="r", payload={"k": 1}, timestamp=ts, attempts=3)
    d = entry.to_dict()
    restored = DeadLetterEntry.from_dict(d)
    assert restored.job == entry.job
    assert restored.reason == entry.reason
    assert restored.payload == entry.payload
    assert restored.attempts == entry.attempts
    assert restored.timestamp == entry.timestamp
