"""fanout.py — broadcast a pipeline event to multiple named destinations."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional


class FanoutError(ValueError):
    """Raised when fanout configuration or dispatch fails."""


@dataclass
class FanoutRoute:
    """A single named destination in a fanout group."""

    name: str
    enabled: bool = True
    tags: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {"name": self.name, "enabled": self.enabled, "tags": dict(self.tags)}

    @classmethod
    def from_dict(cls, data: dict) -> "FanoutRoute":
        return cls(
            name=data["name"],
            enabled=bool(data.get("enabled", True)),
            tags=dict(data.get("tags", {})),
        )


@dataclass
class FanoutGroup:
    """A named collection of routes that receive the same event."""

    group: str
    routes: List[FanoutRoute] = field(default_factory=list)

    # ------------------------------------------------------------------
    def add(self, route: FanoutRoute) -> None:
        if any(r.name == route.name for r in self.routes):
            raise FanoutError(f"Route '{route.name}' already exists in group '{self.group}'")
        self.routes.append(route)

    def remove(self, name: str) -> None:
        before = len(self.routes)
        self.routes = [r for r in self.routes if r.name != name]
        if len(self.routes) == before:
            raise FanoutError(f"Route '{name}' not found in group '{self.group}'")

    def active_routes(self) -> List[FanoutRoute]:
        return [r for r in self.routes if r.enabled]

    # ------------------------------------------------------------------
    def to_dict(self) -> dict:
        return {"group": self.group, "routes": [r.to_dict() for r in self.routes]}

    @classmethod
    def from_dict(cls, data: dict) -> "FanoutGroup":
        g = cls(group=data["group"])
        g.routes = [FanoutRoute.from_dict(r) for r in data.get("routes", [])]
        return g


class FanoutRegistry:
    """Persist and retrieve fanout groups from a JSON file."""

    def __init__(self, path: Path) -> None:
        self._path = Path(path)
        self._groups: Dict[str, FanoutGroup] = {}
        self._load()

    # ------------------------------------------------------------------
    def _load(self) -> None:
        if self._path.exists():
            raw = json.loads(self._path.read_text())
            for item in raw.get("groups", []):
                g = FanoutGroup.from_dict(item)
                self._groups[g.group] = g

    def _save(self) -> None:
        self._path.write_text(
            json.dumps({"groups": [g.to_dict() for g in self._groups.values()]}, indent=2)
        )

    # ------------------------------------------------------------------
    def get_or_create(self, group: str) -> FanoutGroup:
        if group not in self._groups:
            self._groups[group] = FanoutGroup(group=group)
            self._save()
        return self._groups[group]

    def get(self, group: str) -> Optional[FanoutGroup]:
        return self._groups.get(group)

    def all_groups(self) -> List[FanoutGroup]:
        return list(self._groups.values())

    def add_route(self, group: str, route: FanoutRoute) -> None:
        g = self.get_or_create(group)
        g.add(route)
        self._save()

    def remove_route(self, group: str, name: str) -> None:
        g = self._groups.get(group)
        if g is None:
            raise FanoutError(f"Group '{group}' not found")
        g.remove(name)
        self._save()

    def dispatch(self, group: str) -> List[str]:
        """Return names of active routes for *group* (simulates dispatch)."""
        g = self._groups.get(group)
        if g is None:
            raise FanoutError(f"Group '{group}' not found")
        return [r.name for r in g.active_routes()]
