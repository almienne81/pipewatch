"""Configuration loader for pipewatch.

Loads settings from a YAML config file and environment variables,
providing a single Config dataclass used throughout the application.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import yaml

DEFAULT_CONFIG_PATH = Path("pipewatch.yml")


@dataclass
class SlackConfig:
    webhook_url: str = ""
    channel: str = "#alerts"


@dataclass
class EmailConfig:
    smtp_host: str = "localhost"
    smtp_port: int = 587
    sender: str = ""
    recipients: List[str] = field(default_factory=list)
    username: str = ""
    password: str = ""


@dataclass
class Config:
    job_name: str = "pipeline"
    timeout_seconds: int = 3600
    poll_interval_seconds: int = 30
    alert_on_failure: bool = True
    alert_on_timeout: bool = True
    alert_on_success: bool = False
    slack: SlackConfig = field(default_factory=SlackConfig)
    email: EmailConfig = field(default_factory=EmailConfig)


def load_config(path: Optional[Path] = None) -> Config:
    """Load configuration from a YAML file, with env-var overrides."""
    config_path = path or DEFAULT_CONFIG_PATH
    raw: dict = {}

    if config_path.exists():
        with config_path.open("r") as fh:
            raw = yaml.safe_load(fh) or {}

    slack_raw = raw.get("slack", {})
    email_raw = raw.get("email", {})

    slack = SlackConfig(
        webhook_url=os.getenv("PIPEWATCH_SLACK_WEBHOOK", slack_raw.get("webhook_url", "")),
        channel=slack_raw.get("channel", "#alerts"),
    )

    email = EmailConfig(
        smtp_host=email_raw.get("smtp_host", "localhost"),
        smtp_port=int(email_raw.get("smtp_port", 587)),
        sender=os.getenv("PIPEWATCH_EMAIL_SENDER", email_raw.get("sender", "")),
        recipients=email_raw.get("recipients", []),
        username=os.getenv("PIPEWATCH_EMAIL_USER", email_raw.get("username", "")),
        password=os.getenv("PIPEWATCH_EMAIL_PASS", email_raw.get("password", "")),
    )

    return Config(
        job_name=raw.get("job_name", "pipeline"),
        timeout_seconds=int(raw.get("timeout_seconds", 3600)),
        poll_interval_seconds=int(raw.get("poll_interval_seconds", 30)),
        alert_on_failure=raw.get("alert_on_failure", True),
        alert_on_timeout=raw.get("alert_on_timeout", True),
        alert_on_success=raw.get("alert_on_success", False),
        slack=slack,
        email=email,
    )
