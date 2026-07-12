from __future__ import annotations

import csv
import json
import re
import unicodedata
from argparse import ArgumentParser
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

import yaml


class DashboardBuildError(RuntimeError):
    pass


_RANKING_NAME = re.compile(r"^weekly_paper_rank_(\d{4}-\d{2}-\d{2})\.csv$")
_REQUIRED_FIELDS = {
    "rank", "title", "url", "pdf_url", "source", "category",
    "abstract_summary_cn", "abstract_summary_en", "key_innovation",
    "why_it_matters", "product_idea", "target_users", "monetization",
    "mvp_complexity", "commercial_potential_score",
    "solo_founder_feasibility_score", "mvp_speed_score", "total_score",
    "risks", "recommended_next_step", "code_url", "huggingface_url",
}


def find_latest_ranking(output_dir: Path) -> Path:
    dated: list[tuple[date, Path]] = []
    for path in output_dir.glob("weekly_paper_rank_*.csv"):
        match = _RANKING_NAME.match(path.name)
        if not match:
            continue
        try:
            dated.append((date.fromisoformat(match.group(1)), path))
        except ValueError:
            continue
    if not dated:
        raise DashboardBuildError("no weekly ranking CSV found")
    return max(dated, key=lambda item: item[0])[1]


def load_ranking(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fieldnames = set(reader.fieldnames or [])
    if len(rows) != 21:
        raise DashboardBuildError(f"ranking must contain exactly 21 papers; got {len(rows)}")
    if any("placeholder" in (row.get("source") or "").casefold() for row in rows):
        raise DashboardBuildError("ranking contains placeholder papers")
    if any("demo_fixture" in (row.get("source") or "").casefold() for row in rows):
        raise DashboardBuildError("ranking contains demo_fixture papers")
    try:
        ranks = [int(row.get("rank") or "") for row in rows]
    except ValueError as exc:
        raise DashboardBuildError("ranking contains an invalid rank") from exc
    if sorted(ranks) != list(range(1, 22)) or len(set(ranks)) != 21:
        raise DashboardBuildError("ranking must contain ranks 1 through 21 exactly once")
    missing = sorted(_REQUIRED_FIELDS - fieldnames)
    if missing:
        raise DashboardBuildError(f"ranking is missing required fields: {', '.join(missing)}")
    return [row for _, row in sorted(zip(ranks, rows), key=lambda item: item[0])]


_PLAYBOOK_FIELDS = {
    "product_name", "one_liner", "target_customers", "pain_point", "mvp",
    "pricing_unit", "pilot_price", "steady_state_pricing", "acquisition",
    "validation_30d", "risks",
}


def normalize_title(value: str) -> str:
    text = unicodedata.normalize("NFKC", value).casefold()
    text = "".join(character if character.isalnum() else " " for character in text)
    return " ".join(text.split())


def load_playbooks(path: Path) -> dict[str, dict[str, Any]]:
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError) as exc:
        raise DashboardBuildError(f"cannot load playbooks from {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise DashboardBuildError("playbooks root must be a mapping keyed by paper title")
    result: dict[str, dict[str, Any]] = {}
    for title, record in payload.items():
        if not isinstance(title, str) or not isinstance(record, dict):
            raise DashboardBuildError("every playbook must map a paper title to a record")
        missing = sorted(_PLAYBOOK_FIELDS - set(record))
        if missing:
            raise DashboardBuildError(f"playbook '{title}' is missing: {', '.join(missing)}")
        key = normalize_title(title)
        if key in result:
            raise DashboardBuildError(f"duplicate normalized playbook title: {title}")
        result[key] = dict(record)
    return result


def merge_dashboard_data(
    papers: list[dict[str, str]], playbooks: dict[str, dict[str, Any]]
) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    for paper in papers:
        item: dict[str, Any] = dict(paper)
        playbook = playbooks.get(normalize_title(paper["title"]))
        if playbook:
            item.update(playbook)
            item["playbook_status"] = "curated"
        else:
            item.update({
                "product_name": paper.get("product_idea") or "待定义产品",
                "one_liner": paper.get("why_it_matters") or "待进一步验证的研究机会",
                "target_customers": [value.strip() for value in paper.get("target_users", "").split(";") if value.strip()],
                "pain_point": paper.get("business_insight") or "待客户访谈验证",
                "mvp": paper.get("product_idea") or "待客户访谈验证",
                "pricing_unit": paper.get("monetization") or "待客户访谈验证",
                "pilot_price": "待客户访谈验证",
                "steady_state_pricing": "待客户访谈验证",
                "acquisition": [paper.get("recommended_next_step") or "访谈目标客户"],
                "validation_30d": [paper.get("recommended_next_step") or "完成首轮客户访谈"],
                "risks": [paper.get("risks") or "待技术验证"],
                "playbook_status": "fallback",
            })
        merged.append(item)
    return merged


def _report_metadata(ranking_path: Path, papers: list[dict[str, Any]]) -> dict[str, Any]:
    match = _RANKING_NAME.match(ranking_path.name)
    candidate_count: int | str = "30+"
    if match:
        raw_path = ranking_path.with_name(f"raw_candidates_{match.group(1)}.json")
        try:
            raw_candidates = json.loads(raw_path.read_text(encoding="utf-8-sig"))
            if isinstance(raw_candidates, list):
                candidate_count = len(raw_candidates)
        except (OSError, json.JSONDecodeError):
            pass
    categories = Counter(str(item.get("category") or "未分类") for item in papers)
    scores = [float(item.get("total_score") or 0) for item in papers]
    return {
        "report_date": match.group(1) if match else "",
        "candidate_count": candidate_count,
        "selected_count": len(papers),
        "top_score": max(scores, default=0),
        "category_count": len(categories),
        "category_counts": dict(categories),
    }


def build_dashboard(
    ranking_path: Path,
    playbook_path: Path,
    template_path: Path,
    destination: Path,
) -> Path:
    papers = merge_dashboard_data(load_ranking(ranking_path), load_playbooks(playbook_path))
    template = template_path.read_text(encoding="utf-8")
    if template.count("__DASHBOARD_DATA__") != 1 or template.count("__REPORT_META__") != 1:
        raise DashboardBuildError("template must contain each dashboard token exactly once")
    data_json = json.dumps(papers, ensure_ascii=False).replace("</", "<\\/")
    meta_json = json.dumps(_report_metadata(ranking_path, papers), ensure_ascii=False).replace("</", "<\\/")
    rendered = template.replace("__DASHBOARD_DATA__", data_json).replace("__REPORT_META__", meta_json)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    temporary.write_text(rendered, encoding="utf-8")
    temporary.replace(destination)
    return destination


def main() -> None:
    parser = ArgumentParser(description="Build the standalone commercial opportunity dashboard")
    parser.add_argument("--output-dir", type=Path, default=Path("outputs"))
    parser.add_argument("--ranking", type=Path)
    parser.add_argument("--playbooks", type=Path, default=Path("dashboard/business_playbooks.yaml"))
    parser.add_argument("--template", type=Path, default=Path("dashboard/template.html"))
    parser.add_argument("--destination", type=Path, default=Path("dashboard/index.html"))
    args = parser.parse_args()
    ranking = args.ranking or find_latest_ranking(args.output_dir)
    result = build_dashboard(ranking, args.playbooks, args.template, args.destination)
    print(f"Built {result} from {ranking}")


if __name__ == "__main__":
    main()
