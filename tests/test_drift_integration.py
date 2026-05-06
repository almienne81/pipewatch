"""Integration tests for drift detection across multiple tracker instances."""
from pathlib import Path

import pytest

from pipewatch.drift import DriftPolicy, DriftTracker


@pytest.fixture
def drift_file(tmp_path: Path) -> Path:
    return tmp_path / "drift.json"


def test_state_persists_across_instances(drift_file: Path):
    t1 = DriftTracker(path=drift_file)
    for v in [1.0, 1.1, 0.9]:
        t1.record(v)
    t2 = DriftTracker(path=drift_file)
    assert len(t2.samples()) == 3


def test_drift_detected_after_stable_baseline(drift_file: Path):
    policy = DriftPolicy(baseline_window=4, z_score_threshold=2.0)
    t = DriftTracker(path=drift_file, policy=policy)
    stable = [1.0, 1.0, 1.0, 1.0]
    for v in stable:
        t.record(v)
    result = t.record(50.0)
    assert result.is_drifted is True


def test_no_drift_within_normal_variance(drift_file: Path):
    policy = DriftPolicy(baseline_window=5, z_score_threshold=3.0)
    t = DriftTracker(path=drift_file, policy=policy)
    for v in [2.0, 2.1, 1.9, 2.05, 1.95]:
        t.record(v)
    result = t.record(2.03)
    assert result.is_drifted is False


def test_clear_then_rerecord(drift_file: Path):
    t1 = DriftTracker(path=drift_file)
    t1.record(1.0)
    t1.record(2.0)
    t1.clear()
    t2 = DriftTracker(path=drift_file)
    assert t2.samples() == []
    t2.record(3.0)
    assert len(t2.samples()) == 1


def test_window_limits_baseline_samples(drift_file: Path):
    policy = DriftPolicy(baseline_window=3, z_score_threshold=2.0)
    t = DriftTracker(path=drift_file, policy=policy)
    # record many stable values then a spike
    for _ in range(10):
        t.record(1.0)
    result = t.record(100.0)
    # baseline is computed from last 3 samples (all 1.0), spike should be detected
    assert result.is_drifted is True
    assert result.baseline_mean == pytest.approx(1.0)
