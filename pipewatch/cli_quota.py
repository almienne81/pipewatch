"""CLI sub-commands for quota inspection and management."""
from __future__ import annotations

import argparse
from pathlib import Path

from pipewatch.quota import Quota, QuotaPolicy


def _resolve_path(args: argparse.Namespace) -> Path:
    return Path(args.file)


def cmd_quota_check(args: argparse.Namespace) -> None:
    quota = Quota(_resolve_path(args))
    policy = QuotaPolicy(max_runs=args.max_runs, window_seconds=args.window)
    exceeded = quota.is_exceeded(args.job, policy)
    remaining = quota.remaining(args.job, policy)
    status = "EXCEEDED" if exceeded else "OK"
    print(f"job={args.job} status={status} remaining={remaining}/{policy.max_runs}")


def cmd_quota_record(args: argparse.Namespace) -> None:
    quota = Quota(_resolve_path(args))
    policy = QuotaPolicy(max_runs=args.max_runs, window_seconds=args.window)
    quota.record(args.job, policy)
    remaining = quota.remaining(args.job, policy)
    print(f"Recorded run for '{args.job}'. Remaining: {remaining}/{policy.max_runs}")


def cmd_quota_reset(args: argparse.Namespace) -> None:
    quota = Quota(_resolve_path(args))
    quota.reset(args.job)
    print(f"Quota state cleared for '{args.job}'.")


def _add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--file", default=".pipewatch_quota.json")
    parser.add_argument("--job", required=True)
    parser.add_argument("--max-runs", type=int, default=10)
    parser.add_argument("--window", type=int, default=3600,
                        help="Window size in seconds (default: 3600)")


def build_quota_parser(sub: argparse._SubParsersAction) -> None:
    p_check = sub.add_parser("quota-check", help="Check if quota is exceeded")
    _add_common(p_check)
    p_check.set_defaults(func=cmd_quota_check)

    p_record = sub.add_parser("quota-record", help="Record a run against the quota")
    _add_common(p_record)
    p_record.set_defaults(func=cmd_quota_record)

    p_reset = sub.add_parser("quota-reset", help="Reset quota state for a job")
    p_reset.add_argument("--file", default=".pipewatch_quota.json")
    p_reset.add_argument("--job", required=True)
    p_reset.set_defaults(func=cmd_quota_reset)
