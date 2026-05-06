"""Cascade: dependency-aware pipeline stage failure propagation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set


class CascadeError(Exception):
    """Raised when a cascade configuration is invalid."""


@dataclass
class CascadePolicy:
    """Defines how failures propagate through dependent pipeline stages."""

    stop_on_failure: bool = True
    blocked_stages: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "stop_on_failure": self.stop_on_failure,
            "blocked_stages": list(self.blocked_stages),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CascadePolicy":
        return cls(
            stop_on_failure=bool(data.get("stop_on_failure", True)),
            blocked_stages=list(data.get("blocked_stages", [])),
        )


@dataclass
class CascadeGraph:
    """Tracks stage dependencies and propagates failures."""

    _deps: Dict[str, List[str]] = field(default_factory=dict)

    def add_stage(self, stage: str, depends_on: Optional[List[str]] = None) -> None:
        """Register a stage with optional upstream dependencies."""
        if not stage:
            raise CascadeError("Stage name must be non-empty.")
        self._deps[stage] = list(depends_on or [])

    def blocked_by_failures(self, failed: Set[str]) -> List[str]:
        """Return stages that cannot run because an upstream stage failed."""
        blocked: List[str] = []
        for stage, deps in self._deps.items():
            if stage in failed:
                continue
            if any(d in failed for d in deps):
                blocked.append(stage)
        return sorted(blocked)

    def execution_order(self) -> List[str]:
        """Return a topologically sorted list of stages."""
        visited: List[str] = []
        seen: Set[str] = set()

        def visit(node: str) -> None:
            if node in seen:
                return
            seen.add(node)
            for dep in self._deps.get(node, []):
                if dep not in self._deps:
                    raise CascadeError(f"Unknown dependency '{dep}' for stage '{node}'.")
                visit(dep)
            visited.append(node)

        for s in self._deps:
            visit(s)
        return visited

    def to_dict(self) -> dict:
        return {"deps": {k: list(v) for k, v in self._deps.items()}}

    @classmethod
    def from_dict(cls, data: dict) -> "CascadeGraph":
        g = cls()
        for stage, deps in data.get("deps", {}).items():
            g.add_stage(stage, deps)
        return g
