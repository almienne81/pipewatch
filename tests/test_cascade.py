"""Tests for pipewatch.cascade."""

import pytest

from pipewatch.cascade import CascadeError, CascadeGraph, CascadePolicy


# ---------------------------------------------------------------------------
# CascadePolicy
# ---------------------------------------------------------------------------

def test_default_policy_values():
    p = CascadePolicy()
    assert p.stop_on_failure is True
    assert p.blocked_stages == []


def test_policy_to_dict_round_trip():
    p = CascadePolicy(stop_on_failure=False, blocked_stages=["stage_b"])
    d = p.to_dict()
    p2 = CascadePolicy.from_dict(d)
    assert p2.stop_on_failure is False
    assert p2.blocked_stages == ["stage_b"]


def test_policy_from_dict_defaults():
    p = CascadePolicy.from_dict({})
    assert p.stop_on_failure is True
    assert p.blocked_stages == []


# ---------------------------------------------------------------------------
# CascadeGraph – registration
# ---------------------------------------------------------------------------

def test_add_stage_empty_name_raises():
    g = CascadeGraph()
    with pytest.raises(CascadeError):
        g.add_stage("")


def test_add_stage_no_deps():
    g = CascadeGraph()
    g.add_stage("extract")
    assert "extract" in g._deps
    assert g._deps["extract"] == []


# ---------------------------------------------------------------------------
# CascadeGraph – blocked_by_failures
# ---------------------------------------------------------------------------

def test_no_failures_nothing_blocked():
    g = CascadeGraph()
    g.add_stage("a")
    g.add_stage("b", depends_on=["a"])
    assert g.blocked_by_failures(set()) == []


def test_upstream_failure_blocks_downstream():
    g = CascadeGraph()
    g.add_stage("extract")
    g.add_stage("transform", depends_on=["extract"])
    g.add_stage("load", depends_on=["transform"])
    blocked = g.blocked_by_failures({"extract"})
    assert "transform" in blocked
    assert "load" not in blocked  # only direct deps checked per call


def test_failed_stage_not_included_in_blocked():
    g = CascadeGraph()
    g.add_stage("a")
    g.add_stage("b", depends_on=["a"])
    blocked = g.blocked_by_failures({"a", "b"})
    assert "b" not in blocked


# ---------------------------------------------------------------------------
# CascadeGraph – execution_order
# ---------------------------------------------------------------------------

def test_execution_order_respects_deps():
    g = CascadeGraph()
    g.add_stage("load", depends_on=["transform"])
    g.add_stage("transform", depends_on=["extract"])
    g.add_stage("extract")
    order = g.execution_order()
    assert order.index("extract") < order.index("transform")
    assert order.index("transform") < order.index("load")


def test_execution_order_unknown_dep_raises():
    g = CascadeGraph()
    g.add_stage("b", depends_on=["missing"])
    with pytest.raises(CascadeError, match="missing"):
        g.execution_order()


# ---------------------------------------------------------------------------
# CascadeGraph – serialisation
# ---------------------------------------------------------------------------

def test_graph_to_dict_round_trip():
    g = CascadeGraph()
    g.add_stage("a")
    g.add_stage("b", depends_on=["a"])
    g2 = CascadeGraph.from_dict(g.to_dict())
    assert g2._deps == g._deps


def test_from_dict_empty():
    g = CascadeGraph.from_dict({})
    assert g._deps == {}
