"""Tests for pipewatch.digest."""
from __future__ import annotations

import time
from unittest.mock import patch

import pytest

from pipewatch.digest import DigestEntry, build_digest, format_digest
from pipewatch.history import History


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _entry(exit_code: int = 0, age_seconds: float = 0.0) -> dict:
    """Return a raw history entry dict."""
    return {
        "timestamp": time.time() - age_seconds,
        "exit_code": exit_code,
        "command": "echo test",
        "duration": 0.1,
    }


@pytest.fixture()
def history_file(tmp_path):
    return str(tmp_path / "history.json")


@pytest.fixture()
def history(history_file):
    return History(history_file)


# ---------------------------------------------------------------------------
# DigestEntry unit tests
# ---------------------------------------------------------------------------

def test_digest_entry_to_dict_contains_all_keys():
    e = DigestEntry(
        pipeline="my-pipe",
        total_runs=5,
        successes=4,
        failures=1,
        success_rate=0.8,
        last_run_at="2024-01-01T00:00:00+00:00",
        last_status="success",
    )
    d = e.to_dict()
    assert set(d.keys()) == {
        "pipeline", "total_runs", "successes", "failures",
        "success_rate", "last_run_at", "last_status",
    }


# ---------------------------------------------------------------------------
# build_digest
# ---------------------------------------------------------------------------

def test_empty_history_produces_zero_counts(history):
    digest = build_digest(history, pipeline="pipe", window_hours=24)
    assert len(digest.entries) == 1
    e = digest.entries[0]
    assert e.total_runs == 0
    assert e.successes == 0
    assert e.failures == 0
    assert e.success_rate is None
    assert e.last_run_at is None
    assert e.last_status is None


def test_counts_within_window(history):
    history.append(_entry(exit_code=0, age_seconds=100))
    history.append(_entry(exit_code=1, age_seconds=200))
    history.append(_entry(exit_code=0, age_seconds=300))

    digest = build_digest(history, pipeline="pipe", window_hours=1)
    e = digest.entries[0]
    assert e.total_runs == 3
    assert e.successes == 2
    assert e.failures == 1
    assert pytest.approx(e.success_rate, rel=1e-3) == 2 / 3


def test_entries_outside_window_excluded(history):
    history.append(_entry(exit_code=0, age_seconds=100))          # inside 1 h
    history.append(_entry(exit_code=1, age_seconds=7300))         # outside 2 h

    digest = build_digest(history, pipeline="pipe", window_hours=2)
    e = digest.entries[0]
    assert e.total_runs == 1
    assert e.successes == 1


def test_last_status_reflects_most_recent_entry(history):
    history.append(_entry(exit_code=0, age_seconds=600))
    history.append(_entry(exit_code=1, age_seconds=60))

    digest = build_digest(history, pipeline="pipe", window_hours=1)
    assert digest.entries[0].last_status == "failure"


# ---------------------------------------------------------------------------
# format_digest
# ---------------------------------------------------------------------------

def test_format_digest_contains_pipeline_name(history):
    digest = build_digest(history, pipeline="my-pipeline", window_hours=24)
    text = format_digest(digest)
    assert "my-pipeline" in text


def test_format_digest_shows_window(history):
    digest = build_digest(history, pipeline="p", window_hours=48)
    text = format_digest(digest)
    assert "48" in text


def test_format_digest_json_round_trip(history):
    import json
    history.append(_entry(exit_code=0, age_seconds=10))
    digest = build_digest(history, pipeline="p", window_hours=24)
    data = json.loads(json.dumps(digest.to_dict()))
    assert data["window_hours"] == 24
    assert data["entries"][0]["total_runs"] == 1
