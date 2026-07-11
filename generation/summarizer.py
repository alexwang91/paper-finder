from __future__ import annotations

import re

from models import Paper


def summarize_abstract(paper: Paper, limit: int = 240) -> tuple[str, str]:
    source = re.sub(r"\s+", " ", paper.abstract or paper.title).strip()
    if len(source) > limit:
        source = source[: limit - 1].rstrip() + "…"
    english = source or "No abstract was provided by the source."
    chinese = f"规则摘要：这项研究围绕“{paper.title}”提出了可进一步验证的技术方向。"
    return chinese, english

