"""Tests for pipewatch.leakybucket."""
import json
import time
import pytest
from pathlib import Path

from pipewatch.leakybucket import LeakyBucket, LeakyBucketError, LeakyBucketPolicy


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def bucket_file(tmp_path: Path) -> Path:
    return tmp_path / "leakybucket.json"


@pytest.fixture()
def policy() -> LeakyBucketPolicy:
    return LeakyBucketPolicy(capacity=5.0, leak_rate=1.0)


@pytest.fixture()
def bucket(bucket_file: Path, policy: LeakyBucketPolicy) -> LeakyBucket:
    return LeakyBucket(bucket_file, policy)


# ---------------------------------------------------------------------------
# Policy validation
# ---------------------------------------------------------------------------

def test_policy_defaults():
    p = LeakyBucketPolicy()
    assert p.capacity == 10.0
    assert p.leak_rate == 1.0


def test_policy_zero_capacity_raises():
    with pytest.raises(LeakyBucketError, match="capacity"):
        LeakyBucketPolicy(capacity=0.0)


def test_policy_negative_leak_rate_raises():
    with pytest.raises(LeakyBucketError, match="leak_rate"):
        LeakyBucketPolicy(leak_rate=-1.0)


def test_policy_to_dict_round_trip():
    p = LeakyBucketPolicy(capacity=3.0, leak_rate=0.5)
    assert LeakyBucketPolicy.from_dict(p.to_dict()) == p


# ---------------------------------------------------------------------------
# Bucket behaviour
# ---------------------------------------------------------------------------

def test_new_key_level_is_zero(bucket: LeakyBucket):
    assert bucket.level("job_a") == 0.0


def test_allow_within_capacity(bucket: LeakyBucket):
    assert bucket.allow("job_a") is True


def test_allow_fills_bucket(bucket: LeakyBucket):
    now = time.time()
    for _ in range(5):
        bucket.allow("job_a", now=now)
    assert bucket.level("job_a", now=now) == pytest.approx(5.0)


def test_allow_rejects_when_full(bucket: LeakyBucket):
    now = time.time()
    for _ in range(5):
        bucket.allow("job_a", now=now)
    assert bucket.allow("job_a", now=now) is False


def test_level_decreases_after_time(bucket: LeakyBucket):
    t0 = time.time()
    bucket.allow("job_a", cost=4.0, now=t0)
    level_after = bucket.level("job_a", now=t0 + 2.0)  # 2 seconds later → -2 tokens
    assert level_after == pytest.approx(2.0)


def test_reset_clears_bucket(bucket: LeakyBucket):
    now = time.time()
    bucket.allow("job_a", cost=3.0, now=now)
    bucket.reset("job_a")
    assert bucket.level("job_a") == 0.0


def test_empty_key_raises(bucket: LeakyBucket):
    with pytest.raises(LeakyBucketError, match="key"):
        bucket.allow("")


def test_state_persists_across_instances(bucket_file: Path, policy: LeakyBucketPolicy):
    now = time.time()
    b1 = LeakyBucket(bucket_file, policy)
    b1.allow("job_a", cost=3.0, now=now)

    b2 = LeakyBucket(bucket_file, policy)
    assert b2.level("job_a", now=now) == pytest.approx(3.0)


def test_different_keys_are_independent(bucket: LeakyBucket):
    now = time.time()
    for _ in range(5):
        bucket.allow("job_a", now=now)
    assert bucket.allow("job_b", now=now) is True
