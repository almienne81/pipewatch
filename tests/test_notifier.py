"""Tests for pipewatch.notifier."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from pipewatch.config import Config, EmailConfig, SlackConfig
from pipewatch.notifier import NotificationError, notify, send_email, send_slack


@pytest.fixture()
def slack_config() -> Config:
    return Config(slack=SlackConfig(webhook_url="https://hooks.slack.com/test", channel="#alerts"))


@pytest.fixture()
def email_config() -> Config:
    return Config(
        email=EmailConfig(
            smtp_host="smtp.example.com",
            smtp_port=587,
            from_address="pipewatch@example.com",
            to_addresses=["ops@example.com"],
            use_tls=True,
        )
    )


# --- Slack tests ---

def test_send_slack_success(slack_config: Config) -> None:
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None

    with patch("pipewatch.notifier.requests.post", return_value=mock_response) as mock_post:
        send_slack("hello", slack_config)

    mock_post.assert_called_once()
    _, kwargs = mock_post.call_args
    assert kwargs["json"]["text"] == "hello"
    assert kwargs["json"]["channel"] == "#alerts"


def test_send_slack_no_webhook_raises() -> None:
    cfg = Config(slack=SlackConfig(webhook_url=""))
    with pytest.raises(NotificationError, match="webhook_url"):
        send_slack("hi", cfg)


def test_send_slack_no_config_raises() -> None:
    cfg = Config()
    with pytest.raises(NotificationError, match="webhook_url"):
        send_slack("hi", cfg)


def test_send_slack_http_error_raises(slack_config: Config) -> None:
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = Exception("HTTP 500")

    with patch("pipewatch.notifier.requests.post", return_value=mock_response):
        with pytest.raises(NotificationError, match="Slack notification failed"):
            send_slack("boom", slack_config)


# --- Email tests ---

def test_send_email_success(email_config: Config) -> None:
    with patch("pipewatch.notifier.smtplib.SMTP") as mock_smtp_cls:
        mock_smtp = MagicMock()
        mock_smtp_cls.return_value.__enter__ = lambda s: mock_smtp
        mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)
        send_email("Subject", "Body", email_config)

    mock_smtp.starttls.assert_called_once()
    mock_smtp.send_message.assert_called_once()


def test_send_email_no_host_raises() -> None:
    cfg = Config(email=EmailConfig(smtp_host="", to_addresses=["a@b.com"]))
    with pytest.raises(NotificationError, match="smtp_host"):
        send_email("s", "b", cfg)


def test_send_email_no_recipients_raises() -> None:
    cfg = Config(email=EmailConfig(smtp_host="smtp.example.com", to_addresses=[]))
    with pytest.raises(NotificationError, match="to_addresses"):
        send_email("s", "b", cfg)


# --- notify() aggregator ---

def test_notify_returns_status_dict(slack_config: Config) -> None:
    with patch("pipewatch.notifier.send_slack") as mock_slack, \
         patch("pipewatch.notifier.send_email") as _:
        results = notify("Alert", "Something failed", slack_config)

    assert results["slack"] == "ok"
    assert "email" in results
    mock_slack.assert_called_once()


def test_notify_captures_errors() -> None:
    cfg = Config()  # no slack or email configured
    results = notify("Alert", "Something failed", cfg)
    assert results["slack"] != "ok"
    assert results["email"] != "ok"
