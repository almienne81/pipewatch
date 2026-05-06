"""Drift detection: tracks whether a pipeline's runtime is diverging from its baseline."""
from __future__ import annotations

import json
import statistics
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


class DriftError(ValueError):
    """Raised when drift policy parameters are invalid."""


@dataclass
class DriftPolicy:
    """Configuration for drift detection."""

    baseline_window: int = 10  # number of recent runs used to compute baseline
    z_score_threshold: float = 2.0  # standard deviations before flagging drift

    def __post_init__(self) -> None:
        if self.baseline_window < 2:
            raise DriftError("baseline_window must be >= 2")
        if self.z_score_threshold <= 0:
            raise DriftError("z_score_threshold must be positive")

    def to_dict(self) -> dict:
        return {
            "baseline_window": self.baseline_window,
            "z_score_threshold": self.z_score_threshold,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DriftPolicy":
        return cls(
            baseline_window=data.get("baseline_window", 10),
            z_score_threshold=data.get("z_score_threshold", 2.0),
        )


@dataclass
class DriftResult:
    """Result of a single drift check."""

    duration: float
    baseline_mean: Optional[float]
    baseline_stdev: Optional[float]
    z_score: Optional[float]
    is_drifted: bool

    def to_dict(self) -> dict:
        return {
            "duration": self.duration,
            "baseline_mean": self.baseline_mean,
            "baseline_stdev": self.baseline_stdev,
            "z_score": self.z_score,
            "is_drifted": self.is_drifted,
        }


@dataclass
class DriftTracker:
    """Persists duration history and evaluates drift for a named job."""

    path: Path
    policy: DriftPolicy = field(default_factory=DriftPolicy)
    _samples: List[float] = field(init=False, default_factory=list)

    def __post_init__(self) -> None:
        self.path = Path(self.path)
        self._load()

    def _load(self) -> None:
        if self.path.exists():
            data = json.loads(self.path.read_text())
            self._samples = data.get("samples", [])

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps({"samples": self._samples}))

    def record(self, duration: float) -> DriftResult:
        """Record a new duration and return a drift assessment."""
        window = self._samples[-self.policy.baseline_window:]
        if len(window) >= 2:
            mean = statistics.mean(window)
            stdev = statistics.stdev(window)
            z = (duration - mean) / stdev if stdev > 0 else 0.0
            drifted = abs(z) > self.policy.z_score_threshold
            result = DriftResult(duration, mean, stdev, z, drifted)
        else:
            result = DriftResult(duration, None, None, None, False)
        self._samples.append(duration)
        self._save()
        return result

    def samples(self) -> List[float]:
        return list(self._samples)

    def clear(self) -> None:
        self._samples = []
        self._save()
