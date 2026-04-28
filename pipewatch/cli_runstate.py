"""CLI subcommands for inspecting pipeline run state."""

from __future__ import annotations

import argparse
from pathlib import Path

from pipewatch.runstate import RunStateStore


def _resolve_path(args: argparse.Namespace) -> Path:
    return Path(getattr(args, "state_file", ".pipewatch/runstate.json"))


def cmd_runstate_show(args: argparse.Namespace) -> None:
    store = RunStateStore(_resolve_path(args))
    state = store.load()
    if state is None:
        print("No run state found.")
        return
    print(f"Job:        {state.job}")
    print(f"PID:        {state.pid}")
    print(f"Started:    {state.started_at.isoformat()}")
    print(f"Status:     {state.status}")
    if state.note:
        print(f"Note:       {state.note}")


def cmd_runstate_status(args: argparse.Namespace) -> None:
    store = RunStateStore(_resolve_path(args))
    if store.is_running():
        state = store.load()
        print(f"RUNNING  pid={state.pid}  job={state.job}")
    else:
        print("NOT RUNNING")


def cmd_runstate_clear(args: argparse.Namespace) -> None:
    store = RunStateStore(_resolve_path(args))
    store.clear()
    print("Run state cleared.")


def build_runstate_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("runstate", help="Inspect pipeline run state")
    p.add_argument("--state-file", default=".pipewatch/runstate.json")
    sub = p.add_subparsers(dest="runstate_cmd")

    sub.add_parser("show", help="Show current run state")
    sub.add_parser("status", help="Check if pipeline is currently running")
    sub.add_parser("clear", help="Clear stored run state")

    p.set_defaults(
        func=lambda args: {
            "show": cmd_runstate_show,
            "status": cmd_runstate_status,
            "clear": cmd_runstate_clear,
        }.get(args.runstate_cmd, cmd_runstate_show)(args)
    )
