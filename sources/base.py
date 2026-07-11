from __future__ import annotations

from datetime import date
from typing import Protocol

from models import Paper


class SourceUnavailable(RuntimeError):
    pass


class PaperFetcher(Protocol):
    name: str

    def fetch(self, start_date: date, end_date: date, keywords: list[str]) -> list[Paper]:
        raise NotImplementedError

