"""Tests for pipewatch.signal_trap."""
from __future__ import annotations

import signal
import argparse

import pytest

from pipewatch.signal_trap import SignalTrap, SignalTrapError
from pipewatch.cli_signal_trap import build_signal_trap_parser, cmd_signal_trap_info, cmd_signal_trap_list


# ---------------------------------------------------------------------------
# Unit tests – SignalTrap
# ---------------------------------------------------------------------------

def test_empty_signals_raises():
    with pytest.raises(SignalTrapError):
        SignalTrap(signals=[])


def test_default_signals_include_sigint_and_sigterm():
    trap = SignalTrap()
    assert signal.SIGINT in trap.signals
    assert signal.SIGTERM in trap.signals


def test_not_triggered_initially():
    trap = SignalTrap()
    assert not trap.triggered
    assert trap.signal_received is None


def test_manual_handle_sets_triggered():
    trap = SignalTrap(signals=[signal.SIGUSR1])
    trap._handle(signal.SIGUSR1, None)
    assert trap.triggered
    assert trap.signal_received == signal.SIGUSR1


def test_reset_clears_triggered():
    trap = SignalTrap(signals=[signal.SIGUSR1])
    trap._handle(signal.SIGUSR1, None)
    trap.reset()
    assert not trap.triggered


def test_callback_invoked_on_signal():
    received: list[int] = []
    trap = SignalTrap(signals=[signal.SIGUSR1])
    trap.add_callback(received.append)
    trap._handle(signal.SIGUSR1, None)
    assert received == [signal.SIGUSR1]


def test_callback_exception_does_not_propagate():
    def bad_cb(_sig: int) -> None:
        raise RuntimeError("boom")

    trap = SignalTrap(signals=[signal.SIGUSR1])
    trap.add_callback(bad_cb)
    trap._handle(signal.SIGUSR1, None)  # must not raise
    assert trap.triggered


def test_to_dict_shape():
    trap = SignalTrap()
    d = trap.to_dict()
    assert "signals" in d
    assert "triggered" in d
    assert "signal_received" in d


def test_context_manager_arms_and_disarms():
    trap = SignalTrap(signals=[signal.SIGUSR1])
    with trap:
        assert signal.getsignal(signal.SIGUSR1) == trap._handle
    # After exit the original handler is restored (not our _handle)
    assert signal.getsignal(signal.SIGUSR1) != trap._handle


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")
    build_signal_trap_parser(sub)
    return parser


def test_build_signal_trap_parser_registers_subcommands():
    parser = _build_parser()
    args = parser.parse_args(["signal-trap", "list"])
    assert args.signal_trap_cmd == "list"


def test_list_subcommand_prints(capsys):
    args = argparse.Namespace()
    cmd_signal_trap_list(args)
    out = capsys.readouterr().out
    assert "SIGINT" in out or "2" in out


def test_info_valid_signals(capsys):
    args = argparse.Namespace(signals=["SIGINT", "SIGTERM"])
    cmd_signal_trap_info(args)
    out = capsys.readouterr().out
    assert "SIGINT" in out
    assert "SIGTERM" in out


def test_info_unknown_signal_exits():
    args = argparse.Namespace(signals=["SIGFAKE"])
    with pytest.raises(SystemExit):
        cmd_signal_trap_info(args)
