"""Tests for pipewatch.metrics."""
import time

import pytest

from pipewatch.metrics import Metrics, collect


def test_elapsed_none_before_stop():
    m = Metrics(start_time=time.time())
    assert m.elapsed_seconds is None
    assert m.elapsed_human == "running"


def test_elapsed_seconds_after_stop():
    m = Metrics(start_time=time.time() - 5.0)
    m.end_time = time.time()
    assert m.elapsed_seconds is not None
    assert m.elapsed_seconds >= 5.0


def test_elapsed_human_seconds():
    m = Metrics(start_time=0.0)
    m.end_time = 42.5
    assert m.elapsed_human == "42.5s"


def test_elapsed_human_minutes():
    m = Metrics(start_time=0.0)
    m.end_time = 125.0  # 2m 5s
    assert m.elapsed_human == "2m 5s"


def test_elapsed_human_hours():
    m = Metrics(start_time=0.0)
    m.end_time = 3661.0  # 1h 1m 1s
    assert m.elapsed_human == "1h 1m 1s"


def test_to_dict_and_from_dict_roundtrip():
    m = Metrics(start_time=1000.0)
    m.end_time = 1060.0
    m.exit_code = 0
    m.stdout_lines = 10
    m.stderr_lines = 2
    m.peak_memory_mb = 128.5

    d = m.to_dict()
    assert d["elapsed_seconds"] == pytest.approx(60.0)

    restored = Metrics.from_dict(d)
    assert restored.start_time == 1000.0
    assert restored.end_time == 1060.0
    assert restored.exit_code == 0
    assert restored.stdout_lines == 10
    assert restored.stderr_lines == 2
    assert restored.peak_memory_mb == pytest.approx(128.5)


def test_collect_counts_lines():
    start = time.time() - 1.0
    m = collect(exit_code=0, stdout="line1\nline2\nline3\n", stderr="err\n", start=start)
    assert m.exit_code == 0
    assert m.stdout_lines == 3
    assert m.stderr_lines == 1
    assert m.elapsed_seconds is not None
    assert m.elapsed_seconds >= 1.0


def test_collect_no_trailing_newline():
    start = time.time()
    m = collect(exit_code=1, stdout="only line", stderr="", start=start)
    assert m.stdout_lines == 1
    assert m.stderr_lines == 0


def test_from_dict_missing_fields_use_defaults():
    m = Metrics.from_dict({})
    assert m.start_time == 0.0
    assert m.end_time is None
    assert m.stdout_lines == 0
    assert m.stderr_lines == 0
