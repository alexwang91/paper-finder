from __future__ import annotations

import argparse
import logging
import os
from pathlib import Path
from typing import Sequence

from huggingface_hub import HfApi
from openai import OpenAI

from config_loader import ConfigError, load_config, resolve_date_range
from pipeline import PipelineError, run_pipeline
from scoring.scorer import HeuristicAnalyzer, LLMAnalyzer
from sources.arxiv_fetcher import ArxivFetcher
from sources.github_fetcher import GitHubFetcher
from sources.huggingface_fetcher import HuggingFaceFetcher
from sources.http import build_session
from sources.paperswithcode_fetcher import PapersWithCodeFetcher
from sources.semantic_scholar_fetcher import SemanticScholarFetcher

LOGGER = logging.getLogger("weekly_paper_radar")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Find and rank commercially promising research papers."
    )
    parser.add_argument("--days-back", type=int)
    parser.add_argument("--week-start")
    parser.add_argument("--week-end")
    parser.add_argument("--final-count", type=int)
    parser.add_argument("--max-candidates", type=int)
    parser.add_argument("--no-llm", action="store_true")
    parser.add_argument("--output-dir", default="outputs")
    parser.add_argument(
        "--config",
        default=str(Path(__file__).with_name("config.yaml")),
    )
    parser.add_argument(
        "--output-format",
        nargs="+",
        choices=("csv", "markdown"),
        default=["csv", "markdown"],
    )
    return parser


def _build_runtime(config, no_llm: bool):
    session = build_session(config.http.user_agent, config.http.retries)
    fetchers = []
    if config.sources.arxiv.enabled:
        fetchers.append(ArxivFetcher(
            session,
            config.arxiv_categories,
            config.sources.arxiv.max_results,
            config.http.timeout_seconds,
        ))
    if config.sources.semantic_scholar.enabled:
        fetchers.append(SemanticScholarFetcher(
            session,
            os.getenv("SEMANTIC_SCHOLAR_API_KEY"),
            config.sources.semantic_scholar.max_results,
            config.http.timeout_seconds,
        ))
    if config.sources.huggingface.enabled:
        fetchers.append(HuggingFaceFetcher(
            HfApi(token=False), config.sources.huggingface.max_results
        ))
    if config.sources.paperswithcode.enabled:
        fetchers.append(PapersWithCodeFetcher(
            session,
            config.sources.paperswithcode.max_results,
            config.http.timeout_seconds,
        ))
    github = None
    if config.sources.github.enabled:
        github = GitHubFetcher(
            session,
            os.getenv("GITHUB_TOKEN"),
            config.sources.github.max_results,
            config.http.timeout_seconds,
        )
    heuristic = HeuristicAnalyzer(config.keywords, config.scoring.weights)
    api_key = os.getenv("OPENAI_API_KEY")
    if no_llm or not api_key:
        if not no_llm and not api_key:
            LOGGER.warning("OPENAI_API_KEY is missing; using heuristic analysis")
        analyzer = heuristic
    else:
        analyzer = LLMAnalyzer(
            OpenAI(api_key=api_key),
            config.llm.model,
            heuristic,
            config.llm.temperature,
            config.llm.max_tokens,
        )
    return fetchers, github, analyzer


def main(argv: Sequence[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    args = build_parser().parse_args(argv)
    try:
        config = load_config(args.config, {
            "days_back": args.days_back,
            "final_count": args.final_count,
            "max_candidates": args.max_candidates,
        })
        start_date, end_date = resolve_date_range(
            config.run.days_back, args.week_start, args.week_end
        )
    except (ConfigError, ValueError) as exc:
        LOGGER.error("Invalid configuration: %s", exc)
        return 2

    fetchers, github, analyzer = _build_runtime(config, args.no_llm)
    try:
        result = run_pipeline(
            config,
            fetchers,
            analyzer,
            args.output_dir,
            start_date,
            end_date,
            github_enricher=github,
            output_formats=set(args.output_format),
        )
    except PipelineError as exc:
        LOGGER.error("Weekly radar failed: %s", exc)
        return 1
    LOGGER.info(
        "Complete: %d unique candidates, %d selected",
        result.deduplicated_count,
        result.selected_count,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
