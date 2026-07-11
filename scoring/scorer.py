from __future__ import annotations

import math
from typing import Any

from generation.product_idea_generator import product_template
from generation.summarizer import summarize_abstract
from models import Category, Paper, PaperAnalysis
from scoring.prompts import SYSTEM_PROMPT, build_paper_prompt


def calculate_total_score(scores: dict[str, float], weights: dict[str, float]) -> float:
    return round(sum(scores.get(name, 0) * weight for name, weight in weights.items()), 2)


def _clamp(value: float) -> float:
    return round(max(0.0, min(100.0, value)), 2)


def classify_category(paper: Paper) -> Category:
    text = f"{paper.title} {paper.abstract or ''} {' '.join(paper.categories)}".casefold()
    groups: list[tuple[Category, tuple[str, ...]]] = [
        ("agents_workflow", ("agent", "workflow", "rag", "tool use", "automation")),
        ("multimodal", ("multimodal", "vision language", "video", "speech", "diffusion", "image")),
        ("robotics", ("robot", "embodied", "manipulation", "navigation")),
        ("vertical_ai", ("medical", "legal", "finance", "education", "drug", "cybersecurity", "document ai")),
        ("infrastructure", ("inference", "evaluation", "benchmark", "serving", "compiler", "developer")),
    ]
    for category, markers in groups:
        if any(marker in text for marker in markers):
            return category
    ai_markers = (" ai ", "artificial intelligence", "model", "neural", "learning", "llm")
    return "general_ai" if any(marker in f" {text} " for marker in ai_markers) else "non_ai_commercial"


class HeuristicAnalyzer:
    def __init__(self, keywords: list[str], weights: dict[str, float]) -> None:
        self.keywords = [keyword.casefold() for keyword in keywords]
        self.weights = weights

    def analyze(self, paper: Paper) -> PaperAnalysis:
        text = f"{paper.title} {paper.abstract or ''}".casefold()
        keyword_hits = sum(1 for keyword in self.keywords if keyword in text)
        business_hits = sum(1 for marker in (
            "enterprise", "workflow", "automation", "api", "productivity", "legal",
            "medical", "finance", "customer", "document", "security",
        ) if marker in text)
        novelty_hits = sum(1 for marker in ("new", "novel", "benchmark", "dataset", "framework") if marker in text)
        resource_penalty = 25 if any(marker in text for marker in ("billion parameter", "multi-gpu", "large-scale training")) else 0
        code_signal = 1 if paper.code_url else 0
        popularity = min(20.0, math.log10(1 + paper.github_stars + paper.huggingface_upvotes) * 8)
        scores = {
            "technical_novelty": _clamp(45 + novelty_hits * 8 + min(15, paper.citation_count / 4) + code_signal * 5),
            "commercial_potential": _clamp(25 + keyword_hits * 7 + business_hits * 8 + code_signal * 10 + popularity / 2),
            "solo_founder_feasibility": _clamp(58 + code_signal * 15 + business_hits * 2 - resource_penalty),
            "market_need": _clamp(35 + business_hits * 9 + keyword_hits * 3),
            "mvp_speed": _clamp(55 + code_signal * 18 + keyword_hits * 2 - resource_penalty),
            "virality": _clamp(38 + novelty_hits * 7 + popularity + (10 if paper.demo_url else 0)),
            "moat": _clamp(30 + business_hits * 4 + (10 if paper.dataset or paper.linked_datasets else 0)),
        }
        total = calculate_total_score(scores, self.weights)
        category = classify_category(paper)
        summary_cn, summary_en = summarize_abstract(paper)
        product = product_template(paper, category)
        return PaperAnalysis(
            title=paper.title,
            category=category,
            abstract_summary_cn=summary_cn,
            abstract_summary_en=summary_en,
            key_innovation="The paper introduces a product-relevant method, workflow, or evaluation signal.",
            why_it_matters="It may reduce the cost or complexity of a repeatable user task.",
            business_insight=str(product["business_insight"]),
            product_idea=str(product["product_idea"]),
            skill_or_agent_idea=str(product["skill_or_agent_idea"]),
            target_users=list(product["target_users"]),
            monetization=str(product["monetization"]),
            mvp_complexity="low" if scores["mvp_speed"] >= 75 else ("medium" if scores["mvp_speed"] >= 50 else "high"),
            technical_novelty_score=scores["technical_novelty"],
            commercial_potential_score=scores["commercial_potential"],
            solo_founder_feasibility_score=scores["solo_founder_feasibility"],
            market_need_score=scores["market_need"],
            mvp_speed_score=scores["mvp_speed"],
            virality_score=scores["virality"],
            moat_score=scores["moat"],
            total_score=total,
            why_selected="Selected by deterministic commercial and feasibility signals.",
            risks=str(product["risks"]),
            recommended_next_step=str(product["recommended_next_step"]),
            llm_analysis_status="failed_or_skipped",
            confidence="high" if total >= 75 else ("medium" if total >= 50 else "low"),
        )


class LLMAnalyzer:
    def __init__(
        self,
        client: Any,
        model: str,
        fallback: HeuristicAnalyzer,
        temperature: float = 0.2,
        max_tokens: int = 3000,
    ) -> None:
        self.client = client
        self.model = model
        self.fallback = fallback
        self.temperature = temperature
        self.max_tokens = max_tokens

    def analyze(self, paper: Paper) -> PaperAnalysis:
        last_error: Exception | None = None
        for _attempt in range(2):
            try:
                response = self.client.responses.parse(
                    model=self.model,
                    input=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": build_paper_prompt(paper)},
                    ],
                    text_format=PaperAnalysis,
                    temperature=self.temperature,
                    max_output_tokens=self.max_tokens,
                )
                analysis = response.output_parsed
                if not isinstance(analysis, PaperAnalysis):
                    raise ValueError("OpenAI response did not contain parsed analysis")
                scores = {
                    "technical_novelty": analysis.technical_novelty_score,
                    "commercial_potential": analysis.commercial_potential_score,
                    "solo_founder_feasibility": analysis.solo_founder_feasibility_score,
                    "market_need": analysis.market_need_score,
                    "mvp_speed": analysis.mvp_speed_score,
                    "virality": analysis.virality_score,
                    "moat": analysis.moat_score,
                }
                analysis.title = paper.title
                analysis.total_score = calculate_total_score(scores, self.fallback.weights)
                analysis.llm_analysis_status = "completed"
                analysis.confidence = "high" if analysis.total_score >= 75 else (
                    "medium" if analysis.total_score >= 50 else "low"
                )
                return analysis
            except Exception as exc:
                last_error = exc
        fallback = self.fallback.analyze(paper)
        fallback.llm_analysis_status = "failed_fallback"
        if last_error:
            fallback.risks = f"LLM analysis failed; heuristic fallback used. {fallback.risks}"
        return fallback
