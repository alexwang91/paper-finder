from __future__ import annotations

import json
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd

from models import OutputPaths, Paper, RankedPaper, SocialCalendarEntry

RANKING_COLUMNS = [
    "rank", "title", "url", "pdf_url", "source", "published_date", "authors",
    "institutions", "category", "abstract_summary_cn", "abstract_summary_en",
    "key_innovation", "why_it_matters", "business_insight", "product_idea",
    "skill_or_agent_idea", "target_users", "monetization", "mvp_complexity",
    "technical_novelty_score", "commercial_potential_score",
    "solo_founder_feasibility_score", "market_need_score", "mvp_speed_score",
    "virality_score", "moat_score", "total_score", "why_selected", "risks",
    "recommended_next_step", "code_url", "github_stars", "huggingface_url",
    "demo_url", "llm_analysis_status", "confidence",
]

SOCIAL_COLUMNS = [
    "date", "weekday", "rank", "paper_title", "paper_url", "x_post_time",
    "x_post", "x_thread", "x_hashtags", "xiaohongshu_post_time",
    "xiaohongshu_title", "xiaohongshu_body", "xiaohongshu_tags", "image_prompt",
]


def _joined(values: list[str]) -> str:
    return "; ".join(values)


def _ranking_record(item: RankedPaper) -> dict[str, Any]:
    paper, analysis = item.paper, item.analysis
    return {
        "rank": item.rank,
        "title": paper.title,
        "url": paper.url,
        "pdf_url": paper.pdf_url or "",
        "source": _joined(paper.sources),
        "published_date": paper.published_date.isoformat() if paper.published_date else "",
        "authors": _joined(paper.authors),
        "institutions": _joined(paper.institutions),
        "category": analysis.category,
        "abstract_summary_cn": analysis.abstract_summary_cn,
        "abstract_summary_en": analysis.abstract_summary_en,
        "key_innovation": analysis.key_innovation,
        "why_it_matters": analysis.why_it_matters,
        "business_insight": analysis.business_insight,
        "product_idea": analysis.product_idea,
        "skill_or_agent_idea": analysis.skill_or_agent_idea,
        "target_users": _joined(analysis.target_users),
        "monetization": analysis.monetization,
        "mvp_complexity": analysis.mvp_complexity,
        "technical_novelty_score": analysis.technical_novelty_score,
        "commercial_potential_score": analysis.commercial_potential_score,
        "solo_founder_feasibility_score": analysis.solo_founder_feasibility_score,
        "market_need_score": analysis.market_need_score,
        "mvp_speed_score": analysis.mvp_speed_score,
        "virality_score": analysis.virality_score,
        "moat_score": analysis.moat_score,
        "total_score": analysis.total_score,
        "why_selected": analysis.why_selected,
        "risks": analysis.risks,
        "recommended_next_step": analysis.recommended_next_step,
        "code_url": paper.code_url or "",
        "github_stars": paper.github_stars,
        "huggingface_url": paper.huggingface_url or "",
        "demo_url": paper.demo_url or "",
        "llm_analysis_status": analysis.llm_analysis_status,
        "confidence": analysis.confidence,
    }


def _atomic_text(path: Path, content: str, encoding: str = "utf-8") -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(content, encoding=encoding)
    temporary.replace(path)


def _atomic_csv(path: Path, records: list[dict[str, Any]], columns: list[str]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    pd.DataFrame(records, columns=columns).to_csv(temporary, index=False, encoding="utf-8-sig")
    temporary.replace(path)


def _table_text(value: object) -> str:
    return str(value or "").replace("|", "\\|").replace("\n", " ")


def build_markdown_report(report_date: date, ranked: list[RankedPaper]) -> str:
    categories = Counter(item.analysis.category for item in ranked if item.paper.source != "placeholder")
    trend_text = ", ".join(f"{name}: {count}" for name, count in categories.most_common()) or "No qualified trends"
    lines = [
        f"# Weekly Paper Commercial Radar — {report_date.isoformat()}",
        "",
        "## 1. Executive Summary",
        "",
        f"This week's selected portfolio is led by {trend_text}.",
        "Commercial priority is given to narrow workflow products, reusable AI skills, and fast customer validation.",
        "The strongest solo-founder opportunities combine accessible code, a specific buyer, and an MVP that can be tested in weeks.",
        "",
        "## 2. Top 21 Ranking",
        "",
        "| Rank | Title | Category | Total Score | Product Idea | Solo Founder Fit | Link |",
        "| ---: | --- | --- | ---: | --- | ---: | --- |",
    ]
    for item in ranked:
        a, p = item.analysis, item.paper
        lines.append(
            f"| {item.rank} | {_table_text(p.title)} | {a.category} | {a.total_score:.2f} | "
            f"{_table_text(a.product_idea)} | {a.solo_founder_feasibility_score:.0f} | [Paper]({p.url}) |"
        )
    lines.extend(["", "## 3. Detailed Analysis", ""])
    for item in ranked:
        p, a = item.paper, item.analysis
        lines.extend([
            f"### {item.rank}. {p.title}",
            "",
            f"- **Link:** {p.url}",
            f"- **One-sentence summary:** {a.abstract_summary_en}",
            f"- **Core technical idea:** {a.key_innovation}",
            f"- **Why it matters:** {a.why_it_matters}",
            f"- **Commercial opportunity:** {a.business_insight}",
            f"- **Possible AI Skill / Agent:** {a.skill_or_agent_idea}",
            f"- **Target customers:** {_joined(a.target_users)}",
            f"- **MVP suggestion:** {a.product_idea}",
            f"- **Monetization:** {a.monetization}",
            f"- **Risk:** {a.risks}",
            f"- **Final score:** {a.total_score:.2f}/100 ({a.confidence} confidence)",
            "",
        ])
    lines.extend(["## 4. Top 5 Solo Founder Opportunities", ""])
    top_five = sorted(
        [item for item in ranked if item.paper.source != "placeholder"],
        key=lambda item: (item.analysis.solo_founder_feasibility_score, item.analysis.total_score),
        reverse=True,
    )[:5]
    for index, item in enumerate(top_five, start=1):
        a = item.analysis
        lines.extend([
            f"### {index}. {item.paper.title}",
            "",
            f"- **Why suitable:** {a.why_selected or a.why_it_matters}",
            f"- **MVP:** {a.product_idea}",
            "- **First users:** Recruit five niche users through specialist communities and direct outreach.",
            f"- **Pricing:** {a.monetization or 'Start with a paid pilot, then a monthly plan.'}",
            "- **30-day plan:** Week 1 interviews; Week 2 working demo; Week 3 paid pilots; Week 4 measure retention and decide whether to deepen the niche.",
            "",
        ])
    lines.extend(["## 5. Content Angles", ""])
    angles = [
        "X: Three papers that can become paid workflow agents",
        "X: Why code availability matters more than academic prestige for founders",
        "Xiaohongshu: 一个人能验证的三个 AI 产品方向",
        "Xiaohongshu: 从论文到小而美 SaaS 的四步法",
        "Newsletter: The commercial research patterns behind this week's Top 21",
        "Newsletter: Five MVPs worth testing before training a model",
        "YouTube Shorts: One research demo, one customer pain, one product",
        "TikTok: Can this paper become a business in 30 days?",
        "Cross-platform: The hidden distribution advantage of research-led products",
        "Cross-platform: Seven questions to score a paper like a founder",
    ]
    lines.extend(f"{index}. {angle}" for index, angle in enumerate(angles, start=1))
    return "\n".join(lines) + "\n"


def write_outputs(
    output_dir: str | Path,
    report_date: date,
    raw_candidates: list[Paper],
    ranked: list[RankedPaper],
    social: list[SocialCalendarEntry],
    output_formats: set[str] | None = None,
) -> OutputPaths:
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    stamp = report_date.isoformat()
    raw_path = write_raw_candidates(directory, report_date, raw_candidates)
    formats = output_formats or {"csv", "markdown"}
    ranking_path = directory / f"weekly_paper_rank_{stamp}.csv" if "csv" in formats else None
    social_path = directory / f"social_calendar_{stamp}.csv" if "csv" in formats else None
    report_path = directory / f"weekly_report_{stamp}.md" if "markdown" in formats else None
    if ranking_path and social_path:
        _atomic_csv(ranking_path, [_ranking_record(item) for item in ranked], RANKING_COLUMNS)
        _atomic_csv(social_path, [item.model_dump(mode="json") for item in social], SOCIAL_COLUMNS)
    if report_path:
        _atomic_text(report_path, build_markdown_report(report_date, ranked))
    return OutputPaths(
        raw_json=raw_path,
        ranking_csv=ranking_path,
        report_markdown=report_path,
        social_csv=social_path,
    )


def write_raw_candidates(output_dir: str | Path, report_date: date, papers: list[Paper]) -> Path:
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    raw_path = directory / f"raw_candidates_{report_date.isoformat()}.json"
    raw_json = json.dumps([paper.model_dump(mode="json") for paper in papers], ensure_ascii=False, indent=2)
    _atomic_text(raw_path, raw_json)
    return raw_path
