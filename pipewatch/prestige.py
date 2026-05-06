"""prestige.py – run-streak tracking for pipeline jobs.

Tracks consecutive successes and failures for a named job,
persisting state to a JSON file.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


class PrestigeError(Exception):
    """Raised when streak state is invalid or unreadable."""


@dataclass
class StreakState:
    job: str
    current_streak: int = 0
    streak_type: Optional[str] = None  # "success" | "failure" | None
    best_success_streak: int = 0
    worst_failure_streak: int = 0

    def to_dict(self) -> dict:
        return {
            "job": self.job,
            "current_streak": self.current_streak,
            "streak_type": self.streak_type,
            "best_success_streak": self.best_success_streak,
            "worst_failure_streak": self.worst_failure_streak,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "StreakState":
        return cls(
            job=data["job"],
            current_streak=data.get("current_streak", 0),
            streak_type=data.get("streak_type"),
            best_success_streak=data.get("best_success_streak", 0),
            worst_failure_streak=data.get("worst_failure_streak", 0),
        )


class Prestige:
    """Persistent streak tracker for a collection of jobs."""

    def __init__(self, path: Path) -> None:
        self._path = Path(path)
        self._data: dict[str, StreakState] = {}
        self._load()

    def _load(self) -> None:
        if self._path.exists():
            try:
                raw = json.loads(self._path.read_text())
                self._data = {
                    k: StreakState.from_dict(v) for k, v in raw.items()
                }
            except (json.JSONDecodeError, KeyError) as exc:
                raise PrestigeError(f"Corrupt streak file: {exc}") from exc

    def _save(self) -> None:
        self._path.write_text(
            json.dumps({k: v.to_dict() for k, v in self._data.items()}, indent=2)
        )

    def record(self, job: str, success: bool) -> StreakState:
        """Record an outcome and return the updated StreakState."""
        if not job:
            raise PrestigeError("job name must not be empty")
        state = self._data.get(job, StreakState(job=job))
        outcome = "success" if success else "failure"
        if state.streak_type == outcome:
            state.current_streak += 1
        else:
            state.streak_type = outcome
            state.current_streak = 1
        if success:
            state.best_success_streak = max(
                state.best_success_streak, state.current_streak
            )
        else:
            state.worst_failure_streak = max(
                state.worst_failure_streak, state.current_streak
            )
        self._data[job] = state
        self._save()
        return state

    def get(self, job: str) -> Optional[StreakState]:
        """Return the current StreakState for *job*, or None if unseen."""
        return self._data.get(job)

    def clear(self, job: str) -> None:
        """Remove streak data for *job*."""
        self._data.pop(job, None)
        self._save()

    def all_jobs(self) -> list[str]:
        """Return sorted list of tracked job names."""
        return sorted(self._data.keys())
