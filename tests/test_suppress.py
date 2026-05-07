"""Tests for pipewatch.suppress."""

from __future__ import annotations

import time

import pytest

from pipewatch.suppress import Suppress, SuppressEntry, SuppressError


@pytest.fixture()
def sup_file(tmp_path):
    return tmp_path / "suppress.json"


@pytest.fixture()
def sup(sup_file):
    return Suppress(sup_file)


# ---------------------------------------------------------------------------
# SuppressEntry serialisation
# ---------------------------------------------------------------------------

def test_entry_to_dict_round_trip():
    entry = SuppressEntry(job="etl", suppressed_until=9999.0, reason="maintenance")
    restored = SuppressEntry.from_dict(entry.to_dict())
    assert restored.job == "etl"
    assert restored.suppressed_until == 9999.0
    assert restored.reason == "maintenance"


def test_entry_from_dict_missing_reason_defaults_empty():
    data = {"job": "etl", "suppressed_until": 1234.0}
    entry = SuppressEntry.from_dict(data)
    assert entry.reason == ""


# ---------------------------------------------------------------------------
# is_suppressed
# ---------------------------------------------------------------------------

def test_new_job_is_not_suppressed(sup):
    assert sup.is_suppressed("unknown-job") is False


def test_suppressed_job_returns_true(sup):
    sup.suppress("etl", duration_seconds=60)
    assert sup.is_suppressed("etl") is True


def test_expired_suppression_returns_false(sup):
    sup.suppress("etl", duration_seconds=0.01)
    time.sleep(0.05)
    assert sup.is_suppressed("etl") is False


# ---------------------------------------------------------------------------
# suppress
# ---------------------------------------------------------------------------

def test_suppress_returns_entry(sup):
    entry = sup.suppress("etl", 30, reason="planned")
    assert isinstance(entry, SuppressEntry)
    assert entry.job == "etl"
    assert entry.reason == "planned"


def test_suppress_zero_duration_raises(sup):
    with pytest.raises(SuppressError):
        sup.suppress("etl", 0)


def test_suppress_negative_duration_raises(sup):
    with pytest.raises(SuppressError):
        sup.suppress("etl", -5)


def test_suppress_empty_job_raises(sup):
    with pytest.raises(SuppressError):
        sup.suppress("", 60)


# ---------------------------------------------------------------------------
# release
# ---------------------------------------------------------------------------

def test_release_existing_entry_returns_true(sup):
    sup.suppress("etl", 60)
    assert sup.release("etl") is True
    assert sup.is_suppressed("etl") is False


def test_release_missing_entry_returns_false(sup):
    assert sup.release("nonexistent") is False


# ---------------------------------------------------------------------------
# active_entries / all_entries
# ---------------------------------------------------------------------------

def test_active_entries_excludes_expired(sup):
    sup.suppress("etl", 60)
    sup.suppress("loader", 0.01)
    time.sleep(0.05)
    active = sup.active_entries()
    jobs = [e.job for e in active]
    assert "etl" in jobs
    assert "loader" not in jobs


def test_all_entries_includes_expired(sup):
    sup.suppress("etl", 60)
    sup.suppress("loader", 0.01)
    time.sleep(0.05)
    assert len(sup.all_entries()) == 2


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

def test_state_persists_across_instances(sup_file):
    s1 = Suppress(sup_file)
    s1.suppress("etl", 120)
    s2 = Suppress(sup_file)
    assert s2.is_suppressed("etl") is True
