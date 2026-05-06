"""Tests for pipewatch.fence."""
from __future__ import annotations

import pytest
from pathlib import Path

from pipewatch.fence import Fence, FenceError, FenceState


@pytest.fixture
def fence_file(tmp_path: Path) -> Path:
    return tmp_path / "fence.json"


@pytest.fixture
def fence(fence_file: Path) -> Fence:
    return Fence(fence_file)


def test_create_returns_fence_state(fence: Fence) -> None:
    state = fence.create("sync", ["jobA", "jobB"])
    assert state.name == "sync"
    assert state.expected == ["jobA", "jobB"]
    assert state.arrived == []
    assert not state.is_open


def test_create_empty_name_raises(fence: Fence) -> None:
    with pytest.raises(FenceError, match="name"):
        fence.create("", ["jobA"])


def test_create_empty_jobs_raises(fence: Fence) -> None:
    with pytest.raises(FenceError, match="Expected"):
        fence.create("sync", [])


def test_arrive_marks_job(fence: Fence) -> None:
    fence.create("sync", ["jobA", "jobB"])
    state = fence.arrive("sync", "jobA")
    assert "jobA" in state.arrived
    assert "jobB" in state.pending
    assert not state.is_open


def test_all_arrive_opens_fence(fence: Fence) -> None:
    fence.create("sync", ["jobA", "jobB"])
    fence.arrive("sync", "jobA")
    state = fence.arrive("sync", "jobB")
    assert state.is_open
    assert state.pending == []


def test_arrive_idempotent(fence: Fence) -> None:
    fence.create("sync", ["jobA"])
    fence.arrive("sync", "jobA")
    state = fence.arrive("sync", "jobA")
    assert state.arrived.count("jobA") == 1


def test_arrive_unknown_fence_raises(fence: Fence) -> None:
    with pytest.raises(FenceError, match="No fence"):
        fence.arrive("missing", "jobA")


def test_arrive_unexpected_job_raises(fence: Fence) -> None:
    fence.create("sync", ["jobA"])
    with pytest.raises(FenceError, match="not expected"):
        fence.arrive("sync", "jobZ")


def test_get_missing_returns_none(fence: Fence) -> None:
    assert fence.get("nope") is None


def test_clear_removes_fence(fence: Fence) -> None:
    fence.create("sync", ["jobA"])
    fence.clear("sync")
    assert fence.get("sync") is None


def test_state_persists_across_instances(fence_file: Path) -> None:
    f1 = Fence(fence_file)
    f1.create("barrier", ["a", "b", "c"])
    f1.arrive("barrier", "a")

    f2 = Fence(fence_file)
    state = f2.get("barrier")
    assert state is not None
    assert "a" in state.arrived
    assert set(state.pending) == {"b", "c"}


def test_to_dict_round_trip() -> None:
    s = FenceState(name="x", expected=["p", "q"], arrived=["p"], created_at=1234.0)
    d = s.to_dict()
    s2 = FenceState.from_dict(d)
    assert s2.name == s.name
    assert s2.expected == s.expected
    assert s2.arrived == s.arrived
    assert s2.created_at == s.created_at


def test_all_returns_all_fences(fence: Fence) -> None:
    fence.create("f1", ["a"])
    fence.create("f2", ["b", "c"])
    names = {s.name for s in fence.all()}
    assert names == {"f1", "f2"}
