"""fence.py — Named execution barriers that block until all expected jobs check in."""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


class FenceError(Exception):
    """Raised for invalid fence operations."""


@dataclass
class FenceState:
    name: str
    expected: List[str]
    arrived: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "expected": list(self.expected),
            "arrived": list(self.arrived),
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "FenceState":
        return cls(
            name=d["name"],
            expected=list(d["expected"]),
            arrived=list(d.get("arrived", [])),
            created_at=float(d.get("created_at", time.time())),
        )

    @property
    def pending(self) -> List[str]:
        return [j for j in self.expected if j not in self.arrived]

    @property
    def is_open(self) -> bool:
        return len(self.pending) == 0


class Fence:
    """Persistent named barrier tracking which jobs have arrived."""

    def __init__(self, path: Path) -> None:
        self._path = Path(path)
        self._states: Dict[str, FenceState] = {}
        self._load()

    def _load(self) -> None:
        if self._path.exists():
            raw = json.loads(self._path.read_text())
            self._states = {k: FenceState.from_dict(v) for k, v in raw.items()}

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps({k: v.to_dict() for k, v in self._states.items()}, indent=2))

    def create(self, name: str, expected: List[str]) -> FenceState:
        if not name:
            raise FenceError("Fence name must not be empty.")
        if not expected:
            raise FenceError("Expected job list must not be empty.")
        state = FenceState(name=name, expected=list(expected))
        self._states[name] = state
        self._save()
        return state

    def arrive(self, name: str, job: str) -> FenceState:
        if name not in self._states:
            raise FenceError(f"No fence named '{name}'.")
        state = self._states[name]
        if job not in state.expected:
            raise FenceError(f"Job '{job}' is not expected at fence '{name}'.")
        if job not in state.arrived:
            state.arrived.append(job)
            self._save()
        return state

    def get(self, name: str) -> Optional[FenceState]:
        return self._states.get(name)

    def clear(self, name: str) -> None:
        self._states.pop(name, None)
        self._save()

    def all(self) -> List[FenceState]:
        return list(self._states.values())
