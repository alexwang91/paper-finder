from __future__ import annotations

import re
from datetime import date, datetime

import feedparser
import requests

from models import Paper


def _date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    except ValueError:
        return None


def _canonical_arxiv_url(value: str, kind: str = "abs") -> str:
    identifier = value.rstrip("/").split("/")[-1].removesuffix(".pdf")
    identifier = re.sub(r"v\d+$", "", identifier)
    return f"https://arxiv.org/{kind}/{identifier}"


class ArxivFetcher:
    name = "arxiv"
    api_url = "https://export.arxiv.org/api/query"

    def __init__(
        self,
        session: requests.Session,
        categories: list[str],
        max_results: int = 100,
        timeout: int = 20,
    ) -> None:
        self.session = session
        self.categories = categories
        self.max_results = max_results
        self.timeout = timeout

    @staticmethod
    def parse_feed(content: bytes | str) -> list[Paper]:
        feed = feedparser.parse(content)
        papers: list[Paper] = []
        for entry in feed.entries:
            url = _canonical_arxiv_url(entry.get("id", ""))
            pdf_url = None
            for link in entry.get("links", []):
                if link.get("type") == "application/pdf" or link.get("title") == "pdf":
                    pdf_url = _canonical_arxiv_url(link.get("href", ""), "pdf")
                    break
            authors = [author.get("name", "").strip() for author in entry.get("authors", [])]
            categories = [tag.get("term", "") for tag in entry.get("tags", [])]
            papers.append(Paper(
                paper_id=url.rsplit("/", 1)[-1],
                title=" ".join(entry.get("title", "Untitled").split()),
                abstract=" ".join(entry.get("summary", "").split()) or None,
                authors=[name for name in authors if name],
                published_date=_date(entry.get("published")),
                updated_date=_date(entry.get("updated")),
                url=url,
                pdf_url=pdf_url,
                categories=[category for category in categories if category],
                source="arxiv",
            ))
        return papers

    def fetch(self, start_date: date, end_date: date, keywords: list[str]) -> list[Paper]:
        category_query = " OR ".join(f"cat:{category}" for category in self.categories)
        date_query = f"submittedDate:[{start_date:%Y%m%d}0000 TO {end_date:%Y%m%d}2359]"
        params = {
            "search_query": f"({category_query}) AND {date_query}",
            "start": 0,
            "max_results": self.max_results,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }
        response = self.session.get(self.api_url, params=params, timeout=self.timeout)
        response.raise_for_status()
        papers = self.parse_feed(response.content)
        lowered = [keyword.casefold() for keyword in keywords]
        if not lowered:
            return papers
        return [
            paper for paper in papers
            if any(keyword in f"{paper.title} {paper.abstract or ''}".casefold() for keyword in lowered)
        ]
