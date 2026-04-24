"""Notification dispatchers for Slack and email alerts."""

from __future__ import annotations

import smtplib
from email.message import EmailMessage
from typing import Optional

try:
    import requests
except ImportError:  # pragma: no cover
    requests = None  # type: ignore

from pipewatch.config import Config


class NotificationError(Exception):
    """Raised when a notification fails to send."""


def send_slack(message: str, config: Config) -> None:
    """Post *message* to the configured Slack webhook.

    Raises:
        NotificationError: if Slack is not configured or the request fails.
    """
    if requests is None:  # pragma: no cover
        raise NotificationError("'requests' package is required for Slack notifications")

    slack = config.slack
    if not slack or not slack.webhook_url:
        raise NotificationError("Slack webhook_url is not configured")

    payload = {"text": message}
    if slack.channel:
        payload["channel"] = slack.channel
    if slack.username:
        payload["username"] = slack.username

    try:
        response = requests.post(slack.webhook_url, json=payload, timeout=10)
        response.raise_for_status()
    except Exception as exc:  # noqa: BLE001
        raise NotificationError(f"Slack notification failed: {exc}") from exc


def send_email(subject: str, body: str, config: Config) -> None:
    """Send an email alert using the configured SMTP settings.

    Raises:
        NotificationError: if email is not configured or sending fails.
    """
    email_cfg = config.email
    if not email_cfg or not email_cfg.smtp_host:
        raise NotificationError("Email smtp_host is not configured")
    if not email_cfg.to_addresses:
        raise NotificationError("Email to_addresses is not configured")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = email_cfg.from_address or "pipewatch@localhost"
    msg["To"] = ", ".join(email_cfg.to_addresses)
    msg.set_content(body)

    try:
        with smtplib.SMTP(email_cfg.smtp_host, email_cfg.smtp_port or 25, timeout=10) as smtp:
            if email_cfg.use_tls:
                smtp.starttls()
            if email_cfg.username and email_cfg.password:
                smtp.login(email_cfg.username, email_cfg.password)
            smtp.send_message(msg)
    except Exception as exc:  # noqa: BLE001
        raise NotificationError(f"Email notification failed: {exc}") from exc


def notify(subject: str, body: str, config: Config) -> dict[str, Optional[str]]:
    """Attempt both Slack and email notifications; return a status dict."""
    results: dict[str, Optional[str]] = {"slack": None, "email": None}

    try:
        send_slack(body, config)
        results["slack"] = "ok"
    except NotificationError as exc:
        results["slack"] = str(exc)

    try:
        send_email(subject, body, config)
        results["email"] = "ok"
    except NotificationError as exc:
        results["email"] = str(exc)

    return results
