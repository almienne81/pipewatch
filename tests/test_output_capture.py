"""Tests for pipewatch.output_capture."""
from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

import pytest

from pipewatch.output_capture import CapturedOutput, capture
from datetime import datetime, timezone


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _make_output(**kwargs) -> CapturedOutput:
    defaults = dict(
        command="echo hi",
        stdout="hi\n",
        stderr="",
        returncode=0,
        started_at=_now(),
        finished_at=_now(),
        truncated=False,
    )
    defaults.update(kwargs)
    return CapturedOutput(**defaults)


def test_succeeded_true_on_zero_returncode():
    out = _make_output(returncode=0)
    assert out.succeeded() is True


def test_succeeded_false_on_nonzero():
    out = _make_output(returncode=1)
    assert out.succeeded() is False


def test_combined_merges_stdout_and_stderr():
    out = _make_output(stdout="hello\n", stderr="world\n")
    combined = out.combined()
    assert "hello" in combined
    assert "world" in combined


def test_combined_skips_empty_streams():
    out = _make_output(stdout="only\n", stderr="")
    assert out.combined() == "only\n"


def test_tail_returns_last_n_lines():
    lines = "\n".join(str(i) for i in range(50))
    out = _make_output(stdout=lines, stderr="")
    tail = out.tail(5)
    assert tail == "\n".join(str(i) for i in range(45, 50))


def test_to_dict_contains_expected_keys():
    out = _make_output()
    d = out.to_dict()
    for key in ("command", "stdout", "stderr", "returncode", "started_at", "finished_at", "truncated"):
        assert key in d


def test_capture_successful_command():
    result = capture([sys.executable, "-c", "print('hello')"])
    assert result.succeeded()
    assert "hello" in result.stdout
    assert result.returncode == 0


def test_capture_failing_command():
    result = capture([sys.executable, "-c", "import sys; sys.exit(2)"])
    assert not result.succeeded()
    assert result.returncode == 2


def test_capture_stderr_captured():
    result = capture([sys.executable, "-c", "import sys; sys.stderr.write('err\\n')"])
    assert "err" in result.stderr


def test_capture_timeout_returns_negative_returncode():
    result = capture(
        [sys.executable, "-c", "import time; time.sleep(10)"],
        timeout=0.1,
    )
    assert result.returncode == -1


def test_capture_truncates_large_output():
    max_b = 10
    result = capture(
        [sys.executable, "-c", f"print('x' * 1000)"],
        max_bytes=max_b,
    )
    assert len(result.stdout) <= max_b
    assert result.truncated is True
