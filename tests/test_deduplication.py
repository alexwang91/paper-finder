from datetime import date

from deduplication import deduplicate_papers, normalize_title, normalize_url
from models import Paper


def make_paper(**changes: object) -> Paper:
    values: dict[str, object] = {
        "title": "Agent, Inc.!",
        "url": "https://arxiv.org/abs/2607.00001",
        "source": "arxiv",
    }
    values.update(changes)
    return Paper(**values)


def test_normalizes_title_and_arxiv_pdf_url() -> None:
    assert normalize_title(" Agent,  Inc.! ") == "agent inc"
    assert normalize_url("https://arxiv.org/pdf/2607.00001.pdf?download=1") == "arxiv:2607.00001"


def test_merges_similar_duplicates_and_metadata() -> None:
    first = make_paper(authors=["A"], published_date=date(2026, 7, 8))
    second = make_paper(
        title="Agent Inc: a commercial workflow",
        url="https://example.org/paper/agent-inc",
        source="semantic_scholar",
        abstract="Longer abstract",
        authors=["B"],
        code_url="https://github.com/acme/agent-inc",
        github_stars=42,
    )

    result = deduplicate_papers([first, second], similarity_threshold=0.55)

    assert len(result) == 1
    assert result[0].sources == ["arxiv", "semantic_scholar"]
    assert result[0].authors == ["A", "B"]
    assert result[0].code_url == "https://github.com/acme/agent-inc"
    assert result[0].github_stars == 42
