"""CLI commands for inspecting stagger policies."""
from __future__ import annotations

import argparse

from pipewatch.stagger import (
    StaggerPolicy,
    StaggerError,
    all_delays,
    delay_for_job,
)


def cmd_stagger_info(args: argparse.Namespace) -> None:
    """Print stagger policy details."""
    try:
        policy = StaggerPolicy(
            window_seconds=args.window,
            slots=args.slots,
            offset_seconds=args.offset,
        )
    except StaggerError as exc:
        print(f"error: {exc}")
        raise SystemExit(1)

    print(f"window : {policy.window_seconds}s")
    print(f"slots  : {policy.slots}")
    print(f"offset : {policy.offset_seconds}s")
    step = policy.window_seconds / policy.slots
    print(f"step   : {step:.3f}s per slot")


def cmd_stagger_delays(args: argparse.Namespace) -> None:
    """Print all slot delays for a policy."""
    try:
        policy = StaggerPolicy(
            window_seconds=args.window,
            slots=args.slots,
            offset_seconds=args.offset,
        )
    except StaggerError as exc:
        print(f"error: {exc}")
        raise SystemExit(1)

    for i, delay in enumerate(all_delays(policy)):
        print(f"slot {i:>3}: {delay:.3f}s")


def cmd_stagger_job(args: argparse.Namespace) -> None:
    """Print the stagger delay for a specific job name."""
    try:
        policy = StaggerPolicy(
            window_seconds=args.window,
            slots=args.slots,
            offset_seconds=args.offset,
        )
    except StaggerError as exc:
        print(f"error: {exc}")
        raise SystemExit(1)

    delay = delay_for_job(policy, args.job)
    print(f"{args.job}: {delay:.3f}s")


def _add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--window", type=float, default=60.0,
                        help="Window size in seconds (default: 60)")
    parser.add_argument("--slots", type=int, default=1,
                        help="Number of slots (default: 1)")
    parser.add_argument("--offset", type=float, default=0.0,
                        help="Base offset in seconds (default: 0)")


def build_stagger_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("stagger", help="Stagger policy utilities")
    sp = p.add_subparsers(dest="stagger_cmd", required=True)

    info = sp.add_parser("info", help="Show policy summary")
    _add_common(info)
    info.set_defaults(func=cmd_stagger_info)

    delays = sp.add_parser("delays", help="List all slot delays")
    _add_common(delays)
    delays.set_defaults(func=cmd_stagger_delays)

    job = sp.add_parser("job", help="Delay for a specific job")
    _add_common(job)
    job.add_argument("job", help="Job name")
    job.set_defaults(func=cmd_stagger_job)
