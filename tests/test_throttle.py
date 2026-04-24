"""Tests for pipewatch.throttle."""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from pipewatch.throttle import DEFAULT_COOLDOWN_SECONDS, Throttle, ThrottleState

PIPELINE = "my-pipeline"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def throttle() -> Throttle:
    return Throttle(cooldown_seconds=60)


@pytest.fixture()
def state_file(tmp_path: Path) -> Path:
    return tmp_path / "throttle_state.json"


# ---------------------------------------------------------------------------
# Basic suppression logic
# ---------------------------------------------------------------------------


def test_new_key_is_not_suppressed(throttle: Throttle) -> None:
    assert throttle.is_suppressed(PIPELINE) is False


def test_suppressed_within_cooldown(throttle: Throttle) -> None:
    now = time.time()
    throttle.record(PIPELINE, now=now)
    assert throttle.is_suppressed(PIPELINE, now=now + 30) is True


def test_not_suppressed_after_cooldown(throttle: Throttle) -> None:
    now = time.time()
    throttle.record(PIPELINE, now=now)
    assert throttle.is_suppressed(PIPELINE, now=now + 61) is False


def test_exactly_at_cooldown_boundary_is_not_suppressed(throttle: Throttle) -> None:
    now = time.time()
    throttle.record(PIPELINE, now=now)
    # elapsed == cooldown_seconds → not suppressed
    assert throttle.is_suppressed(PIPELINE, now=now + 60) is False


# ---------------------------------------------------------------------------
# record / reset
# ---------------------------------------------------------------------------


def test_record_increments_count(throttle: Throttle) -> None:
    now = time.time()
    throttle.record(PIPELINE, now=now)
    throttle.record(PIPELINE, now=now + 70)  # after cooldown, but still counts
    state = throttle.state_for(PIPELINE)
    assert state is not None
    assert state.count == 2


def test_reset_removes_state(throttle: Throttle) -> None:
    throttle.record(PIPELINE)
    throttle.reset(PIPELINE)
    assert throttle.state_for(PIPELINE) is None
    assert throttle.is_suppressed(PIPELINE) is False


def test_reset_unknown_key_is_noop(throttle: Throttle) -> None:
    throttle.reset("nonexistent")  # must not raise


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------


def test_state_persisted_to_file(state_file: Path) -> None:
    t = Throttle(cooldown_seconds=60, state_path=state_file)
    now = 1_700_000_000.0
    t.record(PIPELINE, now=now)
    assert state_file.exists()
    data = json.loads(state_file.read_text())
    assert PIPELINE in data
    assert data[PIPELINE]["count"] == 1
    assert data[PIPELINE]["last_notified_at"] == now


def test_state_loaded_from_existing_file(state_file: Path) -> None:
    payload = {PIPELINE: {"last_notified_at": time.time(), "count": 3}}
    state_file.write_text(json.dumps(payload))
    t = Throttle(cooldown_seconds=60, state_path=state_file)
    state = t.state_for(PIPELINE)
    assert state is not None
    assert state.count == 3
    assert t.is_suppressed(PIPELINE) is True


def test_default_cooldown_constant() -> None:
    assert DEFAULT_COOLDOWN_SECONDS == 300
