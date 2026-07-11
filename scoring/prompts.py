from __future__ import annotations

from models import Paper

SYSTEM_PROMPT = """You evaluate research for solo founders and small product teams.
Prioritize practical commercial value over academic prestige. Use only the supplied metadata.
Return plain language, specific product ideas, realistic risks, and scores from 0 to 100.
Do not invent customers, traction, citations, code, demos, or experimental results."""


def build_paper_prompt(paper: Paper) -> str:
    return (
        f"Title: {paper.title}\n"
        f"Abstract: {paper.abstract or 'Not provided'}\n"
        f"Categories: {', '.join(paper.categories) or 'Unknown'}\n"
        f"Citations: {paper.citation_count}\n"
        f"GitHub stars: {paper.github_stars}\n"
        f"Code URL: {paper.code_url or 'None'}\n"
        f"Demo URL: {paper.demo_url or 'None'}"
    )

