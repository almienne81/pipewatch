"""Tests for pipewatch.sampling and pipewatch.cli_sampling."""
from __future__ import annotations

import argparse

import pytest

from pipewatch.sampling import SamplingError, SamplingPolicy, sample_filter
from pipewatch.cli_sampling import build_sampling_parser


# ---------------------------------------------------------------------------
# SamplingPolicy unit tests
# ---------------------------------------------------------------------------

def test_default_rate_is_one():
    p = SamplingPolicy()
    assert p.rate == 1.0


def test_rate_above_one_raises():
    with pytest.raises(SamplingError):
        SamplingPolicy(rate=1.1)


def test_rate_below_zero_raises():
    with pytest.raises(SamplingError):
        SamplingPolicy(rate=-0.1)


def test_rate_one_always_samples():
    p = SamplingPolicy(rate=1.0)
    assert all(p.should_sample() for _ in range(50))


def test_rate_zero_never_samples():
    p = SamplingPolicy(rate=0.0)
    assert not any(p.should_sample() for _ in range(50))


def test_seeded_policy_is_deterministic():
    p1 = SamplingPolicy(rate=0.5, seed=42)
    p2 = SamplingPolicy(rate=0.5, seed=42)
    results1 = [p1.should_sample() for _ in range(20)]
    results2 = [p2.should_sample() for _ in range(20)]
    assert results1 == results2


def test_to_dict_round_trip():
    p = SamplingPolicy(rate=0.75, seed=7)
    d = p.to_dict()
    p2 = SamplingPolicy.from_dict(d)
    assert p2.rate == p.rate
    assert p2.seed == p.seed


def test_from_dict_defaults():
    p = SamplingPolicy.from_dict({})
    assert p.rate == 1.0
    assert p.seed is None


# ---------------------------------------------------------------------------
# sample_filter tests
# ---------------------------------------------------------------------------

def test_sample_filter_rate_one_keeps_all():
    p = SamplingPolicy(rate=1.0)
    items = list(range(10))
    assert sample_filter(p, items) == items


def test_sample_filter_rate_zero_keeps_none():
    p = SamplingPolicy(rate=0.0)
    assert sample_filter(p, list(range(10))) == []


def test_sample_filter_partial_rate_reduces_list():
    p = SamplingPolicy(rate=0.5, seed=0)
    items = list(range(100))
    result = sample_filter(p, items)
    assert 0 < len(result) < 100


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser()
    sp = root.add_subparsers(dest="cmd")
    build_sampling_parser(sp)
    return root


def _parse(args: list[str]) -> argparse.Namespace:
    return _build_parser().parse_args(args)


def test_build_sampling_parser_registers_subcommands():
    p = _build_parser()
    # Should not raise
    ns = _parse(["sampling", "info"])
    assert ns.rate == 1.0


def test_info_default_rate(capsys):
    ns = _parse(["sampling", "info"])
    ns.func(ns)
    out = capsys.readouterr().out
    assert "100.0%" in out


def test_info_custom_rate(capsys):
    ns = _parse(["sampling", "info", "--rate", "0.25"])
    ns.func(ns)
    out = capsys.readouterr().out
    assert "25.0%" in out


def test_info_invalid_rate_exits():
    ns = _parse(["sampling", "info", "--rate", "2.0"])
    with pytest.raises(SystemExit):
        ns.func(ns)


def test_trial_output_contains_counts(capsys):
    ns = _parse(["sampling", "trial", "--rate", "1.0", "-n", "10"])
    ns.func(ns)
    out = capsys.readouterr().out
    assert "Trials : 10" in out
    assert "Kept   : 10" in out
