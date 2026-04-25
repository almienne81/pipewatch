# pipewatch

A lightweight CLI monitor for long-running data pipeline jobs with Slack and email alerting.

---

## Installation

```bash
pip install pipewatch
```

Or install from source:

```bash
git clone https://github.com/yourname/pipewatch.git && cd pipewatch && pip install .
```

---

## Usage

Wrap any pipeline command with `pipewatch` to monitor its execution and receive alerts on completion or failure:

```bash
pipewatch --name "nightly-etl" --timeout 3600 --slack "#data-alerts" -- python run_pipeline.py
```

**With email alerting:**

```bash
pipewatch --name "daily-sync" --email ops@example.com -- ./sync_job.sh
```

**Configuration via `.pipewatch.yml`:**

```yaml
slack_webhook: https://hooks.slack.com/services/xxx/yyy/zzz
email:
  smtp_host: smtp.example.com
  from: alerts@example.com
  to: ops@example.com
default_timeout: 7200
```

Then run:

```bash
pipewatch --config .pipewatch.yml --name "weekly-report" -- python weekly.py
```

### Key Options

| Flag | Description |
|------|-------------|
| `--name` | Human-readable job name for alerts |
| `--timeout` | Max allowed runtime in seconds |
| `--slack` | Slack channel to notify |
| `--email` | Email address to notify |
| `--config` | Path to YAML config file |
| `--retries` | Number of times to retry on failure (default: 0) |
| `--on-success` | Alert only on success (skip failure alerts) |
| `--on-failure` | Alert only on failure (skip success alerts) |

---

## Exit Codes

`pipewatch` forwards the exit code of the wrapped command. Additionally:

- `0` — Job completed successfully
- `1` — Job failed (non-zero exit from wrapped command)
- `2` — Job timed out
- `3` — Configuration error (missing or invalid `.pipewatch.yml`)

---

## License

MIT © 2024 Your Name
