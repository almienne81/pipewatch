"""Unit tests for pipewatch.cli_timeout."""

from __future__ import annotations

import argparse
import pytest

from pipewatch.cli_timeout import build_timeout_parser, cmd_timeout_info


def _build_parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser()
    sub = root.add_subparsers(dest="cmd")
    build_timeout_parser(sub)
    return root


def _parse(args: list[str]) -> argparse.Namespace:
    return _build_parser().parse_args(args)


def test_build_timeout_parser_registers_subcommands():
    root = argparse.ArgumentParser()
    sub = root.add_subparsers(dest="cmd")
    p = build_timeout_parser(sub)
    assert p is not None


def test_info_no_duration(capsys):
    ns = _parse(["timeout", "info"])
    ns.func(ns)
    out = capsys.readouterr().out
    assert "disabled" in out


def test_info_with_duration(capsys):
    ns = _parse(["timeout", "info", "--duration", "2m"])
    ns.func(ns)
    out = capsys.readouterr().out
    assert "2m" in out or "120" in out


def test_info_no_kill_flag(capsys):
    ns = _parse(["timeout", "info", "--duration", "30s", "--no-kill"])
    ns.func(ns)
    out = capsys.readouterr().out
    assert "raise only" in out


def test_info_kill_default(capsys):
    ns = _parse(["timeout", "info", "--duration", "30s"])
    ns.func(ns)
    out = capsys.readouterr().out
    assert "kill" in out


def test_info_invalid_duration_exits(capsys):
    ns = _parse(["timeout", "info", "--duration", "badvalue"])
    with pytest.raises(SystemExit) as exc_info:
        ns.func(ns)
    assert exc_info.value.code == 1
    err = capsys.readouterr().err
    assert "error" in err
