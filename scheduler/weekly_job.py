from __future__ import annotations

from pathlib import Path

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from config_loader import load_config
from main import main


def _run_weekly(config_path: str) -> None:
    exit_code = main(["--config", config_path, "--days-back", "7"])
    if exit_code:
        raise RuntimeError(f"weekly radar exited with code {exit_code}")


def build_scheduler(config_path: Path) -> BlockingScheduler:
    config = load_config(config_path)
    scheduler = BlockingScheduler(timezone=config.social.timezone)
    scheduler.add_job(
        _run_weekly,
        CronTrigger(
            day_of_week="mon",
            hour=7,
            minute=0,
            timezone=config.social.timezone,
        ),
        args=[str(config_path)],
        id="weekly-paper-commercial-radar",
        replace_existing=True,
    )
    return scheduler


if __name__ == "__main__":
    build_scheduler(Path("config.yaml")).start()

