"""CLI helpers for signal trap introspection."""
from __future__ import annotations

import argparse
import signal

from pipewatch.signal_trap import SignalTrap


_KNOWN: dict[str, int] = {
    "SIGINT": signal.SIGINT,
    "SIGTERM": signal.SIGTERM,
    "SIGHUP": getattr(signal, "SIGHUP", None),  # type: ignore[assignment]
}


def cmd_signal_trap_info(args: argparse.Namespace) -> None:
    """Print information about a SignalTrap configuration."""
    sigs: list[int] = []
    for name in args.signals:
        num = _KNOWN.get(name.upper())
        if num is None:
            print(f"Unknown signal: {name}")
            raise SystemExit(1)
        sigs.append(num)

    trap = SignalTrap(signals=sigs)
    info = trap.to_dict()
    sig_names = [signal.Signals(s).name for s in info["signals"]]
    print(f"Watching : {', '.join(sig_names)}")
    print(f"Triggered: {info['triggered']}")


def cmd_signal_trap_list(args: argparse.Namespace) -> None:  # noqa: ARG001
    """List signals that SignalTrap monitors by default."""
    default_trap = SignalTrap()
    for sig in default_trap.signals:
        try:
            name = signal.Signals(sig).name
        except ValueError:
            name = str(sig)
        print(f"  {sig:2d}  {name}")


def build_signal_trap_parser(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = sub.add_parser("signal-trap", help="Signal trap utilities")
    sp = p.add_subparsers(dest="signal_trap_cmd", required=True)

    info_p = sp.add_parser("info", help="Show trap configuration for given signals")
    info_p.add_argument(
        "signals",
        nargs="+",
        metavar="SIGNAL",
        help="Signal names, e.g. SIGINT SIGTERM",
    )
    info_p.set_defaults(func=cmd_signal_trap_info)

    list_p = sp.add_parser("list", help="List default watched signals")
    list_p.set_defaults(func=cmd_signal_trap_list)
