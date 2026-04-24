"""Integration tests: metrics collected during a real run_and_monitor call."""
import time
from unittest.mock import MagicMock, patch

import pytest

from pipewatch.config import Config
from pipewatch.metrics import Metrics, collect
from pipewatch.monitor import RunResult


def _make_config(**kwargs) -> Config:
    cfg = Config()
    for k, v in kwargs.items():
        setattr(cfg, k, v)
    return cfg


def test_collect_produces_valid_metrics():
    start = time.time() - 2.0
    m = collect(
        exit_code=0,
        stdout="alpha\nbeta\ngamma\n",
        stderr="warn\n",
        start=start,
    )
    assert m.exit_code == 0
    assert m.stdout_lines == 3
    assert m.stderr_lines == 1
    assert m.elapsed_seconds is not None
    assert m.elapsed_seconds >= 2.0
    assert m.elapsed_human.endswith("s") or "m" in m.elapsed_human


def test_metrics_to_dict_contains_expected_keys():
    m = Metrics(start_time=500.0)
    m.end_time = 560.0
    m.exit_code = 1
    m.stdout_lines = 5
    m.stderr_lines = 3
    d = m.to_dict()
    assert set(d.keys()) == {
        "start_time",
        "end_time",
        "elapsed_seconds",
        "peak_memory_mb",
        "exit_code",
        "stdout_lines",
        "stderr_lines",
    }


def test_metrics_roundtrip_preserves_values():
    m = Metrics(start_time=100.0)
    m.end_time = 200.0
    m.exit_code = 0
    m.stdout_lines = 42
    m.stderr_lines = 7
    m.peak_memory_mb = 256.0

    restored = Metrics.from_dict(m.to_dict())
    assert restored.exit_code == 0
    assert restored.stdout_lines == 42
    assert restored.stderr_lines == 7
    assert restored.peak_memory_mb == pytest.approx(256.0)
    assert restored.elapsed_seconds == pytest.approx(100.0)


def test_elapsed_human_formats_correctly_for_edge_cases():
    cases = [
        (0.0, 1.0, "1.0s"),
        (0.0, 59.9, "59.9s"),
        (0.0, 60.0, "1m 0s"),
        (0.0, 3600.0, "1h 0m 0s"),
    ]
    for start, end, expected in cases:
        m = Metrics(start_time=start)
        m.end_time = end
        assert m.elapsed_human == expected, f"Expected {expected!r}, got {m.elapsed_human!r}"
