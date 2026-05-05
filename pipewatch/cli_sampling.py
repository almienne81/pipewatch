"""CLI sub-commands for inspecting sampling policy configuration."""
from __future__ import annotations

import argparse

from pipewatch.sampling import SamplingError, SamplingPolicy


def cmd_sampling_info(args: argparse.Namespace) -> None:
    """Print a summary of the sampling policy."""
    try:
        policy = SamplingPolicy(rate=args.rate, seed=args.seed)
    except SamplingError as exc:
        print(f"error: {exc}")
        raise SystemExit(1) from exc

    pct = policy.rate * 100
    print(f"Sampling rate : {policy.rate:.4f}  ({pct:.1f}%)")
    if policy.seed is not None:
        print(f"RNG seed      : {policy.seed}")
    else:
        print("RNG seed      : (random)")


def cmd_sampling_trial(args: argparse.Namespace) -> None:
    """Run *n* trial draws and report how many would be sampled."""
    try:
        policy = SamplingPolicy(rate=args.rate, seed=args.seed)
    except SamplingError as exc:
        print(f"error: {exc}")
        raise SystemExit(1) from exc

    kept = sum(1 for _ in range(args.n) if policy.should_sample())
    print(f"Trials : {args.n}")
    print(f"Kept   : {kept}  ({kept / args.n * 100:.1f}%)")


def _add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--rate",
        type=float,
        default=1.0,
        help="Sampling rate in [0.0, 1.0] (default: 1.0)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Optional RNG seed for reproducibility",
    )


def build_sampling_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("sampling", help="Sampling policy utilities")
    sp = p.add_subparsers(dest="sampling_cmd", required=True)

    info_p = sp.add_parser("info", help="Show sampling policy details")
    _add_common(info_p)
    info_p.set_defaults(func=cmd_sampling_info)

    trial_p = sp.add_parser("trial", help="Simulate N sampling draws")
    _add_common(trial_p)
    trial_p.add_argument(
        "-n",
        type=int,
        default=100,
        help="Number of trial draws (default: 100)",
    )
    trial_p.set_defaults(func=cmd_sampling_trial)
