"""Tests for pipewatch.concurrency."""
from __future__ import annotations

import os
import time
from pathlib import Path

import pytest

from pipewatch.concurrency import (
    ConcurrencyError,
    ConcurrencyLimiter,
    ConcurrencyPolicy,
    ConcurrencySlot,
)


# ---------------------------------------------------------------------------
# Policy validation
# ---------------------------------------------------------------------------

def test_default_policy_has_expected_values():
    p = ConcurrencyPolicy()
    assert p.max_concurrent == 1
    assert p.timeout_seconds is None


def test_invalid_max_concurrent_raises():
    with pytest.raises(ConcurrencyError, match="max_concurrent"):
        ConcurrencyPolicy(max_concurrent=0)


def test_negative_timeout_raises():
    with pytest.raises(ConcurrencyError, match="timeout_seconds"):
        ConcurrencyPolicy(max_concurrent=2, timeout_seconds=-1.0)


def test_policy_to_dict_round_trip():
    p = ConcurrencyPolicy(max_concurrent=3, timeout_seconds=30.0)
    assert ConcurrencyPolicy.from_dict(p.to_dict()) == p


# ---------------------------------------------------------------------------
# Slot serialisation
# ---------------------------------------------------------------------------

def test_slot_to_dict_round_trip():
    s = ConcurrencySlot(pid=1234, job="etl", started_at=1_000_000.0)
    assert ConcurrencySlot.from_dict(s.to_dict()) == s


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def state_file(tmp_path: Path) -> Path:
    return tmp_path / "concurrency.json"


@pytest.fixture()
def limiter(state_file: Path) -> ConcurrencyLimiter:
    return ConcurrencyLimiter(state_file, ConcurrencyPolicy(max_concurrent=2))


# ---------------------------------------------------------------------------
# Limiter behaviour
# ---------------------------------------------------------------------------

def test_active_slots_empty_initially(limiter: ConcurrencyLimiter):
    assert limiter.active_slots() == []


def test_acquire_returns_slot(limiter: ConcurrencyLimiter):
    slot = limiter.acquire("job-a")
    assert slot.pid == os.getpid()
    assert slot.job == "job-a"


def test_acquire_increments_active_count(limiter: ConcurrencyLimiter):
    limiter.acquire("job-a")
    assert len(limiter.active_slots()) == 1


def test_release_removes_slot(limiter: ConcurrencyLimiter):
    slot = limiter.acquire("job-a")
    limiter.release(slot)
    assert limiter.active_slots() == []


def test_limit_enforced(state_file: Path):
    policy = ConcurrencyPolicy(max_concurrent=1)
    lim = ConcurrencyLimiter(state_file, policy)
    lim.acquire("job-a")
    with pytest.raises(ConcurrencyError, match="limit"):
        lim.acquire("job-b")


def test_clear_removes_all_slots(limiter: ConcurrencyLimiter):
    limiter.acquire("job-a")
    limiter.acquire("job-b")
    limiter.clear()
    assert limiter.active_slots() == []


def test_stale_pid_is_pruned(state_file: Path):
    """Slots with dead PIDs are automatically pruned."""
    policy = ConcurrencyPolicy(max_concurrent=1)
    lim = ConcurrencyLimiter(state_file, policy)
    # Inject a slot with a PID that cannot exist (PID 0 is never a real process)
    dead_slot = ConcurrencySlot(pid=99999999, job="ghost", started_at=time.time())
    import json
    state_file.write_text(json.dumps([dead_slot.to_dict()]))
    # Should be able to acquire because the dead slot is pruned
    slot = lim.acquire("job-live")
    assert slot.job == "job-live"
