from models import Paper
from scoring.scorer import HeuristicAnalyzer, LLMAnalyzer, calculate_total_score


WEIGHTS = {
    "technical_novelty": 0.15,
    "commercial_potential": 0.25,
    "solo_founder_feasibility": 0.20,
    "market_need": 0.15,
    "mvp_speed": 0.10,
    "virality": 0.10,
    "moat": 0.05,
}


def test_calculates_requested_weighted_score() -> None:
    scores = {name: 80 for name in WEIGHTS}

    assert calculate_total_score(scores, WEIGHTS) == 80.0


def test_code_and_market_keywords_raise_commercial_score() -> None:
    weak = Paper(title="A theorem", abstract="proof", url="https://x/1", source="fixture")
    strong = Paper(
        title="Document AI workflow agent",
        abstract="Enterprise automation API for legal teams",
        url="https://x/2",
        source="fixture",
        code_url="https://github.com/x/y",
        github_stars=100,
    )
    analyzer = HeuristicAnalyzer(["AI agent", "workflow automation"], WEIGHTS)

    strong_result = analyzer.analyze(strong)
    weak_result = analyzer.analyze(weak)

    assert strong_result.commercial_potential_score > weak_result.commercial_potential_score
    assert strong_result.product_idea
    assert strong_result.total_score > weak_result.total_score


class FailingResponses:
    def parse(self, **kwargs: object) -> object:
        raise RuntimeError("rate limited")


class FailingClient:
    responses = FailingResponses()


def test_llm_failure_falls_back_per_paper() -> None:
    fallback = HeuristicAnalyzer(["agent"], WEIGHTS)
    analyzer = LLMAnalyzer(FailingClient(), "gpt-4o-mini", fallback)
    paper = Paper(title="Useful agent", abstract="Workflow automation", url="https://x/3", source="fixture")

    result = analyzer.analyze(paper)

    assert result.llm_analysis_status == "failed_fallback"
    assert result.total_score > 0
