"""Tests for pipewatch.duration."""

import pytest

from pipewatch.duration import DurationError, format_duration, parse_duration


# ---------------------------------------------------------------------------
# parse_duration
# ---------------------------------------------------------------------------


def test_parse_seconds_short():
    assert parse_duration("30s") == 30.0


def test_parse_seconds_long():
    assert parse_duration("10 seconds") == 10.0


def test_parse_minutes():
    assert parse_duration("5m") == 300.0


def test_parse_minutes_long():
    assert parse_duration("2 minutes") == 120.0


def test_parse_hours():
    assert parse_duration("1h") == 3600.0


def test_parse_hours_long():
    assert parse_duration("1.5 hours") == 5400.0


def test_parse_days():
    assert parse_duration("1d") == 86400.0


def test_parse_days_long():
    assert parse_duration("2 days") == 172800.0


def test_parse_fractional_minutes():
    assert parse_duration("0.5m") == pytest.approx(30.0)


def test_parse_strips_whitespace():
    assert parse_duration("  10s  ") == 10.0


def test_parse_unknown_unit_raises():
    with pytest.raises(DurationError, match="Unknown time unit"):
        parse_duration("5x")


def test_parse_bad_format_raises():
    with pytest.raises(DurationError, match="Cannot parse duration"):
        parse_duration("five minutes")


def test_parse_empty_string_raises():
    with pytest.raises(DurationError):
        parse_duration("")


# ---------------------------------------------------------------------------
# format_duration
# ---------------------------------------------------------------------------


def test_format_zero():
    assert format_duration(0) == "0s"


def test_format_seconds_only():
    assert format_duration(45) == "45s"


def test_format_one_minute_exact():
    assert format_duration(60) == "1m"


def test_format_minutes_and_seconds():
    assert format_duration(90) == "1m 30s"


def test_format_hours_minutes_seconds():
    assert format_duration(3661) == "1h 1m 1s"


def test_format_days():
    assert format_duration(86400) == "1d"


def test_format_days_hours_minutes_seconds():
    assert format_duration(90061) == "1d 1h 1m 1s"


def test_format_negative_raises():
    with pytest.raises(DurationError, match="non-negative"):
        format_duration(-1)


def test_roundtrip_minutes():
    assert parse_duration("5m") == 300.0
    assert format_duration(300) == "5m"
