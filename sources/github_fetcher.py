from __future__ import annotations

from datetime import date
from typing import Any

import requests

from deduplication import normalize_title
from models import Paper


class GitHubFetcher:
    name = "github"
    api_url = "https://api.github.com/search/repositories"

    def __init__(
        self,
        session: requests.Session,
        token: str | None,
        max_results: int = 50,
        timeout: int = 20,
    ) -> None:
        self.session = session
        self.token = token
        self.max_results = max_results
        self.timeout = timeout

    def fetch(self, start_date: date, end_date: date, keywords: list[str]) -> list[Paper]:
        return []

    @staticmethod
    def _relevance(paper: Paper, repository: dict[str, Any]) -> float:
        haystack = normalize_title(
            f"{repository.get('name', '')} {repository.get('description') or ''}"
        )
        title_words = set(normalize_title(paper.title).split())
        haystack_words = set(haystack.split())
        overlap = len(title_words & haystack_words) / max(1, len(title_words))
        if paper.paper_id and paper.paper_id.casefold() in haystack.casefold():
            return 1.0
        return overlap

    def enrich(self, papers: list[Paper]) -> list[Paper]:
        enriched: list[Paper] = []
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        for paper in papers[: self.max_results]:
            if paper.code_url:
                enriched.append(paper.model_copy(deep=True))
                continue
            query_parts = [f'"{paper.title}"']
            if paper.paper_id:
                query_parts.append(paper.paper_id)
            response = self.session.get(
                self.api_url,
                params={"q": " OR ".join(query_parts), "sort": "stars", "order": "desc", "per_page": 5},
                headers=headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
            candidates = response.json().get("items", [])
            relevant = [item for item in candidates if self._relevance(paper, item) >= 0.45]
            selected = max(relevant, key=lambda item: item.get("stargazers_count", 0), default=None)
            copy = paper.model_copy(deep=True)
            if selected:
                copy.code_url = selected.get("html_url")
                copy.github_stars = int(selected.get("stargazers_count") or 0)
                copy.github_language = selected.get("language")
            enriched.append(copy)
        enriched.extend(paper.model_copy(deep=True) for paper in papers[self.max_results :])
        return enriched
