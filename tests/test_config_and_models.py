from pathlib import Path

import pytest

from config_loader import ConfigError, load_config, resolve_date_range
from models import Paper, PaperAnalysis


def test_paper_accepts_missing_optional_metadata() -> None:
    paper = Paper(title="Useful Agent", url="https://example.com/paper", source="fixture")

    assert paper.abstract is None
    assert paper.authors == []
    assert paper.sources == ["fixture"]


def test_analysis_rejects_out_of_range_score() -> None:
    with pytest.raises(ValueError):
        PaperAnalysis(title="x", category="general_ai", technical_novelty_score=101)


def test_cli_overrides_yaml_values(tmp_path: Path) -> None:
    path = tmp_path / "config.yaml"
    path.write_text("run:\n  days_back: 7\n  final_count: 21\n", encoding="utf-8")

    config = load_config(path, {"days_back": 3, "final_count": 9})

    assert config.run.days_back == 3
    assert config.run.final_count == 9


def test_date_range_rejects_reversed_dates() -> None:
    with pytest.raises(ConfigError, match="week-start"):
        resolve_date_range(days_back=7, week_start="2026-07-12", week_end="2026-07-06")


def test_default_candidate_pool_is_larger_than_final_ranking() -> None:
    config = load_config(Path("missing-config.yaml"))

    assert config.run.min_ranked_candidates == 30
    assert config.run.min_ranked_candidates > config.run.final_count
