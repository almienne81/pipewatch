"""CLI sub-commands for trendline analysis."""
from __future__ import annotations

import argparse
import json

from pipewatch.history import History
from pipewatch.trendline import TrendlinePolicy, TrendlineError, compute_trend


def _resolve_path(args: argparse.Namespace) -> str:
    return getattr(args, "history_file", "pipewatch_history.json")


def cmd_trendline_check(args: argparse.Namespace) -> None:
    path = _resolve_path(args)
    history = History(path)
    entries = history.all()

    try:
        policy = TrendlinePolicy(
            min_samples=args.min_samples,
            slope_warn_threshold=args.warn,
            slope_fail_threshold=args.fail,
        )
    except TrendlineError as exc:
        print(f"[trendline] policy error: {exc}")
        raise SystemExit(1)

    durations = [
        e.duration_seconds
        for e in entries
        if e.duration_seconds is not None
    ]

    result = compute_trend(durations, policy)

    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
        return

    symbol = {"ok": "✓", "warn": "!", "fail": "✗", "insufficient_data": "?"}[result.status]
    print(f"[{symbol}] trend status : {result.status}")
    print(f"    samples   : {result.n}")
    print(f"    slope     : {result.slope:+.4f} s/run")
    print(f"    intercept : {result.intercept:.4f} s")

    if result.status == "fail":
        raise SystemExit(2)
    if result.status == "warn":
        raise SystemExit(1)


def build_trendline_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("trendline", help="Analyse duration trend over history")
    sub = p.add_subparsers(dest="trendline_cmd", required=True)

    chk = sub.add_parser("check", help="Compute and classify the duration trend")
    chk.add_argument("--history-file", default="pipewatch_history.json")
    chk.add_argument("--min-samples", type=int, default=5)
    chk.add_argument("--warn", type=float, default=0.1,
                     help="Slope (s/run) that triggers a warning")
    chk.add_argument("--fail", type=float, default=0.5,
                     help="Slope (s/run) that triggers a failure")
    chk.add_argument("--json", action="store_true", help="Output as JSON")
    chk.set_defaults(func=cmd_trendline_check)
