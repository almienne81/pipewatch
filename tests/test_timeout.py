"""Unit tests for pipewatch.timeout."""

from __future__ import annotations

import time
import pytest

from pipewatch.timeout import TimeoutPolicy, TimeoutError, enforce, _TimeoutContext


# ---------------------------------------------------------------------------
# TimeoutPolicy
# ---------------------------------------------------------------------------

def test_policy_disabled_when_none():
    p = TimeoutPolicy(seconds=None)
    assert not p.is_enabled()


def test_policy_disabled_when_zero():
    p = TimeoutPolicy(seconds=0)
    assert not p.is_enabled()


def test_policy_enabled_for_positive_value():
    p = TimeoutPolicy(seconds=10)
    assert p.is_enabled()


def test_to_dict_round_trip():
    p = TimeoutPolicy(seconds=30, kill_on_timeout=False)
    restored = TimeoutPolicy.from_dict(p.to_dict())
    assert restored.seconds == 30
    assert restored.kill_on_timeout is False


def test_from_dict_defaults():
    p = TimeoutPolicy.from_dict({})
    assert p.seconds is None
    assert p.kill_on_timeout is True


# ---------------------------------------------------------------------------
# enforce — disabled policy passes through
# ---------------------------------------------------------------------------

def test_enforce_disabled_policy_calls_fn():
    policy = TimeoutPolicy(seconds=None)
    result = enforce(policy, lambda x: x * 2, 21)
    assert result == 42


def test_enforce_enabled_policy_returns_value():
    policy = TimeoutPolicy(seconds=5)
    result = enforce(policy, lambda: "ok")
    assert result == "ok"


# ---------------------------------------------------------------------------
# _TimeoutContext — SIGALRM integration (Unix only)
# ---------------------------------------------------------------------------

def test_timeout_context_raises_on_slow_fn():
    """A function that sleeps longer than the alarm should raise TimeoutError."""
    import platform
    if platform.system() == "Windows":
        pytest.skip("SIGALRM not available on Windows")

    with pytest.raises(TimeoutError) as exc_info:
        with _TimeoutContext(1):
            time.sleep(5)

    assert exc_info.value.seconds == 1


def test_timeout_error_message():
    err = TimeoutError(7.5)
    assert "7.5" in str(err)
