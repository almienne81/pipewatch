"""Tests for pipewatch.retry."""
from __future__ import annotations

import pytest

from pipewatch.retry import (
    AttemptResult,
    RetryPolicy,
    parse_retry_policy,
    run_with_retry,
)


def _make_result(exit_code: int, attempt: int = 1) -> AttemptResult:
    return AttemptResult(
        attempt=attempt,
        exit_code=exit_code,
        stdout="",
        stderr="",
        duration=0.1,
    )


# ---------------------------------------------------------------------------
# RetryPolicy.should_retry
# ---------------------------------------------------------------------------

def test_no_retry_on_success():
    policy = RetryPolicy(max_attempts=3)
    assert policy.should_retry(exit_code=0, attempt=1) is False


def test_no_retry_when_max_attempts_reached():
    policy = RetryPolicy(max_attempts=2)
    assert policy.should_retry(exit_code=1, attempt=2) is False


def test_retry_on_failure_within_limit():
    policy = RetryPolicy(max_attempts=3)
    assert policy.should_retry(exit_code=1, attempt=1) is True


def test_retry_on_codes_filters_correctly():
    policy = RetryPolicy(max_attempts=3, retry_on_codes=[1, 2])
    assert policy.should_retry(exit_code=3, attempt=1) is False
    assert policy.should_retry(exit_code=1, attempt=1) is True


def test_wait_seconds_applies_backoff():
    policy = RetryPolicy(delay_seconds=4.0, backoff_factor=2.0)
    assert policy.wait_seconds(0) == pytest.approx(4.0)
    assert policy.wait_seconds(1) == pytest.approx(8.0)
    assert policy.wait_seconds(2) == pytest.approx(16.0)


# ---------------------------------------------------------------------------
# run_with_retry
# ---------------------------------------------------------------------------

def test_single_attempt_success():
    policy = RetryPolicy(max_attempts=3)
    calls = []

    def runner():
        calls.append(1)
        return _make_result(0)

    results = run_with_retry(runner, policy, sleep_fn=lambda _: None)
    assert len(results) == 1
    assert results[0].exit_code == 0
    assert len(calls) == 1


def test_retries_until_success():
    policy = RetryPolicy(max_attempts=3, delay_seconds=0)
    outcomes = [1, 1, 0]
    idx = [0]

    def runner():
        code = outcomes[idx[0]]
        idx[0] += 1
        return _make_result(code)

    slept: list = []
    results = run_with_retry(runner, policy, sleep_fn=slept.append)
    assert len(results) == 3
    assert results[-1].exit_code == 0
    assert len(slept) == 2


def test_exhausts_all_attempts_on_persistent_failure():
    policy = RetryPolicy(max_attempts=3)

    def runner():
        return _make_result(1)

    results = run_with_retry(runner, policy, sleep_fn=lambda _: None)
    assert len(results) == 3
    assert all(r.exit_code == 1 for r in results)


# ---------------------------------------------------------------------------
# parse_retry_policy
# ---------------------------------------------------------------------------

def test_parse_valid_policy():
    p = parse_retry_policy(max_attempts=3, delay=2.0, backoff=1.5)
    assert p.max_attempts == 3
    assert p.delay_seconds == pytest.approx(2.0)
    assert p.backoff_factor == pytest.approx(1.5)


def test_parse_invalid_max_attempts_raises():
    with pytest.raises(ValueError, match="max_attempts"):
        parse_retry_policy(max_attempts=0)


def test_parse_invalid_backoff_raises():
    with pytest.raises(ValueError, match="backoff_factor"):
        parse_retry_policy(backoff=0.5)


def test_parse_invalid_delay_raises():
    with pytest.raises(ValueError, match="delay"):
        parse_retry_policy(delay=-1)
