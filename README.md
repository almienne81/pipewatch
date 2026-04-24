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

---

## License

MIT © 2024 Your Name