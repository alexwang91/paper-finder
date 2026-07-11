from datetime import date

from generation.social_writer import build_social_calendar
from models import Paper, PaperAnalysis, RankedPaper


def ranked_21() -> list[RankedPaper]:
    return [RankedPaper(
        rank=rank,
        paper=Paper(title=f"Paper {rank}", url=f"https://example.com/{rank}", source="fixture"),
        analysis=PaperAnalysis(
            title=f"Paper {rank}",
            category="agents_workflow",
            product_idea="A focused workflow copilot",
            why_it_matters="It makes a repeated task cheaper.",
            risks="Needs real-user validation.",
        ),
    ) for rank in range(1, 22)]


def test_uses_required_rank_distribution_and_content_shape() -> None:
    rows = build_social_calendar(
        ranked_21(),
        date(2026, 7, 13),
        ["09:00", "15:00", "21:00"],
        ["08:30", "12:30", "21:30"],
    )

    assert [row.rank for row in rows[:3]] == [1, 8, 15]
    assert [row.rank for row in rows[-3:]] == [7, 14, 21]
    assert len(rows) == 21
    assert len(rows[0].x_post) <= 280
    assert 5 <= len(rows[0].x_thread.split("\n\n")) <= 7
    assert all(label in rows[0].xiaohongshu_body for label in ["适合谁", "可以做成什么产品", "为什么值得关注"])
    assert rows[0].xiaohongshu_title.count("｜") == 2
