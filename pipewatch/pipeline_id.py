"""Unique pipeline run ID generation and parsing."""

from __future__ import annotations

import hashlib
import time
import uuid
from dataclasses import dataclass
from typing import Optional


class PipelineIDError(ValueError):
    """Raised when a pipeline ID is invalid or cannot be parsed."""


@dataclass(frozen=True)
class PipelineID:
    """Represents a unique identifier for a pipeline run."""

    run_id: str
    pipeline: str
    timestamp: float

    def short(self) -> str:
        """Return an 8-character abbreviated run ID."""
        return self.run_id[:8]

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "pipeline": self.pipeline,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PipelineID":
        try:
            return cls(
                run_id=data["run_id"],
                pipeline=data["pipeline"],
                timestamp=float(data["timestamp"]),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise PipelineIDError(f"Invalid pipeline ID data: {exc}") from exc

    def __str__(self) -> str:
        return f"{self.pipeline}/{self.short()}"


def generate(pipeline: str, seed: Optional[str] = None) -> PipelineID:
    """Generate a new unique PipelineID.

    Args:
        pipeline: Human-readable pipeline name (e.g. 'etl-daily').
        seed: Optional deterministic seed; if omitted a random UUID is used.

    Returns:
        A fresh PipelineID instance.
    """
    if not pipeline or not isinstance(pipeline, str):
        raise PipelineIDError("pipeline name must be a non-empty string")

    ts = time.time()
    if seed is not None:
        raw = hashlib.sha256(f"{pipeline}:{seed}:{ts}".encode()).hexdigest()
    else:
        raw = uuid.uuid4().hex

    return PipelineID(run_id=raw, pipeline=pipeline, timestamp=ts)


def parse(value: str) -> PipelineID:
    """Parse a run_id string back into a minimal PipelineID.

    Accepts either a full 64-char hex run_id or a 'pipeline/short_id' string
    produced by __str__; in the latter case timestamp is set to 0.0.
    """
    if "/" in value:
        parts = value.split("/", 1)
        if len(parts) != 2 or not parts[1]:
            raise PipelineIDError(f"Cannot parse pipeline ID: {value!r}")
        return PipelineID(run_id=parts[1], pipeline=parts[0], timestamp=0.0)
    if len(value) < 8 or not all(c in "0123456789abcdef" for c in value.lower()):
        raise PipelineIDError(f"Cannot parse pipeline ID: {value!r}")
    return PipelineID(run_id=value.lower(), pipeline="unknown", timestamp=0.0)
