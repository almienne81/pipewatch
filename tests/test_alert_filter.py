"""Tests for pipewatch.alert_filter."""

import pytest
from pipewatch.alert_filter import AlertFilter, AlertFilterRule, Severity


# ---------------------------------------------------------------------------
# Severity
# ---------------------------------------------------------------------------

def test_severity_parse_case_insensitive():
    assert Severity.parse("error") == Severity.ERROR
    assert Severity.parse("CRITICAL") == Severity.CRITICAL
    assert Severity.parse("warning") == Severity.WARNING


def test_severity_parse_invalid_raises():
    with pytest.raises(ValueError, match="Unknown severity"):
        Severity.parse("verbose")


def test_severity_ordering():
    assert Severity.DEBUG < Severity.INFO < Severity.WARNING
    assert Severity.WARNING < Severity.ERROR < Severity.CRITICAL


# ---------------------------------------------------------------------------
# AlertFilterRule
# ---------------------------------------------------------------------------

def test_rule_matches_case_insensitive():
    rule = AlertFilterRule(keyword="timeout")
    assert rule.matches("Connection TIMEOUT exceeded")
    assert rule.matches("timeout")
    assert not rule.matches("everything is fine")


# ---------------------------------------------------------------------------
# AlertFilter.should_send
# ---------------------------------------------------------------------------

def test_below_min_severity_suppressed():
    f = AlertFilter(min_severity=Severity.ERROR)
    assert not f.should_send("some warning", Severity.WARNING)
    assert not f.should_send("debug noise", Severity.DEBUG)


def test_at_or_above_min_severity_allowed():
    f = AlertFilter(min_severity=Severity.ERROR)
    assert f.should_send("disk full", Severity.ERROR)
    assert f.should_send("system down", Severity.CRITICAL)


def test_keyword_rule_suppresses_matching_message():
    f = AlertFilter().add_rule("flaky", reason="known flaky test")
    assert not f.should_send("flaky network detected", Severity.ERROR)


def test_keyword_rule_does_not_suppress_non_matching():
    f = AlertFilter().add_rule("flaky")
    assert f.should_send("disk full", Severity.ERROR)


def test_multiple_rules_any_match_suppresses():
    f = AlertFilter().add_rule("flaky").add_rule("test run")
    assert not f.should_send("test run completed", Severity.ERROR)
    assert not f.should_send("flaky connection", Severity.ERROR)
    assert f.should_send("production failure", Severity.ERROR)


# ---------------------------------------------------------------------------
# AlertFilter.suppressed_by
# ---------------------------------------------------------------------------

def test_suppressed_by_returns_matching_rule():
    rule = AlertFilterRule("timeout", reason="known issue")
    f = AlertFilter(suppress_rules=[rule])
    matched = f.suppressed_by("connection timeout")
    assert matched is rule


def test_suppressed_by_returns_none_when_no_match():
    f = AlertFilter().add_rule("timeout")
    assert f.suppressed_by("disk full") is None


# ---------------------------------------------------------------------------
# Serialisation round-trip
# ---------------------------------------------------------------------------

def test_to_dict_from_dict_round_trip():
    original = (
        AlertFilter(min_severity=Severity.ERROR)
        .add_rule("flaky", reason="known")
        .add_rule("test")
    )
    restored = AlertFilter.from_dict(original.to_dict())
    assert restored.min_severity == Severity.ERROR
    assert len(restored.suppress_rules) == 2
    assert restored.suppress_rules[0].keyword == "flaky"
    assert restored.suppress_rules[0].reason == "known"


def test_from_dict_defaults():
    f = AlertFilter.from_dict({})
    assert f.min_severity == Severity.WARNING
    assert f.suppress_rules == []


# ---------------------------------------------------------------------------
# Immutability of add_rule
# ---------------------------------------------------------------------------

def test_add_rule_does_not_mutate_original():
    base = AlertFilter()
    extended = base.add_rule("noise")
    assert len(base.suppress_rules) == 0
    assert len(extended.suppress_rules) == 1
