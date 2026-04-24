"""Integration-style tests: retry logic wired to a real subprocess-like runner."""
from __future__ import annotations

import time
from unittest.mock import patch

import pytest

from pipewatch.retry import AttemptResult, RetryPolicy, run_with_retry


def _make_runner(exit_codes: list[int]):
    """Return a runner that cycles through the given exit codes."""
    codes = list(exit_codes)
    idx = [0]
    start = [time.monotonic()]

    def runner() -> AttemptResult:
        code = codes[idx[0]] if idx[0] < len(codes) else codes[-1]
        idx[0] += 1
        return AttemptResult(
            attempt=idx[0],
            exit_code=code,
            stdout="output",
            stderr="" if code == 0 else "error",
            duration=time.monotonic() - start[0],
        )

    return runner


def test_immediate_success_no_sleep():
    slept: list[float] = []
    policy = RetryPolicy(max_attempts=5)
    results = run_with_retry(
        _make_runner([0]),
        policy,
        sleep_fn=slept.append,
    )
    assert len(results) == 1
    assert results[0].exit_code == 0
    assert slept == []


def test_fail_twice_then_succeed():
    slept: list[float] = []
    policy = RetryPolicy(max_attempts=5, delay_seconds=1.0, backoff_factor=2.0)
    results = run_with_retry(
        _make_runner([1, 1, 0]),
        policy,
        sleep_fn=slept.append,
    )
    assert len(results) == 3
    assert results[-1].exit_code == 0
    # Delays: 1.0 * 2^0 = 1.0, 1.0 * 2^1 = 2.0
    assert slept == pytest.approx([1.0, 2.0])


def test_all_attempts_fail_returns_all_results():
    policy = RetryPolicy(max_attempts=3, delay_seconds=0.0)
    results = run_with_retry(
        _make_runner([2, 2, 2]),
        policy,
        sleep_fn=lambda _: None,
    )
    assert len(results) == 3
    assert all(r.exit_code == 2 for r in results)


def test_retry_on_codes_skips_unmatched_code():
    """Exit code 3 is not in retry_on_codes, so we stop after first attempt."""
    policy = RetryPolicy(max_attempts=5, retry_on_codes=[1, 2])
    results = run_with_retry(
        _make_runner([3]),
        policy,
        sleep_fn=lambda _: None,
    )
    assert len(results) == 1
    assert results[0].exit_code == 3


def test_attempt_numbers_are_sequential():
    policy = RetryPolicy(max_attempts=3, delay_seconds=0.0)
    results = run_with_retry(
        _make_runner([1, 1, 0]),
        policy,
        sleep_fn=lambda _: None,
    )
    assert [r.attempt for r in results] == [1, 2, 3]
