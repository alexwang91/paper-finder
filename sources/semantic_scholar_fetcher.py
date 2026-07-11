from __future__ import annotations

from datetime import date
from typing import Any

import requests

from models import Paper


class SemanticScholarFetcher:
    name = "semantic_scholar"
    api_url = "https://api.semanticscholar.org/graph/v1/paper/search"
    fields = (
        "paperId,title,abstract,authors,venue,year,citationCount,"
        "influentialCitationCount,url,fieldsOfStudy,publicationDate,"
        "openAccessPdf,externalIds"
    )

    def __init__(
        self,
        session: requests.Session,
        api_key: str | None,
        max_results: int = 100,
        timeout: int = 20,
    ) -> None:
        self.session = session
        self.api_key = api_key
        self.max_results = max_results
        self.timeout = timeout

    @staticmethod
    def parse_payload(payload: dict[str, Any]) -> list[Paper]:
        papers: list[Paper] = []
        for item in payload.get("data", []):
            published = None
            if item.get("publicationDate"):
                try:
                    published = date.fromisoformat(item["publicationDate"])
                except ValueError:
                    published = None
            open_pdf = item.get("openAccessPdf") or {}
            papers.append(Paper(
                paper_id=item.get("paperId"),
                title=item.get("title") or "Untitled",
                abstract=item.get("abstract"),
                authors=[author.get("name", "") for author in item.get("authors") or [] if author.get("name")],
                published_date=published,
                url=item.get("url") or f"https://www.semanticscholar.org/paper/{item.get('paperId', '')}",
                pdf_url=open_pdf.get("url"),
                categories=item.get("fieldsOfStudy") or [],
                source="semantic_scholar",
                venue=item.get("venue"),
                year=item.get("year"),
                citation_count=item.get("citationCount") or 0,
                influential_citation_count=item.get("influentialCitationCount") or 0,
            ))
        return papers

    def fetch(self, start_date: date, end_date: date, keywords: list[str]) -> list[Paper]:
        queries = keywords or ["artificial intelligence"]
        seen: set[str] = set()
        papers: list[Paper] = []
        headers = {"x-api-key": self.api_key} if self.api_key else {}
        for query in queries:
            remaining = self.max_results - len(papers)
            if remaining <= 0:
                break
            params = {
                "query": query.replace("-", " "),
                "limit": min(100, remaining),
                "fields": self.fields,
                "publicationDateOrYear": f"{start_date.isoformat()}:{end_date.isoformat()}",
            }
            response = self.session.get(
                self.api_url, params=params, headers=headers, timeout=self.timeout
            )
            response.raise_for_status()
            for paper in self.parse_payload(response.json()):
                key = paper.paper_id or paper.url
                if key not in seen:
                    seen.add(key)
                    papers.append(paper)
        return papers
