"""Tests for pipewatch.audit."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from pipewatch.audit import Audit, AuditEvent


@pytest.fixture()
def audit_file(tmp_path: Path) -> Path:
    return tmp_path / "audit.jsonl"


@pytest.fixture()
def audit(audit_file: Path) -> Audit:
    return Audit(audit_file)


def _entry(job: str = "etl", event: str = "start", **kw) -> AuditEvent:
    return AuditEvent(job=job, event=event, **kw)


def test_empty_audit_returns_empty_list(audit: Audit) -> None:
    assert audit.all() == []


def test_record_and_retrieve(audit: Audit) -> None:
    e = _entry()
    audit.record(e)
    events = audit.all()
    assert len(events) == 1
    assert events[0].job == "etl"
    assert events[0].event == "start"


def test_multiple_events_ordered(audit: Audit) -> None:
    audit.record(_entry(event="start"))
    audit.record(_entry(event="success"))
    events = audit.all()
    assert [e.event for e in events] == ["start", "success"]


def test_for_job_filters_correctly(audit: Audit) -> None:
    audit.record(_entry(job="etl", event="start"))
    audit.record(_entry(job="ingest", event="start"))
    audit.record(_entry(job="etl", event="success"))
    assert len(audit.for_job("etl")) == 2
    assert len(audit.for_job("ingest")) == 1
    assert audit.for_job("missing") == []


def test_to_dict_round_trip() -> None:
    ts = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
    e = AuditEvent(job="j", event="retry", timestamp=ts, details="attempt 2", exit_code=1)
    d = e.to_dict()
    e2 = AuditEvent.from_dict(d)
    assert e2.job == e.job
    assert e2.event == e.event
    assert e2.timestamp == ts
    assert e2.details == "attempt 2"
    assert e2.exit_code == 1


def test_optional_fields_default_none() -> None:
    e = _entry()
    assert e.details is None
    assert e.exit_code is None


def test_clear_removes_file(audit: Audit, audit_file: Path) -> None:
    audit.record(_entry())
    assert audit_file.exists()
    audit.clear()
    assert not audit_file.exists()
    assert audit.all() == []


def test_clear_on_missing_file_is_safe(audit: Audit) -> None:
    audit.clear()  # should not raise


def test_record_creates_parent_dirs(tmp_path: Path) -> None:
    deep = tmp_path / "a" / "b" / "audit.jsonl"
    a = Audit(deep)
    a.record(_entry())
    assert deep.exists()
