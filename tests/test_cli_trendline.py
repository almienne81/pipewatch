"""Tests for pipewatch.cli_trendline."""
import argparse
import json
import pytest

from pipewatch.cli_trendline import build_trendline_parser, cmd_trendline_check
from pipewatch.history import History
from pipewatch.report import format_entry


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd")
    build_trendline_parser(sub)
    return p


def _parse(parser, args):
    return parser.parse_args(args)


def test_build_trendline_parser_registers_subcommands():
    p = _build_parser()
    ns = _parse(p, ["trendline", "check", "--help"])
    # argparse raises SystemExit on --help; reaching here means subparser exists


pytest.mark.parametrize  # silence linter — used below


def test_check_insufficient_data_exits_cleanly(tmp_path, capsys):
    hfile = str(tmp_path / "h.json")
    h = History(hfile)
    # only 2 entries — below default min_samples of 5
    for d in [1.0, 2.0]:
        h.append({"command": "x", "exit_code": 0, "duration_seconds": d,
                  "started_at": "2024-01-01T00:00:00", "finished_at": "2024-01-01T00:00:01"})

    p = _build_parser()
    ns = _parse(p, ["trendline", "check", "--history-file", hfile])
    ns.func(ns)  # should not raise SystemExit
    out = capsys.readouterr().out
    assert "insufficient_data" in out


def test_check_ok_series_no_exit(tmp_path, capsys):
    hfile = str(tmp_path / "h.json")
    h = History(hfile)
    for _ in range(8):
        h.append({"command": "x", "exit_code": 0, "duration_seconds": 1.0,
                  "started_at": "2024-01-01T00:00:00", "finished_at": "2024-01-01T00:00:01"})

    p = _build_parser()
    ns = _parse(p, ["trendline", "check", "--history-file", hfile])
    ns.func(ns)
    out = capsys.readouterr().out
    assert "ok" in out


def test_check_json_output(tmp_path, capsys):
    hfile = str(tmp_path / "h.json")
    h = History(hfile)
    for _ in range(6):
        h.append({"command": "x", "exit_code": 0, "duration_seconds": 1.0,
                  "started_at": "2024-01-01T00:00:00", "finished_at": "2024-01-01T00:00:01"})

    p = _build_parser()
    ns = _parse(p, ["trendline", "check", "--history-file", hfile, "--json"])
    ns.func(ns)
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "slope" in data
    assert "status" in data


def test_check_fail_exits_with_code_two(tmp_path):
    hfile = str(tmp_path / "h.json")
    h = History(hfile)
    for i in range(8):
        h.append({"command": "x", "exit_code": 0, "duration_seconds": float(i * 5),
                  "started_at": "2024-01-01T00:00:00", "finished_at": "2024-01-01T00:00:01"})

    p = _build_parser()
    ns = _parse(p, ["trendline", "check", "--history-file", hfile,
                    "--warn", "0.1", "--fail", "0.5"])
    with pytest.raises(SystemExit) as exc:
        ns.func(ns)
    assert exc.value.code == 2
