"""Tests for pipewatch.status."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from pipewatch.history import HistoryEntry
from pipewatch.status import PipelineStatus, collect_status


def _entry(exit_code: int, duration: float = 1.0) -> HistoryEntry:
    return HistoryEntry(
        started_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        exit_code=exit_code,
        duration_seconds=duration,
        command="echo test",
    )


@pytest.fixture
def empty_history():
    h = MagicMock()
    h.all.return_value = []
    return h


@pytest.fixture
def mixed_history():
    h = MagicMock()
    h.all.return_value = [
        _entry(0, 2.0),
        _entry(1, 3.5),
        _entry(0, 1.0),
    ]
    return h


def test_empty_history_produces_zero_counts(empty_history):
    status = collect_status("my-pipeline", empty_history)
    assert status.total_runs == 0
    assert status.successful_runs == 0
    assert status.failed_runs == 0


def test_empty_history_success_rate_is_none(empty_history):
    status = collect_status("my-pipeline", empty_history)
    assert status.success_rate is None


def test_empty_history_last_fields_are_none(empty_history):
    status = collect_status("my-pipeline", empty_history)
    assert status.last_run_at is None
    assert status.last_exit_code is None
    assert status.last_duration_seconds is None


def test_mixed_history_counts(mixed_history):
    status = collect_status("pipe", mixed_history)
    assert status.total_runs == 3
    assert status.successful_runs == 2
    assert status.failed_runs == 1


def test_mixed_history_success_rate(mixed_history):
    status = collect_status("pipe", mixed_history)
    assert abs(status.success_rate - 2 / 3) < 1e-9


def test_last_entry_fields_reflect_most_recent(mixed_history):
    status = collect_status("pipe", mixed_history)
    assert status.last_exit_code == 0
    assert status.last_duration_seconds == pytest.approx(1.0)


def test_is_healthy_true_when_last_exit_zero(mixed_history):
    status = collect_status("pipe", mixed_history)
    assert status.is_healthy is True


def test_is_healthy_false_when_last_exit_nonzero():
    h = MagicMock()
    h.all.return_value = [_entry(0), _entry(1)]
    status = collect_status("pipe", h)
    assert status.is_healthy is False


def test_to_dict_contains_expected_keys(mixed_history):
    status = collect_status("pipe", mixed_history)
    d = status.to_dict()
    for key in ("name", "last_run_at", "last_exit_code", "total_runs",
                "successful_runs", "failed_runs", "success_rate", "is_healthy", "tags"):
        assert key in d


def test_tags_passed_through():
    h = MagicMock()
    h.all.return_value = []
    tags = MagicMock()
    tags.__iter__ = MagicMock(return_value=iter([("env", "prod")]))
    status = collect_status("pipe", h, tags=tags)
    assert status.tags == {"env": "prod"}
