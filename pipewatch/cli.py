"""Command-line interface for pipewatch.

Provides the `pipewatch` CLI entry point for running and monitoring
long-running pipeline commands with optional Slack and email alerting.
"""

import sys
import click

from pipewatch.config import load_config
from pipewatch.monitor import run_and_monitor


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.argument("command", nargs=-1, required=True)
@click.option(
    "--config",
    "-c",
    "config_path",
    default=None,
    metavar="FILE",
    help="Path to a YAML config file (default: pipewatch.yaml in current directory).",
)
@click.option(
    "--notify-on-success",
    is_flag=True,
    default=False,
    help="Send notifications even when the command succeeds.",
)
@click.option(
    "--notify-on-failure/--no-notify-on-failure",
    default=True,
    show_default=True,
    help="Send notifications when the command fails.",
)
@click.option(
    "--label",
    "-l",
    default=None,
    metavar="TEXT",
    help="Human-readable label for this job (used in notifications).",
)
@click.option(
    "--timeout",
    "-t",
    default=None,
    type=float,
    metavar="SECONDS",
    help="Kill the command after this many seconds (default: no timeout).",
)
@click.version_option(package_name="pipewatch")
def main(
    command: tuple[str, ...],
    config_path: str | None,
    notify_on_success: bool,
    notify_on_failure: bool,
    label: str | None,
    timeout: float | None,
) -> None:
    """Monitor COMMAND and alert via Slack/email on completion or failure.

    COMMAND is the shell command (and its arguments) to run, e.g.:

    \b
        pipewatch python train.py --epochs 50
        pipewatch --notify-on-success bash etl.sh
    """
    try:
        cfg = load_config(config_path)
    except FileNotFoundError as exc:
        raise click.BadParameter(
            str(exc), param_hint="'--config'"
        ) from exc
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(f"Failed to load config: {exc}") from exc

    # Allow CLI --label to override whatever is in the config file.
    if label is not None:
        cfg.label = label

    # Allow CLI --timeout to override config.
    if timeout is not None:
        cfg.timeout = timeout

    result = run_and_monitor(
        list(command),
        config=cfg,
        notify_on_success=notify_on_success,
        notify_on_failure=notify_on_failure,
    )

    # Mirror the subprocess exit code so callers / CI systems see the real status.
    sys.exit(result.returncode)


if __name__ == "__main__":  # pragma: no cover
    main()
