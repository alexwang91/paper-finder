import json
from datetime import date

import pandas as pd

from generation.social_writer import build_social_calendar
from models import Paper, PaperAnalysis, RankedPaper
from reporting import RANKING_COLUMNS, write_outputs


def sample_ranked() -> list[RankedPaper]:
    return [RankedPaper(
        rank=rank,
        paper=Paper(
            title=f"Paper {rank}",
            abstract="A useful research result.",
            authors=["Example Author"],
            url=f"https://example.com/{rank}",
            source="fixture",
        ),
        analysis=PaperAnalysis(
            title=f"Paper {rank}",
            category="agents_workflow",
            abstract_summary_cn="中文摘要",
            abstract_summary_en="English summary",
            product_idea="Workflow copilot",
            target_users=["small teams"],
            total_score=80 - rank / 10,
        ),
    ) for rank in range(1, 22)]


def test_writes_requested_artifacts_and_schema(tmp_path) -> None:
    ranked = sample_ranked()
    social = build_social_calendar(
        ranked, date(2026, 7, 13), ["09:00", "15:00", "21:00"], ["08:30", "12:30", "21:30"]
    )

    paths = write_outputs(tmp_path, date(2026, 7, 12), [item.paper for item in ranked], ranked, social)

    assert paths.ranking_csv.name == "weekly_paper_rank_2026-07-12.csv"
    assert paths.report_markdown.name == "weekly_report_2026-07-12.md"
    assert paths.social_csv.name == "social_calendar_2026-07-12.csv"
    assert paths.raw_json.name == "raw_candidates_2026-07-12.json"
    frame = pd.read_csv(paths.ranking_csv)
    assert list(frame.columns) == RANKING_COLUMNS
    assert len(pd.read_csv(paths.social_csv)) == 21
    assert len(json.loads(paths.raw_json.read_text(encoding="utf-8"))) == 21
    report = paths.report_markdown.read_text(encoding="utf-8")
    for heading in ["Executive Summary", "Top 21 Ranking", "Detailed Analysis", "Top 5 Solo Founder Opportunities", "Content Angles"]:
        assert heading in report
