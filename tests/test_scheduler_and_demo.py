import json
from datetime import date
from pathlib import Path

import pandas as pd

from scheduler.weekly_job import build_scheduler
from scripts.generate_demo import generate_demo


def test_scheduler_creates_one_monday_job() -> None:
    scheduler = build_scheduler(Path("config.yaml"))

    jobs = scheduler.get_jobs()
    assert len(jobs) == 1
    assert str(jobs[0].trigger.fields[4]) == "mon"
    assert str(jobs[0].trigger.fields[5]) == "7"


def test_demo_generates_four_offline_artifacts(tmp_path) -> None:
    paths = generate_demo(tmp_path, date(2026, 7, 12))

    assert paths.raw_json.exists()
    assert paths.ranking_csv.exists()
    assert paths.report_markdown.exists()
    assert paths.social_csv.exists()
    assert len(pd.read_csv(paths.ranking_csv)) == 21
    assert len(pd.read_csv(paths.social_csv)) == 21
    raw = json.loads(paths.raw_json.read_text(encoding="utf-8"))
    assert len(raw) == 35
    assert not any(item["source"] == "placeholder" for item in raw)
