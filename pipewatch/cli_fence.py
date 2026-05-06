"""cli_fence.py — CLI subcommands for managing execution fences."""
from __future__ import annotations

import argparse
from pathlib import Path

from pipewatch.fence import Fence, FenceError

_DEFAULT_PATH = Path(".pipewatch/fence.json")


def _resolve_path(args: argparse.Namespace) -> Path:
    return Path(getattr(args, "fence_file", None) or _DEFAULT_PATH)


def cmd_fence_create(args: argparse.Namespace) -> None:
    fence = Fence(_resolve_path(args))
    try:
        state = fence.create(args.name, args.jobs)
    except FenceError as exc:
        print(f"error: {exc}")
        raise SystemExit(1)
    print(f"Fence '{state.name}' created, waiting for: {', '.join(state.pending)}")


def cmd_fence_arrive(args: argparse.Namespace) -> None:
    fence = Fence(_resolve_path(args))
    try:
        state = fence.arrive(args.name, args.job)
    except FenceError as exc:
        print(f"error: {exc}")
        raise SystemExit(1)
    if state.is_open:
        print(f"Fence '{state.name}' is now OPEN — all jobs arrived.")
    else:
        print(f"Fence '{state.name}' pending: {', '.join(state.pending)}")


def cmd_fence_status(args: argparse.Namespace) -> None:
    fence = Fence(_resolve_path(args))
    state = fence.get(args.name)
    if state is None:
        print(f"No fence named '{args.name}'.")
        return
    status = "OPEN" if state.is_open else "WAITING"
    print(f"[{status}] {state.name}")
    print(f"  expected : {', '.join(state.expected)}")
    print(f"  arrived  : {', '.join(state.arrived) or '(none)'}")
    print(f"  pending  : {', '.join(state.pending) or '(none)'}")


def cmd_fence_clear(args: argparse.Namespace) -> None:
    fence = Fence(_resolve_path(args))
    fence.clear(args.name)
    print(f"Fence '{args.name}' cleared.")


def build_fence_parser(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = sub.add_parser("fence", help="Manage execution barriers")
    p.add_argument("--fence-file", metavar="PATH", help="Path to fence state file")
    sp = p.add_subparsers(dest="fence_cmd", required=True)

    c = sp.add_parser("create", help="Create a new fence")
    c.add_argument("name", help="Fence name")
    c.add_argument("jobs", nargs="+", help="Expected job names")
    c.set_defaults(func=cmd_fence_create)

    a = sp.add_parser("arrive", help="Mark a job as arrived")
    a.add_argument("name", help="Fence name")
    a.add_argument("job", help="Job name")
    a.set_defaults(func=cmd_fence_arrive)

    s = sp.add_parser("status", help="Show fence status")
    s.add_argument("name", help="Fence name")
    s.set_defaults(func=cmd_fence_status)

    d = sp.add_parser("clear", help="Remove a fence")
    d.add_argument("name", help="Fence name")
    d.set_defaults(func=cmd_fence_clear)
