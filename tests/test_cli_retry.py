"""Tests for pipewatch.cli_retry."""
from __future__ import annotations

import argparse
import sys

import pytest

from pipewatch.cli_retry import build_retry_parser, cmd_retry_info


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="cmd")
    build_retry_parser(subparsers)
    return parser


def _parse(args: list) -> argparse.Namespace:
    return _build_parser().parse_args(args)


def test_retry_info_defaults(capsys):
    ns = _parse(["retry", "info"])
    ns.func(ns)
    out = capsys.readouterr().out
    assert "Max attempts : 1" in out
    assert "Initial delay: 5.0s" in out
    assert "Backoff factor: 1.0x" in out


def test_retry_info_custom_values(capsys):
    ns = _parse(["retry", "info", "--max-attempts", "4", "--delay", "2.0", "--backoff", "2.0"])
    ns.func(ns)
    out = capsys.readouterr().out
    assert "Max attempts : 4" in out
    assert "Initial delay: 2.0s" in out
    assert "Backoff factor: 2.0x" in out
    # Three retries => three delay lines
    assert "Before attempt 2" in out
    assert "Before attempt 4" in out


def test_retry_info_invalid_max_attempts_exits(capsys):
    ns = _parse(["retry", "info", "--max-attempts", "0"])
    with pytest.raises(SystemExit) as exc_info:
        ns.func(ns)
    assert exc_info.value.code == 1
    err = capsys.readouterr().err
    assert "max_attempts" in err


def test_retry_info_no_retries_shows_no_schedule(capsys):
    """When max_attempts=1 there are no retries so schedule section is empty."""
    ns = _parse(["retry", "info", "--max-attempts", "1"])
    ns.func(ns)
    out = capsys.readouterr().out
    assert "Before attempt" not in out


def test_build_retry_parser_registers_subcommand():
    parser = _build_parser()
    # Should not raise
    ns = parser.parse_args(["retry", "info"])
    assert ns.cmd == "retry"
    assert ns.retry_cmd == "info"
