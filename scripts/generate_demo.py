from __future__ import annotations

import argparse
import json
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config_loader import load_config
from models import OutputPaths, Paper
from pipeline import run_pipeline
from scoring.scorer import HeuristicAnalyzer


class DemoFetcher:
    name = "demo_fixture"

    def __init__(self, path: Path) -> None:
        self.path = path

    def fetch(self, start_date: date, end_date: date, keywords: list[str]) -> list[Paper]:
        records = json.loads(self.path.read_text(encoding="utf-8"))
        return [Paper.model_validate(record) for record in records]


def generate_demo(output_dir: str | Path, report_date: date | None = None) -> OutputPaths:
    report_date = report_date or date.today()
    config = load_config(ROOT / "config.yaml")
    analyzer = HeuristicAnalyzer(config.keywords, config.scoring.weights)
    result = run_pipeline(
        config,
        [DemoFetcher(ROOT / "examples" / "demo_candidates.json")],
        analyzer,
        output_dir,
        report_date - timedelta(days=6),
        report_date,
        show_progress=False,
    )
    return result.output_paths


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate deterministic offline demo outputs.")
    parser.add_argument("--output-dir", default=str(ROOT / "outputs"))
    parser.add_argument("--report-date", type=date.fromisoformat)
    args = parser.parse_args()
    paths = generate_demo(args.output_dir, args.report_date)
    for path in paths.model_dump().values():
        if path:
            print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
