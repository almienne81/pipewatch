"""Tests for pipewatch.scheduler."""

from datetime import datetime

import pytest

from pipewatch.scheduler import Schedule, parse_schedule, _field_matches


# ---------------------------------------------------------------------------
# parse_schedule
# ---------------------------------------------------------------------------

def test_parse_valid_expression():
    s = parse_schedule("30 6 * * 1")
    assert s.minute == "30"
    assert s.hour == "6"
    assert s.day_of_week == "1"


def test_parse_alias_daily():
    s = parse_schedule("@daily")
    assert s.minute == "0"
    assert s.hour == "0"
    assert s.raw == "0 0 * * *"


def test_parse_alias_hourly():
    s = parse_schedule("@hourly")
    assert s.minute == "0"
    assert s.hour == "*"


def test_parse_invalid_raises():
    with pytest.raises(ValueError, match="expected 5 fields"):
        parse_schedule("* * *")


# ---------------------------------------------------------------------------
# _field_matches
# ---------------------------------------------------------------------------

def test_wildcard_always_matches():
    assert _field_matches("*", 0)
    assert _field_matches("*", 59)


def test_exact_value_matches():
    assert _field_matches("15", 15)
    assert not _field_matches("15", 16)


def test_step_matches():
    assert _field_matches("*/5", 0)
    assert _field_matches("*/5", 15)
    assert not _field_matches("*/5", 7)


def test_range_matches():
    assert _field_matches("9-17", 12)
    assert _field_matches("9-17", 9)
    assert not _field_matches("9-17", 18)


def test_list_matches():
    assert _field_matches("1,3,5", 3)
    assert not _field_matches("1,3,5", 4)


def test_unsupported_syntax_raises():
    with pytest.raises(ValueError):
        _field_matches("abc", 1)


# ---------------------------------------------------------------------------
# Schedule.is_due
# ---------------------------------------------------------------------------

def test_is_due_exact_match():
    s = parse_schedule("30 8 15 6 *")
    dt = datetime(2024, 6, 15, 8, 30)
    assert s.is_due(dt)


def test_is_due_no_match():
    s = parse_schedule("30 8 15 6 *")
    dt = datetime(2024, 6, 15, 8, 31)
    assert not s.is_due(dt)


def test_is_due_every_minute():
    s = parse_schedule("* * * * *")
    assert s.is_due(datetime(2024, 1, 1, 0, 0))
    assert s.is_due(datetime(2024, 12, 31, 23, 59))


def test_is_due_step():
    s = parse_schedule("*/15 * * * *")
    assert s.is_due(datetime(2024, 1, 1, 0, 0))
    assert s.is_due(datetime(2024, 1, 1, 0, 30))
    assert not s.is_due(datetime(2024, 1, 1, 0, 7))
