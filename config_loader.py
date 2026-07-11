from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field, model_validator


class ConfigError(ValueError):
    pass


class RunConfig(BaseModel):
    days_back: int = Field(default=7, ge=1)
    max_candidates: int = Field(default=200, ge=1)
    final_count: int = Field(default=21, ge=1)
    min_ai_ratio: float = Field(default=0.7, ge=0, le=1)


class LlmConfig(BaseModel):
    provider: str = "openai"
    model: str = "gpt-4o-mini"
    temperature: float = Field(default=0.2, ge=0, le=2)
    max_tokens: int = Field(default=3000, ge=1)


class SourceConfig(BaseModel):
    enabled: bool = True
    max_results: int = Field(default=50, ge=1)


class SourcesConfig(BaseModel):
    arxiv: SourceConfig = Field(default_factory=lambda: SourceConfig(max_results=100))
    semantic_scholar: SourceConfig = Field(default_factory=lambda: SourceConfig(max_results=100))
    huggingface: SourceConfig = Field(default_factory=SourceConfig)
    github: SourceConfig = Field(default_factory=SourceConfig)
    paperswithcode: SourceConfig = Field(default_factory=SourceConfig)


class ScoringConfig(BaseModel):
    technical_novelty_weight: float = 0.15
    commercial_potential_weight: float = 0.25
    solo_founder_feasibility_weight: float = 0.20
    market_need_weight: float = 0.15
    mvp_speed_weight: float = 0.10
    virality_weight: float = 0.10
    moat_weight: float = 0.05

    @model_validator(mode="after")
    def weights_sum_to_one(self) -> "ScoringConfig":
        if abs(sum(self.weights.values()) - 1.0) > 1e-6:
            raise ValueError("scoring weights must sum to 1.0")
        return self

    @property
    def weights(self) -> dict[str, float]:
        return {
            "technical_novelty": self.technical_novelty_weight,
            "commercial_potential": self.commercial_potential_weight,
            "solo_founder_feasibility": self.solo_founder_feasibility_weight,
            "market_need": self.market_need_weight,
            "mvp_speed": self.mvp_speed_weight,
            "virality": self.virality_weight,
            "moat": self.moat_weight,
        }


class SocialConfig(BaseModel):
    timezone: str = "Europe/Budapest"
    x_post_times: list[str] = Field(default_factory=lambda: ["09:00", "15:00", "21:00"])
    xiaohongshu_post_times: list[str] = Field(default_factory=lambda: ["08:30", "12:30", "21:30"])
    llm_rewrite: bool = False


class HttpConfig(BaseModel):
    timeout_seconds: int = Field(default=20, ge=1)
    retries: int = Field(default=2, ge=0)
    user_agent: str = "WeeklyPaperCommercialRadar/1.0"


class SelectionConfig(BaseModel):
    similarity_threshold: float = Field(default=0.94, ge=0, le=1)
    topic_caps: dict[str, int] = Field(default_factory=lambda: {
        "agents_workflow": 7,
        "multimodal": 5,
        "vertical_ai": 4,
        "robotics": 3,
        "infrastructure": 3,
        "non_ai_commercial": 3,
        "general_ai": 5,
    })


class AppConfig(BaseModel):
    run: RunConfig = Field(default_factory=RunConfig)
    llm: LlmConfig = Field(default_factory=LlmConfig)
    sources: SourcesConfig = Field(default_factory=SourcesConfig)
    scoring: ScoringConfig = Field(default_factory=ScoringConfig)
    social: SocialConfig = Field(default_factory=SocialConfig)
    http: HttpConfig = Field(default_factory=HttpConfig)
    selection: SelectionConfig = Field(default_factory=SelectionConfig)
    keywords: list[str] = Field(default_factory=list)
    arxiv_categories: list[str] = Field(default_factory=list)


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if value is None:
            continue
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_config(path: str | Path, cli_overrides: dict[str, Any] | None = None) -> AppConfig:
    path = Path(path)
    load_dotenv(path.parent / ".env")
    data: dict[str, Any] = {}
    if path.exists():
        loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if not isinstance(loaded, dict):
            raise ConfigError("config root must be a mapping")
        data = loaded
    overrides = cli_overrides or {}
    run_keys = {"days_back", "max_candidates", "final_count", "min_ai_ratio"}
    run_overrides = {key: value for key, value in overrides.items() if key in run_keys and value is not None}
    nested = {"run": run_overrides} if run_overrides else {}
    return AppConfig.model_validate(_deep_merge(data, nested))


def resolve_date_range(
    days_back: int,
    week_start: str | None = None,
    week_end: str | None = None,
    today: date | None = None,
) -> tuple[date, date]:
    if bool(week_start) != bool(week_end):
        raise ConfigError("week-start and week-end must be provided together")
    if week_start and week_end:
        try:
            start = date.fromisoformat(week_start)
            end = date.fromisoformat(week_end)
        except ValueError as exc:
            raise ConfigError("week-start and week-end must use YYYY-MM-DD") from exc
        if start > end:
            raise ConfigError("week-start must not be after week-end")
        return start, end
    end = today or date.today()
    return end - timedelta(days=days_back - 1), end

