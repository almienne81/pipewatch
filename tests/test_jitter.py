"""Tests for pipewatch.jitter."""

from __future__ import annotations

import argparse

import pytest

from pipewatch.jitter import (
    JitterError,
    JitterPolicy,
    equal_jitter,
    full_jitter,
)
from pipewatch.cli_jitter import build_jitter_parser


# ---------------------------------------------------------------------------
# JitterPolicy construction
# ---------------------------------------------------------------------------

def test_default_policy_has_expected_values():
    p = JitterPolicy()
    assert p.min_factor == 0.8
    assert p.max_factor == 1.2


def test_negative_min_factor_raises():
    with pytest.raises(JitterError, match="min_factor"):
        JitterPolicy(min_factor=-0.1)


def test_max_less_than_min_raises():
    with pytest.raises(JitterError, match="max_factor"):
        JitterPolicy(min_factor=1.5, max_factor=1.0)


def test_equal_factors_is_deterministic():
    p = JitterPolicy(min_factor=1.0, max_factor=1.0)
    assert p.apply(10.0) == pytest.approx(10.0)


def test_apply_result_within_bounds():
    p = JitterPolicy(min_factor=0.5, max_factor=2.0)
    for seed in range(20):
        result = JitterPolicy(min_factor=0.5, max_factor=2.0, seed=seed).apply(100.0)
        assert 50.0 <= result <= 200.0


def test_apply_negative_base_raises():
    p = JitterPolicy()
    with pytest.raises(JitterError):
        p.apply(-1.0)


def test_to_dict_round_trip():
    p = JitterPolicy(min_factor=0.6, max_factor=1.4)
    assert JitterPolicy.from_dict(p.to_dict()) == p


def test_from_dict_uses_defaults_for_missing_keys():
    p = JitterPolicy.from_dict({})
    assert p.min_factor == 0.8
    assert p.max_factor == 1.2


# ---------------------------------------------------------------------------
# full_jitter
# ---------------------------------------------------------------------------

def test_full_jitter_within_zero_and_base():
    for seed in range(20):
        result = full_jitter(50.0, seed=seed)
        assert 0.0 <= result <= 50.0


def test_full_jitter_zero_base_returns_zero():
    assert full_jitter(0.0) == 0.0


def test_full_jitter_negative_base_raises():
    with pytest.raises(JitterError):
        full_jitter(-5.0)


# ---------------------------------------------------------------------------
# equal_jitter
# ---------------------------------------------------------------------------

def test_equal_jitter_at_least_half_base():
    for seed in range(20):
        result = equal_jitter(40.0, seed=seed)
        assert result >= 20.0
        assert result <= 40.0


def test_equal_jitter_negative_base_raises():
    with pytest.raises(JitterError):
        equal_jitter(-1.0)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser()
    sp = root.add_subparsers(dest="cmd")
    build_jitter_parser(sp)
    return root


def test_build_jitter_parser_registers_subcommands():
    parser = _build_parser()
    args = parser.parse_args(["jitter", "info"])
    assert args.jitter_cmd == "info"


def test_sample_subcommand_parsed(capsys):
    parser = _build_parser()
    args = parser.parse_args(["jitter", "sample", "10.0", "--seed", "42"])
    args.func(args)
    out = capsys.readouterr().out
    assert "base=10.0s" in out


def test_info_subcommand_prints_factors(capsys):
    parser = _build_parser()
    args = parser.parse_args(["jitter", "info", "--min-factor", "0.5", "--max-factor", "1.5"])
    args.func(args)
    out = capsys.readouterr().out
    assert "0.5" in out
    assert "1.5" in out
