"""Tests for pipewatch.monitor."""

import pytest
from unittest.mock import MagicMock, patch

from pipewatch.monitor import RunResult, run_and_monitor
from pipewatch.config import Config


@pytest.fixture()
def config() -> Config:
    return Config()


# ---------------------------------------------------------------------------
# RunResult helpers
# ---------------------------------------------------------------------------

def test_run_result_succeeded():
    from datetime import datetime
    r = RunResult(
        command="echo hi",
        returncode=0,
        stdout="hi",
        stderr="",
        duration_seconds=0.1,
        started_at=datetime.utcnow(),
        finished_at=datetime.utcnow(),
    )
    assert r.succeeded is True
    assert "SUCCESS" in r.summary()
    assert "echo hi" in r.summary()


def test_run_result_failed():
    from datetime import datetime
    r = RunResult(
        command="false",
        returncode=1,
        stdout="",
        stderr="error!",
        duration_seconds=0.05,
        started_at=datetime.utcnow(),
        finished_at=datetime.utcnow(),
    )
    assert r.succeeded is False
    assert "FAILED" in r.summary()
    assert "exit 1" in r.summary()


# ---------------------------------------------------------------------------
# run_and_monitor integration
# ---------------------------------------------------------------------------

@patch("pipewatch.monitor.notify")
def test_successful_command_no_notify_by_default(mock_notify, config):
    result = run_and_monitor("echo hello", config)
    assert result.succeeded
    assert "hello" in result.stdout
    mock_notify.assert_not_called()


@patch("pipewatch.monitor.notify")
def test_successful_command_notifies_when_flag_set(mock_notify, config):
    result = run_and_monitor("echo hello", config, notify_on_success=True)
    assert result.succeeded
    mock_notify.assert_called_once()


@patch("pipewatch.monitor.notify")
def test_failed_command_triggers_notify(mock_notify, config):
    result = run_and_monitor("exit 2", config)
    assert not result.succeeded
    assert result.returncode == 2
    mock_notify.assert_called_once()
    message_arg = mock_notify.call_args[0][0]
    assert "FAILED" in message_arg


@patch("pipewatch.monitor.notify")
def test_duration_is_recorded(mock_notify, config):
    result = run_and_monitor("sleep 0.05", config)
    assert result.duration_seconds >= 0.05


@patch("pipewatch.monitor.notify")
def test_stderr_captured(mock_notify, config):
    result = run_and_monitor("echo err >&2", config)
    assert "err" in result.stderr
