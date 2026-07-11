from __future__ import annotations

import math
from datetime import date

from models import Paper, PaperAnalysis, RankedPaper

DEFAULT_TOPIC_CAPS = {
    "agents_workflow": 7,
    "multimodal": 5,
    "vertical_ai": 4,
    "robotics": 3,
    "infrastructure": 3,
    "non_ai_commercial": 3,
    "general_ai": 5,
}


def _sort_key(item: RankedPaper) -> tuple[float, int, int, str]:
    published = item.paper.published_date or date.min
    return (
        item.analysis.total_score,
        1 if item.paper.code_url else 0,
        published.toordinal(),
        item.paper.title.casefold(),
    )


def _placeholder(number: int) -> RankedPaper:
    title = f"Insufficient qualified candidate #{number}"
    return RankedPaper(
        paper=Paper(
            title=title,
            url=f"about:blank#insufficient-{number}",
            source="placeholder",
        ),
        analysis=PaperAnalysis(
            title=title,
            category="general_ai",
            abstract_summary_cn="上游来源返回的唯一有效论文不足，本条仅用于保持排期结构完整。",
            abstract_summary_en="Upstream sources returned too few unique papers; this row preserves the output structure.",
            why_selected="Structural placeholder; not a real paper.",
            risks="Do not publish or treat this row as research.",
            recommended_next_step="Enable more sources or widen the date range.",
            total_score=0,
            confidence="low",
            llm_analysis_status="failed_or_skipped",
        ),
    )


def select_ranked_papers(
    candidates: list[RankedPaper],
    final_count: int = 21,
    min_ai_ratio: float = 0.70,
    topic_caps: dict[str, int] | None = None,
) -> list[RankedPaper]:
    caps = topic_caps or DEFAULT_TOPIC_CAPS
    ordered = sorted(candidates, key=_sort_key, reverse=True)
    selected: list[RankedPaper] = []
    selected_ids: set[int] = set()
    counts: dict[str, int] = {}
    for item in ordered:
        category = item.analysis.category
        if counts.get(category, 0) >= caps.get(category, final_count):
            continue
        selected.append(item.model_copy(deep=True))
        selected_ids.add(id(item))
        counts[category] = counts.get(category, 0) + 1
        if len(selected) == final_count:
            break
    if len(selected) < final_count:
        for item in ordered:
            if id(item) in selected_ids:
                continue
            selected.append(item.model_copy(deep=True))
            selected_ids.add(id(item))
            if len(selected) == final_count:
                break

    minimum_ai = math.ceil(final_count * min_ai_ratio)
    ai_count = sum(item.analysis.category != "non_ai_commercial" for item in selected)
    remaining_ai = [
        item for item in ordered
        if id(item) not in selected_ids and item.analysis.category != "non_ai_commercial"
    ]
    while ai_count < minimum_ai and remaining_ai:
        replace_index = next(
            (index for index in range(len(selected) - 1, -1, -1)
             if selected[index].analysis.category == "non_ai_commercial"),
            None,
        )
        if replace_index is None:
            break
        selected[replace_index] = remaining_ai.pop(0).model_copy(deep=True)
        ai_count += 1

    selected.sort(key=_sort_key, reverse=True)
    while len(selected) < final_count:
        selected.append(_placeholder(len(selected) + 1))
    for rank, item in enumerate(selected[:final_count], start=1):
        item.rank = rank
    return selected[:final_count]
