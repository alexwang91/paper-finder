from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from models import Paper


def _item_id(value: Any) -> str:
    if isinstance(value, str):
        return value
    return str(getattr(value, "id", getattr(value, "name", "")))


class HuggingFaceFetcher:
    name = "huggingface"

    def __init__(self, api: Any, max_results: int = 50) -> None:
        self.api = api
        self.max_results = max_results

    def fetch(self, start_date: date, end_date: date, keywords: list[str]) -> list[Paper]:
        papers: list[Paper] = []
        current = end_date
        while current >= start_date and len(papers) < self.max_results:
            remaining = self.max_results - len(papers)
            items = self.api.list_daily_papers(date=current.isoformat(), limit=remaining)
            for item in items:
                arxiv_id = str(getattr(item, "id", getattr(item, "paper_id", "")))
                if not arxiv_id:
                    continue
                authors = [
                    getattr(author, "name", str(author))
                    for author in (getattr(item, "authors", None) or [])
                ]
                papers.append(Paper(
                    paper_id=arxiv_id,
                    title=getattr(item, "title", "Untitled"),
                    abstract=getattr(item, "summary", None) or getattr(item, "ai_summary", None),
                    authors=authors,
                    published_date=current,
                    url=f"https://arxiv.org/abs/{arxiv_id}",
                    pdf_url=f"https://arxiv.org/pdf/{arxiv_id}",
                    source="huggingface",
                    huggingface_url=f"https://huggingface.co/papers/{arxiv_id}",
                    huggingface_upvotes=int(getattr(item, "upvotes", 0) or 0),
                    linked_models=[_item_id(value) for value in (getattr(item, "models", None) or []) if _item_id(value)],
                    linked_datasets=[_item_id(value) for value in (getattr(item, "datasets", None) or []) if _item_id(value)],
                    linked_spaces=[_item_id(value) for value in (getattr(item, "spaces", None) or []) if _item_id(value)],
                ))
                if len(papers) >= self.max_results:
                    break
            current -= timedelta(days=1)
        return papers
