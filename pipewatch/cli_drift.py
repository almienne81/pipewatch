"""CLI commands for drift detection."""
from __future__ import annotations

import argparse
from pathlib import Path

from pipewatch.drift import DriftPolicy, DriftTracker


def _resolve_path(args: argparse.Namespace) -> Path:
    return Path(args.file)


def cmd_drift_check(args: argparse.Namespace) -> None:
    policy = DriftPolicy(
        baseline_window=args.window,
        z_score_threshold=args.threshold,
    )
    tracker = DriftTracker(path=_resolve_path(args), policy=policy)
    result = tracker.record(args.duration)
    print(f"duration   : {result.duration:.3f}s")
    if result.baseline_mean is not None:
        print(f"baseline   : mean={result.baseline_mean:.3f}s  stdev={result.baseline_stdev:.3f}s")
        print(f"z-score    : {result.z_score:.3f}")
    else:
        print("baseline   : insufficient data")
    print(f"drifted    : {'YES' if result.is_drifted else 'no'}")


def cmd_drift_show(args: argparse.Namespace) -> None:
    tracker = DriftTracker(path=_resolve_path(args))
    samples = tracker.samples()
    if not samples:
        print("No samples recorded.")
        return
    for i, s in enumerate(samples, 1):
        print(f"  {i:4d}  {s:.3f}s")
    print(f"Total: {len(samples)} sample(s)")


def cmd_drift_clear(args: argparse.Namespace) -> None:
    tracker = DriftTracker(path=_resolve_path(args))
    tracker.clear()
    print("Drift history cleared.")


def build_drift_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("drift", help="drift detection commands")
    sub = p.add_subparsers(dest="drift_cmd", required=True)

    def _common(sp: argparse.ArgumentParser) -> None:
        sp.add_argument("--file", default=".pipewatch/drift.json", help="state file")

    chk = sub.add_parser("check", help="record a duration and check for drift")
    _common(chk)
    chk.add_argument("duration", type=float, help="elapsed seconds for this run")
    chk.add_argument("--window", type=int, default=10, help="baseline window size")
    chk.add_argument("--threshold", type=float, default=2.0, help="z-score threshold")
    chk.set_defaults(func=cmd_drift_check)

    show = sub.add_parser("show", help="show recorded duration samples")
    _common(show)
    show.set_defaults(func=cmd_drift_show)

    clr = sub.add_parser("clear", help="clear drift history")
    _common(clr)
    clr.set_defaults(func=cmd_drift_clear)
