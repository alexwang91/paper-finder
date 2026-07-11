from models import Paper, PaperAnalysis, RankedPaper
from selection import select_ranked_papers


def candidates(count: int = 30) -> list[RankedPaper]:
    categories = [
        "agents_workflow", "multimodal", "vertical_ai", "robotics",
        "infrastructure", "general_ai", "non_ai_commercial",
    ]
    result: list[RankedPaper] = []
    for index in range(count):
        category = categories[index % len(categories)]
        result.append(RankedPaper(
            paper=Paper(
                title=f"Paper {index:02d}",
                url=f"https://example.com/{index}",
                source="fixture",
                code_url=f"https://github.com/x/{index}" if index % 2 == 0 else None,
            ),
            analysis=PaperAnalysis(
                title=f"Paper {index:02d}",
                category=category,
                total_score=99 - index,
            ),
        ))
    return result


def test_selects_exact_count_and_minimum_ai_ratio() -> None:
    selected = select_ranked_papers(candidates(), final_count=21, min_ai_ratio=0.70)

    assert len(selected) == 21
    assert sum(item.analysis.category != "non_ai_commercial" for item in selected) >= 15
    assert [item.rank for item in selected] == list(range(1, 22))


def test_short_pool_adds_honest_placeholders() -> None:
    selected = select_ranked_papers(candidates(3), final_count=21, min_ai_ratio=0.70)

    assert len(selected) == 21
    assert selected[-1].analysis.confidence == "low"
    assert selected[-1].paper.source == "placeholder"
    assert selected[-1].analysis.total_score == 0
