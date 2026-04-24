"""Tests for pipewatch.config module."""

import textwrap
from pathlib import Path

import pytest

from pipewatch.config import Config, load_config


@pytest.fixture()
def tmp_config(tmp_path: Path):
    """Return a helper that writes a YAML config file and returns its path."""

    def _write(content: str) -> Path:
        cfg_file = tmp_path / "pipewatch.yml"
        cfg_file.write_text(textwrap.dedent(content))
        return cfg_file

    return _write


def test_defaults_when_no_file(tmp_path: Path):
    """load_config returns sensible defaults when no config file exists."""
    cfg = load_config(tmp_path / "nonexistent.yml")
    assert isinstance(cfg, Config)
    assert cfg.job_name == "pipeline"
    assert cfg.timeout_seconds == 3600
    assert cfg.poll_interval_seconds == 30
    assert cfg.alert_on_failure is True
    assert cfg.alert_on_success is False


def test_values_loaded_from_yaml(tmp_config):
    path = tmp_config(
        """
        job_name: etl_daily
        timeout_seconds: 1800
        poll_interval_seconds: 10
        alert_on_success: true
        slack:
          webhook_url: https://hooks.slack.com/test
          channel: "#data-ops"
        email:
          smtp_host: mail.example.com
          smtp_port: 465
          sender: bot@example.com
          recipients:
            - alice@example.com
            - bob@example.com
        """
    )
    cfg = load_config(path)
    assert cfg.job_name == "etl_daily"
    assert cfg.timeout_seconds == 1800
    assert cfg.poll_interval_seconds == 10
    assert cfg.alert_on_success is True
    assert cfg.slack.webhook_url == "https://hooks.slack.com/test"
    assert cfg.slack.channel == "#data-ops"
    assert cfg.email.smtp_host == "mail.example.com"
    assert cfg.email.smtp_port == 465
    assert cfg.email.recipients == ["alice@example.com", "bob@example.com"]


def test_env_overrides_yaml(tmp_config, monkeypatch):
    path = tmp_config(
        """
        slack:
          webhook_url: https://hooks.slack.com/from-file
        email:
          sender: file@example.com
        """
    )
    monkeypatch.setenv("PIPEWATCH_SLACK_WEBHOOK", "https://hooks.slack.com/from-env")
    monkeypatch.setenv("PIPEWATCH_EMAIL_SENDER", "env@example.com")

    cfg = load_config(path)
    assert cfg.slack.webhook_url == "https://hooks.slack.com/from-env"
    assert cfg.email.sender == "env@example.com"


def test_empty_yaml_uses_defaults(tmp_config):
    path = tmp_config("")
    cfg = load_config(path)
    assert cfg.job_name == "pipeline"
    assert cfg.email.recipients == []
