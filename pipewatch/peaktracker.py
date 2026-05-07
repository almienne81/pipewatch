"""Peak value tracker — records and persists per-job metric extremes."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional


class PeakTrackerError(Exception):
    """Raised for invalid peak-tracker operations."""


@dataclass
class PeakEntry:
    job: str
    metric: str
    min_value: float
    max_value: float
    sample_count: int

    def to_dict(self) -> dict:
        return {
            "job": self.job,
            "metric": self.metric,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "sample_count": self.sample_count,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PeakEntry":
        return cls(
            job=data["job"],
            metric=data["metric"],
            min_value=data["min_value"],
            max_value=data["max_value"],
            sample_count=data["sample_count"],
        )


class PeakTracker:
    """Persists per-job/metric min and max values across runs."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._data: Dict[str, PeakEntry] = {}
        self._load()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _key(self, job: str, metric: str) -> str:
        return f"{job}::{metric}"

    def _load(self) -> None:
        if self._path.exists():
            raw = json.loads(self._path.read_text())
            self._data = {
                k: PeakEntry.from_dict(v) for k, v in raw.items()
            }

    def _save(self) -> None:
        self._path.write_text(
            json.dumps({k: v.to_dict() for k, v in self._data.items()}, indent=2)
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def record(self, job: str, metric: str, value: float) -> PeakEntry:
        """Update the tracked peaks for *job*/*metric* with *value*."""
        if not job:
            raise PeakTrackerError("job must not be empty")
        if not metric:
            raise PeakTrackerError("metric must not be empty")
        k = self._key(job, metric)
        if k in self._data:
            entry = self._data[k]
            updated = PeakEntry(
                job=job,
                metric=metric,
                min_value=min(entry.min_value, value),
                max_value=max(entry.max_value, value),
                sample_count=entry.sample_count + 1,
            )
        else:
            updated = PeakEntry(
                job=job, metric=metric,
                min_value=value, max_value=value, sample_count=1,
            )
        self._data[k] = updated
        self._save()
        return updated

    def get(self, job: str, metric: str) -> Optional[PeakEntry]:
        """Return the current peak entry or *None* if unseen."""
        return self._data.get(self._key(job, metric))

    def all_entries(self) -> List[PeakEntry]:
        """Return all tracked entries sorted by job then metric."""
        return sorted(self._data.values(), key=lambda e: (e.job, e.metric))

    def reset(self, job: str, metric: str) -> None:
        """Remove the tracked entry for *job*/*metric*."""
        k = self._key(job, metric)
        if k in self._data:
            del self._data[k]
            self._save()
