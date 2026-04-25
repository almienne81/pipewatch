"""Tests for pipewatch.pipeline_id."""

import pytest

from pipewatch.pipeline_id import (
    PipelineID,
    PipelineIDError,
    generate,
    parse,
)


# ---------------------------------------------------------------------------
# PipelineID dataclass
# ---------------------------------------------------------------------------

def test_short_returns_first_eight_chars():
    pid = PipelineID(run_id="abcdef1234567890", pipeline="etl", timestamp=1.0)
    assert pid.short() == "abcdef12"


def test_str_format():
    pid = PipelineID(run_id="abcdef1234567890", pipeline="etl", timestamp=1.0)
    assert str(pid) == "etl/abcdef12"


def test_to_dict_round_trip():
    pid = PipelineID(run_id="deadbeef" * 8, pipeline="daily", timestamp=9999.5)
    d = pid.to_dict()
    restored = PipelineID.from_dict(d)
    assert restored == pid


def test_from_dict_missing_key_raises():
    with pytest.raises(PipelineIDError):
        PipelineID.from_dict({"run_id": "abc", "pipeline": "p"})


def test_from_dict_bad_timestamp_raises():
    with pytest.raises(PipelineIDError):
        PipelineID.from_dict({"run_id": "abc", "pipeline": "p", "timestamp": "bad"})


# ---------------------------------------------------------------------------
# generate
# ---------------------------------------------------------------------------

def test_generate_returns_pipeline_id():
    pid = generate("etl-daily")
    assert isinstance(pid, PipelineID)
    assert pid.pipeline == "etl-daily"


def test_generate_run_id_is_hex():
    pid = generate("test")
    assert all(c in "0123456789abcdef" for c in pid.run_id)


def test_generate_unique_without_seed():
    a = generate("test")
    b = generate("test")
    assert a.run_id != b.run_id


def test_generate_with_seed_is_deterministic_in_structure():
    pid = generate("test", seed="fixed-seed")
    assert len(pid.run_id) == 64  # sha256 hex digest


def test_generate_empty_pipeline_raises():
    with pytest.raises(PipelineIDError):
        generate("")


def test_generate_non_string_pipeline_raises():
    with pytest.raises(PipelineIDError):
        generate(None)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# parse
# ---------------------------------------------------------------------------

def test_parse_slash_format():
    pid = parse("my-pipeline/abcdef12")
    assert pid.pipeline == "my-pipeline"
    assert pid.run_id == "abcdef12"
    assert pid.timestamp == 0.0


def test_parse_hex_run_id():
    pid = parse("deadbeef")
    assert pid.run_id == "deadbeef"
    assert pid.pipeline == "unknown"


def test_parse_invalid_slash_format_raises():
    with pytest.raises(PipelineIDError):
        parse("bad-format/")


def test_parse_non_hex_raises():
    with pytest.raises(PipelineIDError):
        parse("zzzzzzzz")


def test_parse_too_short_raises():
    with pytest.raises(PipelineIDError):
        parse("abc")
