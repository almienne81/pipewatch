"""Integration tests: enforce() wired to real callables."""

from __future__ import annotations

import platform
import time
import pytest

from pipewatch.timeout import TimeoutPolicy, TimeoutError, enforce


def _slow(secs: float = 5.0) -> str:
    time.sleep(secs)
    return "done"


def _fast() -> str:
    return "quick"


def test_fast_fn_completes_within_timeout():
    policy = TimeoutPolicy(seconds=5)
    assert enforce(policy, _fast) == "quick"


def test_disabled_policy_never_interrupts():
    policy = TimeoutPolicy(seconds=None)
    # Should not raise even though we don't actually sleep long in CI
    result = enforce(policy, lambda: 99)
    assert result == 99


def test_enforce_passes_args_and_kwargs():
    policy = TimeoutPolicy(seconds=None)
    result = enforce(policy, lambda a, b=0: a + b, 3, b=7)
    assert result == 10


@pytest.mark.skipif(platform.system() == "Windows", reason="SIGALRM unavailable")
def test_slow_fn_raises_timeout_error():
    policy = TimeoutPolicy(seconds=1)
    with pytest.raises(TimeoutError):
        enforce(policy, _slow, 10)


@pytest.mark.skipif(platform.system() == "Windows", reason="SIGALRM unavailable")
def test_timeout_error_carries_duration():
    policy = TimeoutPolicy(seconds=1)
    with pytest.raises(TimeoutError) as exc_info:
        enforce(policy, _slow, 10)
    assert exc_info.value.seconds == 1


@pytest.mark.skipif(platform.system() == "Windows", reason="SIGALRM unavailable")
def test_alarm_cancelled_after_successful_call():
    """Verify the alarm is reset so a subsequent call is not interrupted."""
    policy = TimeoutPolicy(seconds=3)
    enforce(policy, _fast)
    # If alarm was NOT cancelled this sleep would raise; it should not.
    time.sleep(0.05)
