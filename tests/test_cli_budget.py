"""Unit tests for pipewatch.cli_budget."""
import argparse
import pytest

from pipewatch.cli_budget import build_budget_parser, cmd_budget_info, cmd_budget_check


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")
    build_budget_parser(sub)
    return parser


def _parse(args):
    return _build_parser().parse_args(["budget"] + args)


def test_build_budget_parser_registers_subcommands():
    parser = _build_parser()
    ns = parser.parse_args(["budget", "info"])
    assert ns.func == cmd_budget_info


def test_info_no_limits(capsys):
    ns = _parse(["info"])
    ns.func(ns)
    out = capsys.readouterr().out
    assert "warn_seconds" in out
    assert "None" in out


def test_info_with_limits(capsys):
    ns = _parse(["info", "--warn", "5m", "--fail", "10m"])
    ns.func(ns)
    out = capsys.readouterr().out
    assert "300" in out
    assert "600" in out


def test_info_invalid_budget_exits(capsys):
    ns = _parse(["info", "--warn", "10m", "--fail", "5m"])
    with pytest.raises(SystemExit) as exc:
        ns.func(ns)
    assert exc.value.code == 1


def test_check_within_budget(capsys):
    ns = _parse(["check", "30s", "--warn", "1m", "--fail", "2m"])
    ns.func(ns)
    out = capsys.readouterr().out
    assert "[OK]" in out


def test_check_warn_exceeded(capsys):
    ns = _parse(["check", "90s", "--warn", "1m", "--fail", "3m"])
    ns.func(ns)
    out = capsys.readouterr().out
    assert "[WARN]" in out


def test_check_fail_exceeded_exits(capsys):
    ns = _parse(["check", "200s", "--warn", "1m", "--fail", "2m"])
    with pytest.raises(SystemExit) as exc:
        ns.func(ns)
    assert exc.value.code == 2
    out = capsys.readouterr().out
    assert "[FAIL]" in out
