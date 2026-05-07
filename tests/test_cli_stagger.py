"""Tests for pipewatch.cli_stagger."""
import argparse
import pytest
from pipewatch.cli_stagger import (
    build_stagger_parser,
    cmd_stagger_info,
    cmd_stagger_delays,
    cmd_stagger_job,
)


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    sp = p.add_subparsers(dest="cmd")
    build_stagger_parser(sp)
    return p


def _parse(args):
    return _build_parser().parse_args(args)


def test_build_stagger_parser_registers_subcommands():
    p = _build_parser()
    # Should not raise
    ns = p.parse_args(["stagger", "info"])
    assert ns.cmd == "stagger"


def test_info_defaults(capsys):
    ns = _parse(["stagger", "info"])
    ns.func(ns)
    out = capsys.readouterr().out
    assert "60.0s" in out
    assert "slots" in out


def test_info_custom_values(capsys):
    ns = _parse(["stagger", "info", "--window", "120", "--slots", "4", "--offset", "5"])
    ns.func(ns)
    out = capsys.readouterr().out
    assert "120.0s" in out
    assert "4" in out


def test_info_invalid_window_exits(capsys):
    ns = _parse(["stagger", "info", "--window", "0"])
    with pytest.raises(SystemExit) as exc_info:
        ns.func(ns)
    assert exc_info.value.code == 1
    assert "error" in capsys.readouterr().out


def test_delays_output_has_correct_count(capsys):
    ns = _parse(["stagger", "delays", "--slots", "3", "--window", "90"])
    ns.func(ns)
    out = capsys.readouterr().out
    lines = [l for l in out.strip().splitlines() if l.startswith("slot")]
    assert len(lines) == 3


def test_delays_invalid_slots_exits(capsys):
    ns = _parse(["stagger", "delays", "--slots", "0"])
    with pytest.raises(SystemExit) as exc_info:
        ns.func(ns)
    assert exc_info.value.code == 1


def test_job_subcommand_prints_delay(capsys):
    ns = _parse(["stagger", "job", "--window", "60", "--slots", "4", "my-pipeline"])
    ns.func(ns)
    out = capsys.readouterr().out
    assert "my-pipeline" in out
    assert "s" in out


def test_job_invalid_policy_exits(capsys):
    ns = _parse(["stagger", "job", "--window", "-1", "some-job"])
    with pytest.raises(SystemExit) as exc_info:
        ns.func(ns)
    assert exc_info.value.code == 1
