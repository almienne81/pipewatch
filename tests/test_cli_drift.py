"""Tests for pipewatch.cli_drift."""
import argparse
from pathlib import Path

import pytest

from pipewatch.cli_drift import build_drift_parser, cmd_drift_check, cmd_drift_clear, cmd_drift_show
from pipewatch.drift import DriftTracker


@pytest.fixture
def drift_file(tmp_path: Path) -> Path:
    return tmp_path / "drift.json"


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd")
    build_drift_parser(sub)
    return p


def _parse(args: list) -> argparse.Namespace:
    return _build_parser().parse_args(args)


def test_build_drift_parser_registers_subcommands():
    p = _build_parser()
    assert p is not None


def test_check_subcommand_records_and_prints(drift_file: Path, capsys):
    ns = _parse(["drift", "check", "--file", str(drift_file), "1.5"])
    ns.func(ns)
    out = capsys.readouterr().out
    assert "duration" in out
    assert "1.500" in out


def test_check_with_insufficient_data_shows_no_baseline(drift_file: Path, capsys):
    ns = _parse(["drift", "check", "--file", str(drift_file), "2.0"])
    ns.func(ns)
    out = capsys.readouterr().out
    assert "insufficient data" in out


def test_show_empty(drift_file: Path, capsys):
    ns = _parse(["drift", "show", "--file", str(drift_file)])
    ns.func(ns)
    out = capsys.readouterr().out
    assert "No samples" in out


def test_show_with_samples(drift_file: Path, capsys):
    t = DriftTracker(path=drift_file)
    t.record(1.0)
    t.record(2.0)
    ns = _parse(["drift", "show", "--file", str(drift_file)])
    ns.func(ns)
    out = capsys.readouterr().out
    assert "1.000" in out
    assert "2.000" in out
    assert "Total: 2" in out


def test_clear_removes_history(drift_file: Path, capsys):
    t = DriftTracker(path=drift_file)
    t.record(1.0)
    ns = _parse(["drift", "clear", "--file", str(drift_file)])
    ns.func(ns)
    out = capsys.readouterr().out
    assert "cleared" in out
    assert DriftTracker(path=drift_file).samples() == []


def test_check_drift_flagged_for_outlier(drift_file: Path, capsys):
    t = DriftTracker(path=drift_file)
    for _ in range(5):
        t.record(1.0)
    ns = _parse(["drift", "check", "--file", str(drift_file),
                 "--threshold", "2.0", "999.0"])
    ns.func(ns)
    out = capsys.readouterr().out
    assert "YES" in out
