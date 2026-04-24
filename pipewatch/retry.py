"""Retry logic for pipeline commands."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, List, Optional


@dataclass
class RetryPolicy:
    """Configuration for retry behaviour."""

    max_attempts: int = 1
    delay_seconds: float = 5.0
    backoff_factor: float = 1.0  # multiplied with delay after each attempt
    retry_on_codes: List[int] = field(default_factory=list)  # empty = retry on any non-zero

    def should_retry(self, exit_code: int, attempt: int) -> bool:
        """Return True when another attempt is warranted."""
        if attempt >= self.max_attempts:
            return False
        if exit_code == 0:
            return False
        if self.retry_on_codes and exit_code not in self.retry_on_codes:
            return False
        return True

    def wait_seconds(self, attempt: int) -> float:
        """Seconds to sleep before *attempt* (0-indexed)."""
        return self.delay_seconds * (self.backoff_factor ** attempt)


@dataclass
class AttemptResult:
    attempt: int
    exit_code: int
    stdout: str
    stderr: str
    duration: float


def run_with_retry(
    runner: Callable[[],  AttemptResult],
    policy: RetryPolicy,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> List[AttemptResult]:
    """Execute *runner* up to policy.max_attempts times.

    Returns the list of AttemptResult objects (one per attempt made).
    """
    results: List[AttemptResult] = []
    for attempt in range(1, policy.max_attempts + 1):
        result = runner()
        result = AttemptResult(
            attempt=attempt,
            exit_code=result.exit_code,
            stdout=result.stdout,
            stderr=result.stderr,
            duration=result.duration,
        )
        results.append(result)
        if not policy.should_retry(result.exit_code, attempt):
            break
        wait = policy.wait_seconds(attempt - 1)
        sleep_fn(wait)
    return results


def parse_retry_policy(
    max_attempts: int = 1,
    delay: float = 5.0,
    backoff: float = 1.0,
    retry_on_codes: Optional[List[int]] = None,
) -> RetryPolicy:
    """Build a RetryPolicy from CLI / config values."""
    if max_attempts < 1:
        raise ValueError("max_attempts must be >= 1")
    if delay < 0:
        raise ValueError("delay must be >= 0")
    if backoff < 1.0:
        raise ValueError("backoff_factor must be >= 1.0")
    return RetryPolicy(
        max_attempts=max_attempts,
        delay_seconds=delay,
        backoff_factor=backoff,
        retry_on_codes=retry_on_codes or [],
    )
