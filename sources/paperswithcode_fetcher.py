from __future__ import annotations

from datetime import date
from typing import Any

import requests
from bs4 import BeautifulSoup

from models import Paper
from sources.base import SourceUnavailable


class PapersWithCodeFetcher:
    name = "paperswithcode"
    api_url = "https://paperswithcode.com/api/v1/papers/"
    html_url = "https://paperswithcode.com/"

    def __init__(self, session: requests.Session, max_results: int = 50, timeout: int = 20) -> None:
        self.session = session
        self.max_results = max_results
        self.timeout = timeout

    @staticmethod
    def parse_payload(payload: dict[str, Any]) -> list[Paper]:
        papers: list[Paper] = []
        for item in payload.get("results", []):
            repository = item.get("repository") or {}
            tasks = item.get("tasks") or []
            datasets = item.get("datasets") or []
            published = None
            if item.get("published"):
                try:
                    published = date.fromisoformat(item["published"][:10])
                except ValueError:
                    published = None
            url = item.get("url_abs") or item.get("url")
            if not url:
                continue
            papers.append(Paper(
                paper_id=item.get("id"),
                title=item.get("title") or "Untitled",
                abstract=item.get("abstract"),
                authors=[author.get("name", "") for author in item.get("authors") or [] if author.get("name")],
                published_date=published,
                url=url,
                pdf_url=item.get("url_pdf"),
                source="paperswithcode",
                code_url=repository.get("url") or item.get("code_url"),
                github_stars=int(repository.get("stars") or item.get("stars") or 0),
                task=tasks[0].get("name") if tasks and isinstance(tasks[0], dict) else (str(tasks[0]) if tasks else None),
                dataset=datasets[0].get("name") if datasets and isinstance(datasets[0], dict) else (str(datasets[0]) if datasets else None),
            ))
        return papers

    @staticmethod
    def parse_html(html: str) -> list[Paper]:
        soup = BeautifulSoup(html, "html.parser")
        papers: list[Paper] = []
        for card in soup.select(".paper-card"):
            title_link = card.select_one("h1 a, h2 a, .paper-title a")
            if not title_link:
                continue
            href = title_link.get("href", "")
            url = href if href.startswith("http") else f"https://paperswithcode.com{href}"
            abstract_node = card.select_one(".item-strip-abstract, .paper-abstract")
            code_node = card.select_one("a.code-table-link, a[href*='github.com']")
            papers.append(Paper(
                title=title_link.get_text(" ", strip=True),
                abstract=abstract_node.get_text(" ", strip=True) if abstract_node else None,
                url=url,
                source="paperswithcode",
                code_url=code_node.get("href") if code_node else None,
            ))
        return papers

    def fetch(self, start_date: date, end_date: date, keywords: list[str]) -> list[Paper]:
        try:
            response = self.session.get(
                self.api_url,
                params={"page_size": self.max_results, "ordering": "-published"},
                timeout=self.timeout,
            )
            response.raise_for_status()
            papers = self.parse_payload(response.json())
            if papers:
                return [paper for paper in papers if not paper.published_date or start_date <= paper.published_date <= end_date]
        except (requests.RequestException, ValueError, AttributeError):
            pass
        try:
            response = self.session.get(self.html_url, timeout=self.timeout)
            response.raise_for_status()
            papers = self.parse_html(response.text)
            if papers:
                return papers[: self.max_results]
        except (requests.RequestException, AttributeError):
            pass
        raise SourceUnavailable("Papers with Code API and HTML fallback were unavailable")
