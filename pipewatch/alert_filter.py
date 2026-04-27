"""Alert filtering: suppress alerts based on severity level and keyword rules."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from typing import List, Optional


class Severity(IntEnum):
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50

    @classmethod
    def parse(cls, value: str) -> "Severity":
        try:
            return cls[value.upper()]
        except KeyError:
            raise ValueError(
                f"Unknown severity '{value}'. "
                f"Valid values: {[s.name for s in cls]}"
            )


@dataclass
class AlertFilterRule:
    """A single keyword-based suppression rule."""
    keyword: str
    reason: str = ""

    def matches(self, message: str) -> bool:
        return self.keyword.lower() in message.lower()


@dataclass
class AlertFilter:
    """Decides whether an alert message should be sent.

    Attributes:
        min_severity: Minimum severity level to allow through.
        suppress_rules: List of keyword rules; matching messages are blocked.
    """
    min_severity: Severity = Severity.WARNING
    suppress_rules: List[AlertFilterRule] = field(default_factory=list)

    def should_send(self, message: str, severity: Severity) -> bool:
        """Return True if the alert should be dispatched."""
        if severity < self.min_severity:
            return False
        for rule in self.suppress_rules:
            if rule.matches(message):
                return False
        return True

    def suppressed_by(self, message: str) -> Optional[AlertFilterRule]:
        """Return the first matching suppression rule, or None."""
        for rule in self.suppress_rules:
            if rule.matches(message):
                return rule
        return None

    def add_rule(self, keyword: str, reason: str = "") -> "AlertFilter":
        """Return a new AlertFilter with an additional suppression rule."""
        new_rules = list(self.suppress_rules) + [AlertFilterRule(keyword, reason)]
        return AlertFilter(min_severity=self.min_severity, suppress_rules=new_rules)

    def to_dict(self) -> dict:
        return {
            "min_severity": self.min_severity.name,
            "suppress_rules": [
                {"keyword": r.keyword, "reason": r.reason}
                for r in self.suppress_rules
            ],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AlertFilter":
        severity = Severity.parse(data.get("min_severity", "WARNING"))
        rules = [
            AlertFilterRule(r["keyword"], r.get("reason", ""))
            for r in data.get("suppress_rules", [])
        ]
        return cls(min_severity=severity, suppress_rules=rules)
