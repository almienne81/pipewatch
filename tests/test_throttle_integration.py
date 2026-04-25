"""Integration tests for throttle + notifier interaction.

Verifies that ThrottleState persists across Throttle instances and that
the suppression logic correctly gates repeated notifications.
"""

import time
from pathlib import Path

import pytest

from pipewatch.throttle import Throttle, ThrottleState


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_throttle(tmp_path: Path, cooldown: int = 60) -> Throttle:
    state_file = tmp_path / "throttle_state.json"
    return Throttle(state_file=state_file, default_cooldown=cooldown)


# ---------------------------------------------------------------------------
# Persistence across instances
# ---------------------------------------------------------------------------

def test_state_persists_across_instances(tmp_path):
    """A suppressed key should still be suppressed when a new Throttle is
    created pointing at the same state file."""
    t1 = _make_throttle(tmp_path, cooldown=3600)
    assert not t1.is_suppressed("pipeline.a")
    t1.record("pipeline.a")

    # Fresh instance — reads the same file
    t2 = _make_throttle(tmp_path, cooldown=3600)
    assert t2.is_suppressed("pipeline.a"), (
        "Key should still be suppressed after reloading state from disk"
    )


def test_different_keys_are_independent(tmp_path):
    """Recording one key must not suppress a different key."""
    t = _make_throttle(tmp_path, cooldown=3600)
    t.record("pipeline.a")

    assert not t.is_suppressed("pipeline.b"), (
        "Unrelated key must not be affected by another key's record"
    )


def test_expired_key_is_not_suppressed_on_reload(tmp_path):
    """A key whose cooldown has elapsed must not be suppressed even after
    the state file is reloaded by a new Throttle instance."""
    t1 = _make_throttle(tmp_path, cooldown=0)  # expires immediately
    t1.record("pipeline.a")

    # Allow the zero-second cooldown to expire
    time.sleep(0.05)

    t2 = _make_throttle(tmp_path, cooldown=0)
    assert not t2.is_suppressed("pipeline.a"), (
        "Key with elapsed cooldown must not be suppressed"
    )


# ---------------------------------------------------------------------------
# Simulated notification gate
# ---------------------------------------------------------------------------

def test_notify_called_only_once_during_cooldown(tmp_path):
    """Simulate the pattern used in the monitor: only send a notification
    when the throttle permits it."""
    notifications_sent = []

    def _fake_notify(message: str) -> None:
        notifications_sent.append(message)

    t = _make_throttle(tmp_path, cooldown=3600)
    key = "job.daily_etl"

    for attempt in range(5):
        if not t.is_suppressed(key):
            _fake_notify(f"failure on attempt {attempt}")
            t.record(key)

    assert len(notifications_sent) == 1, (
        f"Expected exactly 1 notification, got {len(notifications_sent)}"
    )
    assert "attempt 0" in notifications_sent[0]


def test_notify_resets_after_cooldown(tmp_path):
    """After the cooldown expires the throttle should allow a second
    notification."""
    notifications_sent = []

    def _fake_notify(message: str) -> None:
        notifications_sent.append(message)

    t = _make_throttle(tmp_path, cooldown=0)  # instant expiry
    key = "job.fast_expiry"

    # First notification
    if not t.is_suppressed(key):
        _fake_notify("first")
        t.record(key)

    time.sleep(0.05)  # let cooldown expire

    # Second notification — should be allowed
    if not t.is_suppressed(key):
        _fake_notify("second")
        t.record(key)

    assert len(notifications_sent) == 2, (
        f"Expected 2 notifications after cooldown reset, got {len(notifications_sent)}"
    )
