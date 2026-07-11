from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, field_validator

Category = Literal[
    "agents_workflow",
    "multimodal",
    "vertical_ai",
    "robotics",
    "infrastructure",
    "non_ai_commercial",
    "general_ai",
]


class Paper(BaseModel):
    paper_id: str | None = None
    title: str
    abstract: str | None = None
    authors: list[str] = Field(default_factory=list)
    institutions: list[str] = Field(default_factory=list)
    published_date: date | None = None
    updated_date: date | None = None
    url: str
    pdf_url: str | None = None
    categories: list[str] = Field(default_factory=list)
    source: str
    sources: list[str] = Field(default_factory=list)
    venue: str | None = None
    year: int | None = None
    citation_count: int = 0
    influential_citation_count: int = 0
    huggingface_url: str | None = None
    huggingface_upvotes: int = 0
    linked_models: list[str] = Field(default_factory=list)
    linked_datasets: list[str] = Field(default_factory=list)
    linked_spaces: list[str] = Field(default_factory=list)
    code_url: str | None = None
    github_stars: int = 0
    github_language: str | None = None
    demo_url: str | None = None
    task: str | None = None
    dataset: str | None = None

    def model_post_init(self, __context: object) -> None:
        if not self.sources:
            self.sources = [self.source]


class PaperAnalysis(BaseModel):
    title: str
    category: Category = "general_ai"
    abstract_summary_cn: str = ""
    abstract_summary_en: str = ""
    key_innovation: str = ""
    why_it_matters: str = ""
    business_insight: str = ""
    product_idea: str = ""
    skill_or_agent_idea: str = ""
    target_users: list[str] = Field(default_factory=list)
    monetization: str = ""
    mvp_complexity: Literal["low", "medium", "high"] = "medium"
    solo_founder_feasibility_score: float = 0
    technical_novelty_score: float = 0
    commercial_potential_score: float = 0
    market_need_score: float = 0
    mvp_speed_score: float = 0
    virality_score: float = 0
    moat_score: float = 0
    total_score: float = 0
    why_selected: str = ""
    risks: str = ""
    recommended_next_step: str = ""
    llm_analysis_status: Literal[
        "completed", "failed_fallback", "failed_or_skipped"
    ] = "failed_or_skipped"
    confidence: Literal["high", "medium", "low"] = "medium"

    @field_validator(
        "solo_founder_feasibility_score",
        "technical_novelty_score",
        "commercial_potential_score",
        "market_need_score",
        "mvp_speed_score",
        "virality_score",
        "moat_score",
        "total_score",
    )
    @classmethod
    def score_in_range(cls, value: float) -> float:
        if not 0 <= value <= 100:
            raise ValueError("score must be between 0 and 100")
        return value


class RankedPaper(BaseModel):
    rank: int = 0
    paper: Paper
    analysis: PaperAnalysis


class SocialCalendarEntry(BaseModel):
    date: date
    weekday: str
    rank: int
    paper_title: str
    paper_url: str
    x_post_time: str
    x_post: str
    x_thread: str
    x_hashtags: str
    xiaohongshu_post_time: str
    xiaohongshu_title: str
    xiaohongshu_body: str
    xiaohongshu_tags: str
    image_prompt: str


class OutputPaths(BaseModel):
    raw_json: Path
    ranking_csv: Path | None = None
    report_markdown: Path | None = None
    social_csv: Path | None = None


class PipelineResult(BaseModel):
    fetched_by_source: dict[str, int]
    source_errors: dict[str, str]
    deduplicated_count: int
    analyzed_count: int
    selected_count: int
    output_paths: OutputPaths
