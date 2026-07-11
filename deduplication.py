from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher
from urllib.parse import urlsplit, urlunsplit

from models import Paper

_ARXIV_ID = re.compile(r"arxiv\.org/(?:abs|pdf)/([^/?#]+)", re.IGNORECASE)


def normalize_title(title: str) -> str:
    text = unicodedata.normalize("NFKC", title).casefold()
    text = "".join(char if char.isalnum() else " " for char in text)
    return " ".join(text.split())


def normalize_url(url: str) -> str:
    match = _ARXIV_ID.search(url)
    if match:
        arxiv_id = match.group(1).removesuffix(".pdf")
        return f"arxiv:{arxiv_id}"
    parts = urlsplit(url.strip())
    path = parts.path.rstrip("/") or "/"
    return urlunsplit((parts.scheme.casefold(), parts.netloc.casefold(), path, "", ""))


def title_similarity(left: str, right: str) -> float:
    normalized_left = normalize_title(left)
    normalized_right = normalize_title(right)
    if not normalized_left or not normalized_right:
        return 0.0
    left_words = set(normalized_left.split())
    right_words = set(normalized_right.split())
    shorter = min(len(left_words), len(right_words))
    if shorter >= 2 and (left_words <= right_words or right_words <= left_words):
        return 0.95
    return SequenceMatcher(None, normalized_left, normalized_right).ratio()


def _ordered_union(left: list[str], right: list[str]) -> list[str]:
    return list(dict.fromkeys([*left, *right]))


def _longer(left: str | None, right: str | None) -> str | None:
    candidates = [value for value in (left, right) if value]
    return max(candidates, key=len) if candidates else None


def merge_papers(primary: Paper, incoming: Paper) -> Paper:
    data = primary.model_dump()
    data["title"] = _longer(primary.title, incoming.title) or primary.title
    data["abstract"] = _longer(primary.abstract, incoming.abstract)
    for field in (
        "authors", "institutions", "categories", "sources", "linked_models",
        "linked_datasets", "linked_spaces",
    ):
        data[field] = _ordered_union(getattr(primary, field), getattr(incoming, field))
    data["sources"] = _ordered_union(data["sources"], [incoming.source])
    if primary.published_date and incoming.published_date:
        data["published_date"] = min(primary.published_date, incoming.published_date)
    else:
        data["published_date"] = primary.published_date or incoming.published_date
    if primary.updated_date and incoming.updated_date:
        data["updated_date"] = max(primary.updated_date, incoming.updated_date)
    else:
        data["updated_date"] = primary.updated_date or incoming.updated_date
    for field in ("citation_count", "influential_citation_count", "huggingface_upvotes", "github_stars"):
        data[field] = max(getattr(primary, field), getattr(incoming, field))
    for field in (
        "paper_id", "pdf_url", "venue", "year", "huggingface_url", "code_url",
        "github_language", "demo_url", "task", "dataset",
    ):
        data[field] = getattr(primary, field) or getattr(incoming, field)
    return Paper.model_validate(data)


def deduplicate_papers(
    papers: list[Paper], similarity_threshold: float = 0.94
) -> list[Paper]:
    result: list[Paper] = []
    for incoming in papers:
        normalized_incoming_title = normalize_title(incoming.title)
        normalized_incoming_url = normalize_url(incoming.url)
        match_index: int | None = None
        for index, existing in enumerate(result):
            if normalize_title(existing.title) == normalized_incoming_title:
                match_index = index
                break
            if normalize_url(existing.url) == normalized_incoming_url:
                match_index = index
                break
            if title_similarity(existing.title, incoming.title) >= similarity_threshold:
                match_index = index
                break
        if match_index is None:
            result.append(incoming.model_copy(deep=True))
        else:
            result[match_index] = merge_papers(result[match_index], incoming)
    return result
