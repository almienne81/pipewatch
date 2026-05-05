"""Tests for pipewatch.cli_quota."""
from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from pipewatch.cli_quota import build_quota_parser, cmd_quota_check, cmd_quota_record, cmd_quota_reset


@pytest.fixture()
def quota_file(tmp_path: Path) -> Path:
    return tmp_path / "quota.json"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    build_quota_parser(sub)
    return parser


def _parse(args: list) -> argparse.Namespace:
    return _build_parser().parse_args(args)


def test_build_quota_parser_registers_subcommands() -> None:
    parser = _build_parser()
    # Should not raise
    ns = parser.parse_args(["quota-check", "--job", "etl"])
    assert ns.job == "etl"


def test_quota_check_ok(quota_file: Path, capsys: pytest.CaptureFixture) -> None:
    ns = argparse.Namespace(
        file=str(quota_file), job="etl", max_runs=5, window=60
    )
    cmd_quota_check(ns)
    out = capsys.readouterr().out
    assert "OK" in out
    assert "5/5" in out


def test_quota_record_decrements_remaining(quota_file: Path, capsys: pytest.CaptureFixture) -> None:
    ns = argparse.Namespace(
        file=str(quota_file), job="etl", max_runs=3, window=60
    )
    cmd_quota_record(ns)
    out = capsys.readouterr().out
    assert "2/3" in out


def test_quota_check_exceeded(quota_file: Path, capsys: pytest.CaptureFixture) -> None:
    ns = argparse.Namespace(
        file=str(quota_file), job="etl", max_runs=1, window=60
    )
    cmd_quota_record(ns)
    cmd_quota_check(ns)
    out = capsys.readouterr().out
    assert "EXCEEDED" in out


def test_quota_reset_clears_job(quota_file: Path, capsys: pytest.CaptureFixture) -> None:
    record_ns = argparse.Namespace(
        file=str(quota_file), job="etl", max_runs=2, window=60
    )
    cmd_quota_record(record_ns)
    reset_ns = argparse.Namespace(file=str(quota_file), job="etl")
    cmd_quota_reset(reset_ns)
    out = capsys.readouterr().out
    assert "cleared" in out.lower()


def test_default_file_value() -> None:
    ns = _parse(["quota-check", "--job", "myjob"])
    assert ns.file == ".pipewatch_quota.json"
    assert ns.max_runs == 10
    assert ns.window == 3600
