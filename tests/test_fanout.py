"""Tests for pipewatch.fanout."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from pipewatch.fanout import FanoutError, FanoutGroup, FanoutRegistry, FanoutRoute


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def reg_file(tmp_path: Path) -> Path:
    return tmp_path / "fanout.json"


@pytest.fixture()
def reg(reg_file: Path) -> FanoutRegistry:
    return FanoutRegistry(reg_file)


def _route(name: str, enabled: bool = True) -> FanoutRoute:
    return FanoutRoute(name=name, enabled=enabled, tags={"env": "test"})


# ---------------------------------------------------------------------------
# FanoutRoute
# ---------------------------------------------------------------------------

def test_route_to_dict_round_trip() -> None:
    r = FanoutRoute(name="slack", enabled=True, tags={"channel": "#alerts"})
    assert FanoutRoute.from_dict(r.to_dict()) == r


def test_route_defaults_enabled() -> None:
    r = FanoutRoute.from_dict({"name": "email"})
    assert r.enabled is True
    assert r.tags == {}


# ---------------------------------------------------------------------------
# FanoutGroup
# ---------------------------------------------------------------------------

def test_group_add_and_active_routes() -> None:
    g = FanoutGroup(group="alerts")
    g.add(_route("slack"))
    g.add(_route("email", enabled=False))
    active = g.active_routes()
    assert len(active) == 1
    assert active[0].name == "slack"


def test_group_add_duplicate_raises() -> None:
    g = FanoutGroup(group="alerts")
    g.add(_route("slack"))
    with pytest.raises(FanoutError, match="already exists"):
        g.add(_route("slack"))


def test_group_remove_existing() -> None:
    g = FanoutGroup(group="alerts")
    g.add(_route("slack"))
    g.remove("slack")
    assert g.routes == []


def test_group_remove_missing_raises() -> None:
    g = FanoutGroup(group="alerts")
    with pytest.raises(FanoutError, match="not found"):
        g.remove("missing")


def test_group_to_dict_round_trip() -> None:
    g = FanoutGroup(group="ops")
    g.add(_route("pagerduty"))
    restored = FanoutGroup.from_dict(g.to_dict())
    assert restored.group == "ops"
    assert len(restored.routes) == 1
    assert restored.routes[0].name == "pagerduty"


# ---------------------------------------------------------------------------
# FanoutRegistry
# ---------------------------------------------------------------------------

def test_registry_starts_empty(reg: FanoutRegistry) -> None:
    assert reg.all_groups() == []


def test_registry_add_route_persists(reg_file: Path) -> None:
    reg = FanoutRegistry(reg_file)
    reg.add_route("alerts", _route("slack"))
    reg2 = FanoutRegistry(reg_file)
    g = reg2.get("alerts")
    assert g is not None
    assert g.routes[0].name == "slack"


def test_registry_remove_route(reg: FanoutRegistry) -> None:
    reg.add_route("alerts", _route("slack"))
    reg.remove_route("alerts", "slack")
    assert reg.get("alerts").routes == []


def test_registry_remove_route_missing_group_raises(reg: FanoutRegistry) -> None:
    with pytest.raises(FanoutError, match="not found"):
        reg.remove_route("nonexistent", "slack")


def test_dispatch_returns_active_names(reg: FanoutRegistry) -> None:
    reg.add_route("alerts", _route("slack"))
    reg.add_route("alerts", _route("email", enabled=False))
    names = reg.dispatch("alerts")
    assert names == ["slack"]


def test_dispatch_unknown_group_raises(reg: FanoutRegistry) -> None:
    with pytest.raises(FanoutError, match="not found"):
        reg.dispatch("ghost")


def test_registry_file_is_valid_json(reg_file: Path, reg: FanoutRegistry) -> None:
    reg.add_route("ops", _route("pagerduty"))
    data = json.loads(reg_file.read_text())
    assert "groups" in data
