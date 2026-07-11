from __future__ import annotations

import logging
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Iterable

from tqdm import tqdm

from config_loader import AppConfig
from deduplication import deduplicate_papers
from generation.social_writer import build_social_calendar
from models import Paper, PipelineResult, RankedPaper
from reporting import write_outputs, write_raw_candidates
from selection import select_ranked_papers

LOGGER = logging.getLogger(__name__)


class PipelineError(RuntimeError):
    pass


def _next_monday(value: date) -> date:
    return value + timedelta(days=(7 - value.weekday()) % 7)


def run_pipeline(
    config: AppConfig,
    fetchers: list[Any],
    analyzer: Any,
    output_dir: str | Path,
    start_date: date,
    end_date: date,
    github_enricher: Any | None = None,
    output_formats: set[str] | None = None,
    show_progress: bool = True,
) -> PipelineResult:
    fetched_by_source: dict[str, int] = {}
    source_errors: dict[str, str] = {}
    candidates: list[Paper] = []
    for fetcher in fetchers:
        try:
            papers = fetcher.fetch(start_date, end_date, config.keywords)
            fetched_by_source[fetcher.name] = len(papers)
            candidates.extend(papers)
            LOGGER.info("Fetched %d papers from %s", len(papers), fetcher.name)
        except Exception as exc:
            source_errors[fetcher.name] = f"{type(exc).__name__}: {exc}"
            LOGGER.warning("Source %s failed: %s", fetcher.name, exc)
    if fetchers and len(source_errors) == len(fetchers):
        raise PipelineError("all enabled sources failed")
    if not candidates:
        raise PipelineError("sources returned no paper candidates")

    deduplicated = deduplicate_papers(
        candidates, similarity_threshold=config.selection.similarity_threshold
    )[: config.run.max_candidates]
    LOGGER.info("Candidates after deduplication: %d", len(deduplicated))
    write_raw_candidates(output_dir, end_date, deduplicated)
    if len(deduplicated) < config.run.min_ranked_candidates:
        raise PipelineError(
            f"at least {config.run.min_ranked_candidates} real candidates are required before ranking; "
            f"got {len(deduplicated)}. Increase days_back or source limits."
        )

    enriched = deduplicated
    if github_enricher is not None:
        try:
            enriched = github_enricher.enrich(deduplicated)
        except Exception as exc:
            source_errors[github_enricher.name] = f"{type(exc).__name__}: {exc}"
            LOGGER.warning("GitHub enrichment failed: %s", exc)

    iterator: Iterable[Paper] = tqdm(enriched, desc="Analyzing papers") if show_progress else enriched
    ranked_candidates = [
        RankedPaper(paper=paper, analysis=analyzer.analyze(paper))
        for paper in iterator
    ]
    selected = select_ranked_papers(
        ranked_candidates,
        final_count=config.run.final_count,
        min_ai_ratio=config.run.min_ai_ratio,
        topic_caps=config.selection.topic_caps,
        min_ranked_candidates=config.run.min_ranked_candidates,
    )
    if config.run.final_count != 21:
        LOGGER.warning("Social calendar requires 21 papers; using the top 21 structural output")
    social_source = selected
    if len(social_source) != 21:
        social_source = select_ranked_papers(
            ranked_candidates, final_count=21, min_ai_ratio=config.run.min_ai_ratio,
            topic_caps=config.selection.topic_caps,
            min_ranked_candidates=config.run.min_ranked_candidates,
        )
    social = build_social_calendar(
        social_source,
        _next_monday(end_date),
        config.social.x_post_times,
        config.social.xiaohongshu_post_times,
    )
    paths = write_outputs(
        output_dir,
        end_date,
        deduplicated,
        selected,
        social,
        output_formats=output_formats,
    )
    LOGGER.info("Analyzed %d papers; selected %d", len(ranked_candidates), len(selected))
    for path in paths.model_dump().values():
        if path:
            LOGGER.info("Wrote %s", path)
    return PipelineResult(
        fetched_by_source=fetched_by_source,
        source_errors=source_errors,
        deduplicated_count=len(deduplicated),
        analyzed_count=len(ranked_candidates),
        selected_count=len(selected),
        output_paths=paths,
    )
