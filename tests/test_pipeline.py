import hashlib
from datetime import date

import pytest

from config_loader import AppConfig
from models import Paper
from pipeline import PipelineError, run_pipeline
from scoring.scorer import HeuristicAnalyzer


class SuccessfulFetcher:
    name = "successful"

    def __init__(self, count: int = 35) -> None:
        self.count = count

    def fetch(self, start_date: date, end_date: date, keywords: list[str]) -> list[Paper]:
        return [Paper(
            title=f"Research {hashlib.sha256(str(index).encode()).hexdigest()}",
            abstract="Enterprise workflow automation benchmark",
            url=f"https://example.com/papers/{index}",
            source=self.name,
        ) for index in range(self.count)]


class FailingFetcher:
    name = "failing"

    def fetch(self, start_date: date, end_date: date, keywords: list[str]) -> list[Paper]:
        raise RuntimeError("upstream unavailable")


def test_one_source_failure_does_not_stop_outputs(tmp_path) -> None:
    config = AppConfig()
    analyzer = HeuristicAnalyzer(["agent", "workflow"], config.scoring.weights)

    result = run_pipeline(
        config,
        [FailingFetcher(), SuccessfulFetcher()],
        analyzer,
        tmp_path,
        date(2026, 7, 6),
        date(2026, 7, 12),
        show_progress=False,
    )

    assert "failing" in result.source_errors
    assert result.analyzed_count == 35
    assert result.selected_count == 21
    assert result.output_paths.ranking_csv.exists()
    assert result.output_paths.social_csv.exists()


def test_all_sources_failure_is_a_pipeline_error(tmp_path) -> None:
    config = AppConfig()
    analyzer = HeuristicAnalyzer([], config.scoring.weights)

    with pytest.raises(PipelineError, match="all enabled sources failed"):
        run_pipeline(
            config,
            [FailingFetcher()],
            analyzer,
            tmp_path,
            date(2026, 7, 6),
            date(2026, 7, 12),
            show_progress=False,
        )


def test_pipeline_refuses_to_rank_fewer_than_thirty_real_candidates(tmp_path) -> None:
    config = AppConfig()
    analyzer = HeuristicAnalyzer([], config.scoring.weights)

    with pytest.raises(PipelineError, match="at least 30 real candidates"):
        run_pipeline(
            config,
            [SuccessfulFetcher(count=29)],
            analyzer,
            tmp_path,
            date(2026, 7, 6),
            date(2026, 7, 12),
            show_progress=False,
        )
