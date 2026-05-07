"""CLI subcommands for run-count tracking."""

from __future__ import annotations

import argparse
from pathlib import Path

from pipewatch.runcount import RunCount


def _resolve_path(args: argparse.Namespace) -> Path:
    return Path(args.file)


def cmd_runcount_list(args: argparse.Namespace) -> None:
    rc = RunCount(_resolve_path(args))
    entries = rc.all()
    if not entries:
        print("No run counts recorded.")
        return
    for e in sorted(entries, key=lambda x: x.job):
        rate = e.success_rate
        rate_str = f"{rate:.1%}" if rate is not None else "n/a"
        print(f"{e.job}: total={e.total} ok={e.successes} fail={e.failures} rate={rate_str}")


def cmd_runcount_show(args: argparse.Namespace) -> None:
    rc = RunCount(_resolve_path(args))
    entry = rc.get(args.job)
    if entry is None:
        print(f"No counts for job '{args.job}'.")
        return
    rate = entry.success_rate
    rate_str = f"{rate:.1%}" if rate is not None else "n/a"
    print(f"job:      {entry.job}")
    print(f"total:    {entry.total}")
    print(f"success:  {entry.successes}")
    print(f"failures: {entry.failures}")
    print(f"rate:     {rate_str}")


def cmd_runcount_record(args: argparse.Namespace) -> None:
    rc = RunCount(_resolve_path(args))
    entry = rc.record(args.job, success=not args.fail)
    status = "failure" if args.fail else "success"
    print(f"Recorded {status} for '{args.job}'. Total runs: {entry.total}.")


def cmd_runcount_reset(args: argparse.Namespace) -> None:
    rc = RunCount(_resolve_path(args))
    rc.reset(args.job)
    print(f"Reset counts for '{args.job}'.")


def build_runcount_parser(sub: argparse._SubParsersAction) -> argparse.ArgumentParser:
    p = sub.add_parser("runcount", help="track cumulative run counts per job")
    p.add_argument("--file", default="runcount.json", help="state file path")
    sp = p.add_subparsers(dest="runcount_cmd", required=True)

    sp.add_parser("list", help="list all job counts").set_defaults(func=cmd_runcount_list)

    show = sp.add_parser("show", help="show counts for a specific job")
    show.add_argument("job")
    show.set_defaults(func=cmd_runcount_show)

    record = sp.add_parser("record", help="record a run outcome")
    record.add_argument("job")
    record.add_argument("--fail", action="store_true", help="record as failure")
    record.set_defaults(func=cmd_runcount_record)

    reset = sp.add_parser("reset", help="reset counts for a job")
    reset.add_argument("job")
    reset.set_defaults(func=cmd_runcount_reset)

    return p
