"""Baseline tracking: record and compare metric values against a stored baseline."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


class BaselineError(Exception):
    """Raised for invalid baseline operations."""


@dataclass
class BaselineEntry:
    job: str
    metric: str
    value: float

    def to_dict(self) -> dict:
        return {"job": self.job, "metric": self.metric, "value": self.value}

    @classmethod
    def from_dict(cls, data: dict) -> "BaselineEntry":
        return cls(
            job=data["job"],
            metric=data["metric"],
            value=float(data["value"]),
        )


class Baseline:
    """Persist and compare baseline metric values per job."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._data: dict[str, dict[str, float]] = self._load()

    def _load(self) -> dict[str, dict[str, float]]:
        if not self._path.exists():
            return {}
        try:
            raw = json.loads(self._path.read_text())
            return {job: {m: float(v) for m, v in metrics.items()} for job, metrics in raw.items()}
        except (json.JSONDecodeError, KeyError, ValueError):
            return {}

    def _save(self) -> None:
        self._path.write_text(json.dumps(self._data, indent=2))

    def set(self, job: str, metric: str, value: float) -> BaselineEntry:
        if not job:
            raise BaselineError("job must not be empty")
        if not metric:
            raise BaselineError("metric must not be empty")
        self._data.setdefault(job, {})[metric] = value
        self._save()
        return BaselineEntry(job=job, metric=metric, value=value)

    def get(self, job: str, metric: str) -> Optional[BaselineEntry]:
        value = self._data.get(job, {}).get(metric)
        if value is None:
            return None
        return BaselineEntry(job=job, metric=metric, value=value)

    def compare(self, job: str, metric: str, current: float) -> Optional[float]:
        """Return percentage deviation from baseline, or None if no baseline set."""
        entry = self.get(job, metric)
        if entry is None:
            return None
        if entry.value == 0.0:
            return None
        return (current - entry.value) / abs(entry.value) * 100.0

    def clear(self, job: str) -> None:
        self._data.pop(job, None)
        self._save()

    def all_entries(self) -> list[BaselineEntry]:
        entries = []
        for job, metrics in self._data.items():
            for metric, value in metrics.items():
                entries.append(BaselineEntry(job=job, metric=metric, value=value))
        return entries
