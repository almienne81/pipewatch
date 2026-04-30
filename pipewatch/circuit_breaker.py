"""Circuit breaker pattern for pipeline alerting.

Prevents alert storms by tracking consecutive failures and
'opening' the circuit after a configurable threshold, suppressing
further notifications until a cooldown period has elapsed.

States:
  CLOSED  – normal operation, alerts pass through
  OPEN    – threshold exceeded, alerts suppressed
  HALF    – cooldown expired, next alert is allowed through to test recovery
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional


class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF = "half"


class CircuitBreakerError(Exception):
    """Raised for invalid circuit breaker configuration."""


@dataclass
class CircuitBreakerPolicy:
    """Configuration for the circuit breaker."""

    failure_threshold: int = 3
    """Number of consecutive failures before opening the circuit."""

    cooldown_seconds: float = 300.0
    """Seconds to wait in OPEN state before moving to HALF-OPEN."""

    def __post_init__(self) -> None:
        if self.failure_threshold < 1:
            raise CircuitBreakerError(
                f"failure_threshold must be >= 1, got {self.failure_threshold}"
            )
        if self.cooldown_seconds <= 0:
            raise CircuitBreakerError(
                f"cooldown_seconds must be > 0, got {self.cooldown_seconds}"
            )

    def to_dict(self) -> dict:
        return {
            "failure_threshold": self.failure_threshold,
            "cooldown_seconds": self.cooldown_seconds,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CircuitBreakerPolicy":
        return cls(
            failure_threshold=int(data.get("failure_threshold", 3)),
            cooldown_seconds=float(data.get("cooldown_seconds", 300.0)),
        )


@dataclass
class CircuitBreakerState:
    """Persisted state for a single circuit breaker key."""

    state: CircuitState = CircuitState.CLOSED
    consecutive_failures: int = 0
    opened_at: Optional[float] = None  # epoch seconds

    def to_dict(self) -> dict:
        return {
            "state": self.state.value,
            "consecutive_failures": self.consecutive_failures,
            "opened_at": self.opened_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CircuitBreakerState":
        return cls(
            state=CircuitState(data.get("state", CircuitState.CLOSED.value)),
            consecutive_failures=int(data.get("consecutive_failures", 0)),
            opened_at=data.get("opened_at"),
        )


class CircuitBreaker:
    """File-backed circuit breaker.

    Example usage::

        policy = CircuitBreakerPolicy(failure_threshold=3, cooldown_seconds=60)
        cb = CircuitBreaker(policy, state_file=Path(".pipewatch/circuit.json"))

        if cb.allow(key="my-pipeline"):
            try:
                run_pipeline()
                cb.record_success(key="my-pipeline")
            except Exception:
                cb.record_failure(key="my-pipeline")
    """

    def __init__(
        self,
        policy: CircuitBreakerPolicy,
        state_file: Path = Path(".pipewatch/circuit_breaker.json"),
    ) -> None:
        self._policy = policy
        self._path = Path(state_file)
        self._data: dict[str, CircuitBreakerState] = {}
        self._load()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def allow(self, key: str) -> bool:
        """Return True if the circuit permits an alert/action for *key*."""
        entry = self._get(key)
        now = time.time()

        if entry.state == CircuitState.CLOSED:
            return True

        if entry.state == CircuitState.OPEN:
            if entry.opened_at is not None and (
                now - entry.opened_at >= self._policy.cooldown_seconds
            ):
                entry.state = CircuitState.HALF
                self._save()
                return True  # let one through
            return False

        # HALF – allow one probe
        return True

    def record_success(self, key: str) -> None:
        """Record a successful outcome; resets the circuit to CLOSED."""
        entry = self._get(key)
        entry.state = CircuitState.CLOSED
        entry.consecutive_failures = 0
        entry.opened_at = None
        self._save()

    def record_failure(self, key: str) -> None:
        """Record a failure; may open the circuit if threshold is reached."""
        entry = self._get(key)
        entry.consecutive_failures += 1

        if entry.consecutive_failures >= self._policy.failure_threshold:
            entry.state = CircuitState.OPEN
            entry.opened_at = time.time()

        self._save()

    def state(self, key: str) -> CircuitState:
        """Return the current state for *key*."""
        return self._get(key).state

    def reset(self, key: str) -> None:
        """Manually reset the circuit for *key* to CLOSED."""
        self._data.pop(key, None)
        self._save()

    def to_dict(self) -> dict:
        """Return a serialisable snapshot of all circuit states."""
        return {k: v.to_dict() for k, v in self._data.items()}

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get(self, key: str) -> CircuitBreakerState:
        if key not in self._data:
            self._data[key] = CircuitBreakerState()
        return self._data[key]

    def _load(self) -> None:
        if not self._path.exists():
            return
        try:
            raw = json.loads(self._path.read_text())
            self._data = {
                k: CircuitBreakerState.from_dict(v) for k, v in raw.items()
            }
        except (json.JSONDecodeError, KeyError):
            self._data = {}

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(self.to_dict(), indent=2))
