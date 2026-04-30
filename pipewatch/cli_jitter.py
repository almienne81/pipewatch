"""CLI sub-commands for inspecting jitter policy settings."""

from __future__ import annotations

import argparse

from pipewatch.jitter import JitterPolicy, full_jitter, equal_jitter


def cmd_jitter_info(args: argparse.Namespace) -> None:
    """Print a summary of the jitter policy."""
    policy = JitterPolicy(
        min_factor=args.min_factor,
        max_factor=args.max_factor,
    )
    print(f"min_factor : {policy.min_factor}")
    print(f"max_factor : {policy.max_factor}")
    print(f"mode       : {args.mode}")


def cmd_jitter_sample(args: argparse.Namespace) -> None:
    """Print a sample jittered delay for a given base value."""
    base = args.base_seconds
    mode = args.mode
    seed = args.seed

    if mode == "full":
        result = full_jitter(base, seed=seed)
    elif mode == "equal":
        result = equal_jitter(base, seed=seed)
    else:
        policy = JitterPolicy(
            min_factor=args.min_factor,
            max_factor=args.max_factor,
            seed=seed,
        )
        result = policy.apply(base)

    print(f"{result:.4f}s  (base={base}s, mode={mode})")


def build_jitter_parser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    """Register 'jitter' sub-commands onto *subparsers*."""
    p = subparsers.add_parser("jitter", help="Jitter policy utilities")
    sp = p.add_subparsers(dest="jitter_cmd", required=True)

    # Shared flags
    def _add_common(parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--min-factor", type=float, default=0.8, dest="min_factor")
        parser.add_argument("--max-factor", type=float, default=1.2, dest="max_factor")
        parser.add_argument(
            "--mode",
            choices=["policy", "full", "equal"],
            default="policy",
        )

    info_p = sp.add_parser("info", help="Show jitter policy settings")
    _add_common(info_p)
    info_p.set_defaults(func=cmd_jitter_info)

    sample_p = sp.add_parser("sample", help="Compute a sample jittered delay")
    sample_p.add_argument("base_seconds", type=float, help="Base delay in seconds")
    sample_p.add_argument("--seed", type=int, default=None)
    _add_common(sample_p)
    sample_p.set_defaults(func=cmd_jitter_sample)
