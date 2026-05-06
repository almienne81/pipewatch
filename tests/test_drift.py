"""Unit tests for pipewatch.drift."""
import json
import pytest
from pathlib import Path

from pipewatch.drift import DriftError, DriftPolicy, DriftResult, DriftTracker


@pytest.fixture
def drift_file(tmp_path: Path) -> Path:
    return tmp_path / "drift.json"


@pytest.fixture
def tracker(drift_file: Path) -> DriftTracker:
    return DriftTracker(path=drift_file)


# --- DriftPolicy ---

def test_default_policy_has_expected_values():
    p = DriftPolicy()
    assert p.baseline_window == 10
    assert p.z_score_threshold == 2.0


def test_window_less_than_two_raises():
    with pytest.raises(DriftError, match="baseline_window"):
        DriftPolicy(baseline_window=1)


def test_threshold_zero_raises():
    with pytest.raises(DriftError, match="z_score_threshold"):
        DriftPolicy(z_score_threshold=0.0)


def test_threshold_negative_raises():
    with pytest.raises(DriftError, match="z_score_threshold"):
        DriftPolicy(z_score_threshold=-1.0)


def test_policy_to_dict_round_trip():
    p = DriftPolicy(baseline_window=5, z_score_threshold=1.5)
    assert DriftPolicy.from_dict(p.to_dict()) == p


# --- DriftTracker ---

def test_empty_tracker_returns_no_baseline(tracker: DriftTracker):
    result = tracker.record(1.0)
    assert result.baseline_mean is None
    assert result.z_score is None
    assert result.is_drifted is False


def test_single_sample_no_baseline(tracker: DriftTracker):
    tracker.record(1.0)
    result = tracker.record(2.0)
    assert result.baseline_mean is None  # need >= 2 in window


def test_two_samples_gives_baseline(tracker: DriftTracker):
    tracker.record(1.0)
    tracker.record(1.0)
    result = tracker.record(1.0)
    assert result.baseline_mean is not None
    assert result.is_drifted is False


def test_outlier_triggers_drift(drift_file: Path):
    policy = DriftPolicy(baseline_window=5, z_score_threshold=2.0)
    t = DriftTracker(path=drift_file, policy=policy)
    for _ in range(5):
        t.record(1.0)
    result = t.record(100.0)
    assert result.is_drifted is True
    assert result.z_score is not None and result.z_score > 2.0


def test_normal_run_does_not_drift(drift_file: Path):
    policy = DriftPolicy(baseline_window=5, z_score_threshold=2.0)
    t = DriftTracker(path=drift_file, policy=policy)
    for v in [1.0, 1.1, 0.9, 1.05, 0.95]:
        t.record(v)
    result = t.record(1.02)
    assert result.is_drifted is False


def test_samples_persisted_across_instances(drift_file: Path):
    t1 = DriftTracker(path=drift_file)
    t1.record(1.0)
    t1.record(2.0)
    t2 = DriftTracker(path=drift_file)
    assert len(t2.samples()) == 2


def test_clear_removes_all_samples(tracker: DriftTracker):
    tracker.record(1.0)
    tracker.record(2.0)
    tracker.clear()
    assert tracker.samples() == []


def test_drift_result_to_dict_contains_all_keys():
    r = DriftResult(duration=1.5, baseline_mean=1.0, baseline_stdev=0.1, z_score=5.0, is_drifted=True)
    d = r.to_dict()
    for key in ("duration", "baseline_mean", "baseline_stdev", "z_score", "is_drifted"):
        assert key in d
