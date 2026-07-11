import json
from datetime import date
from pathlib import Path
from types import SimpleNamespace

from sources.arxiv_fetcher import ArxivFetcher
from sources.github_fetcher import GitHubFetcher
from sources.huggingface_fetcher import HuggingFaceFetcher
from sources.paperswithcode_fetcher import PapersWithCodeFetcher
from sources.semantic_scholar_fetcher import SemanticScholarFetcher

FIXTURES = Path(__file__).parent / "fixtures"


def test_arxiv_parser_extracts_pdf_and_categories() -> None:
    papers = ArxivFetcher.parse_feed((FIXTURES / "arxiv_feed.xml").read_bytes())

    assert papers[0].source == "arxiv"
    assert papers[0].pdf_url == "https://arxiv.org/pdf/2607.00001"
    assert papers[0].authors == ["Alice Example"]
    assert "cs.AI" in papers[0].categories


class FakeResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self._payload = payload
        self.content = b""

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, object]:
        return self._payload


class FakeSession:
    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload
        self.last_params: dict[str, object] = {}

    def get(self, url: str, **kwargs: object) -> FakeResponse:
        self.last_params = kwargs.get("params", {})  # type: ignore[assignment]
        return FakeResponse(self.payload)


def test_semantic_scholar_parser_and_date_filter() -> None:
    payload = json.loads((FIXTURES / "semantic_scholar.json").read_text(encoding="utf-8"))
    session = FakeSession(payload)
    fetcher = SemanticScholarFetcher(session, api_key=None, max_results=10)

    papers = fetcher.fetch(date(2026, 7, 6), date(2026, 7, 12), ["AI agent"])

    assert papers[0].abstract is None
    assert papers[0].citation_count == 12
    assert session.last_params["publicationDateOrYear"] == "2026-07-06:2026-07-12"


class FakeHfApi:
    def __init__(self) -> None:
        self.dates: list[str] = []

    def list_daily_papers(self, **kwargs: object) -> list[SimpleNamespace]:
        self.dates.append(str(kwargs["date"]))
        return [SimpleNamespace(
            id="2607.00001",
            title="Useful Workflow Agent",
            summary="Turns documents into workflows.",
            upvotes=25,
            authors=[SimpleNamespace(name="Alice Example")],
            models=[SimpleNamespace(id="acme/model")],
            datasets=[SimpleNamespace(id="acme/data")],
            spaces=[SimpleNamespace(id="acme/demo")],
        )]


def test_huggingface_maps_daily_paper_resources() -> None:
    api = FakeHfApi()
    fetcher = HuggingFaceFetcher(api, max_results=5)

    papers = fetcher.fetch(date(2026, 7, 8), date(2026, 7, 8), [])

    assert papers[0].huggingface_upvotes == 25
    assert papers[0].linked_models == ["acme/model"]
    assert papers[0].linked_datasets == ["acme/data"]
    assert papers[0].linked_spaces == ["acme/demo"]


def test_huggingface_prioritizes_most_recent_day() -> None:
    api = FakeHfApi()
    fetcher = HuggingFaceFetcher(api, max_results=1)

    fetcher.fetch(date(2026, 7, 6), date(2026, 7, 12), [])

    assert api.dates == ["2026-07-12"]


def test_github_enrichment_rejects_irrelevant_high_star_repo() -> None:
    payload = {"items": [
        {"html_url": "https://github.com/x/unrelated", "name": "unrelated", "description": "Other project",
         "stargazers_count": 900, "language": "Rust", "updated_at": "2026-07-10T00:00:00Z"},
        {"html_url": "https://github.com/x/useful-agent", "name": "useful-agent",
         "description": "Useful Workflow Agent implementation", "stargazers_count": 80,
         "language": "Python", "updated_at": "2026-07-10T00:00:00Z"},
    ]}
    session = FakeSession(payload)
    paper = ArxivFetcher.parse_feed((FIXTURES / "arxiv_feed.xml").read_bytes())[0]

    enriched = GitHubFetcher(session, token=None, max_results=5).enrich([paper])

    assert enriched[0].code_url == "https://github.com/x/useful-agent"
    assert enriched[0].github_stars == 80


def test_paperswithcode_parses_api_and_html_fallback() -> None:
    payload = json.loads((FIXTURES / "paperswithcode.json").read_text(encoding="utf-8"))
    api_papers = PapersWithCodeFetcher.parse_payload(payload)
    html_papers = PapersWithCodeFetcher.parse_html(
        (FIXTURES / "paperswithcode.html").read_text(encoding="utf-8")
    )

    assert api_papers[0].code_url == "https://github.com/acme/agent-benchmark"
    assert api_papers[0].github_stars == 123
    assert api_papers[0].task == "Agent evaluation"
    assert html_papers[0].title == "HTML Fallback Paper"
