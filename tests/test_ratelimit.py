"""Tests for pipewatch.ratelimit."""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from pipewatch.ratelimit import RateLimitError, RateLimitPolicy, RateLimiter


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def state_file(tmp_path: Path) -> Path:
    return tmp_path / "ratelimit.json"


@pytest.fixture()
def policy() -> RateLimitPolicy:
    return RateLimitPolicy(max_alerts=3, window_seconds=60)


@pytest.fixture()
def limiter(policy: RateLimitPolicy, state_file: Path) -> RateLimiter:
    return RateLimiter(policy=policy, state_path=state_file)


# ---------------------------------------------------------------------------
# RateLimitPolicy
# ---------------------------------------------------------------------------


def test_policy_defaults() -> None:
    p = RateLimitPolicy()
    assert p.max_alerts == 5
    assert p.window_seconds == 3600


def test_policy_invalid_max_alerts_raises() -> None:
    with pytest.raises(RateLimitError):
        RateLimitPolicy(max_alerts=0)


def test_policy_invalid_window_raises() -> None:
    with pytest.raises(RateLimitError):
        RateLimitPolicy(window_seconds=0)


def test_policy_round_trip() -> None:
    p = RateLimitPolicy(max_alerts=10, window_seconds=300)
    assert RateLimitPolicy.from_dict(p.to_dict()) == p


# ---------------------------------------------------------------------------
# RateLimiter — basic allow / deny
# ---------------------------------------------------------------------------


def test_new_key_is_allowed(limiter: RateLimiter) -> None:
    assert limiter.is_allowed("pipeline.a") is True


def test_allowed_until_limit_reached(limiter: RateLimiter) -> None:
    now = time.time()
    for _ in range(3):
        assert limiter.is_allowed("pipeline.a", now=now) is True
        limiter.record("pipeline.a", now=now)
    assert limiter.is_allowed("pipeline.a", now=now) is False


def test_allowed_again_after_window_expires(limiter: RateLimiter) -> None:
    now = time.time()
    for _ in range(3):
        limiter.record("pipeline.a", now=now)
    # Move past the 60-second window
    future = now + 61
    assert limiter.is_allowed("pipeline.a", now=future) is True


def test_different_keys_are_independent(limiter: RateLimiter) -> None:
    now = time.time()
    for _ in range(3):
        limiter.record("pipeline.a", now=now)
    # key b is unaffected
    assert limiter.is_allowed("pipeline.b", now=now) is True


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------


def test_state_persists_across_instances(
    policy: RateLimitPolicy, state_file: Path
) -> None:
    now = time.time()
    l1 = RateLimiter(policy=policy, state_path=state_file)
    for _ in range(3):
        l1.record("pipeline.x", now=now)

    l2 = RateLimiter(policy=policy, state_path=state_file)
    assert l2.is_allowed("pipeline.x", now=now) is False


def test_corrupt_state_file_treated_as_empty(
    policy: RateLimitPolicy, state_file: Path
) -> None:
    state_file.write_text("not-json")
    l = RateLimiter(policy=policy, state_path=state_file)
    assert l.is_allowed("pipeline.x") is True
