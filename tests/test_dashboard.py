import csv
import json
from pathlib import Path

import pytest

from scripts.build_dashboard import (
    DashboardBuildError,
    build_dashboard,
    find_latest_ranking,
    load_playbooks,
    load_ranking,
    merge_dashboard_data,
    normalize_title,
)

CURRENT_TITLES = [
    "Towards Precision Therapy in Hepatocellular Carcinoma: A Clinical-Reasoning LLM for Risk Stratification and Treatment Guidance",
    "DSpark: Confidence-Scheduled Speculative Decoding with Semi-Autoregressive Generation",
    "UniClawBench: A Universal Benchmark for Proactive Agents on Real-World Tasks",
    "CausalDS: Benchmarking Causal Reasoning in Data-Science Agents",
    "HumanForge: A Human-Centric Deepfake Video Benchmark with Multi-Agent Forgery Rationales",
    "The Context Access Divide: Interaction-Level Architecture as a Complementary Dimension of Agentic Inequality",
    "Do Transformations Reveal the Truth? Generative Residual Learning for Generalized AI-Generated Image Detection",
    "Accurate, Interdisciplinary and Transparent Structure-property Understanding with Deep Native Structural Reasoning",
    "ARDY: Autoregressive Diffusion with Hybrid Representation for Interactive Human Motion Generation",
    "Wake up for Touch! Mask-isolated Tactile Alignment Learning in MLLMs",
    "AlayaWorld: Long-Horizon and Playable Video World Generation",
    "Ideas Have Genomes: Benchmarking Scientific Lineage Reasoning and Lineage-Grounded Idea Generation",
    "UP: Unbounded Positive Asymmetric Optimization for Breaking the Exploration-Stability Dilemma",
    "Teaching LLMs a Low-Resource Language: Enhancing Code Completion in Pharo",
    "OpenCoF: Learning to Reason Through Video Generation",
    "DrugGen 2: A disease-aware language model for enhancing drug discovery",
    "When the Judge Changes, So Does the Measurement: Auditing LLM-as-Judge Reliability",
    "Why Can't I Open My Drawer? Mitigating Object-Driven Shortcuts in Zero-Shot Compositional Action Recognition",
    "A Quantized Native Runtime for On-Device Semantic Audio Generation",
    "Super Weights in LLMs and the Failure of Selective Training",
    "Sparse Delta Memory: Scaling the State of Linear RNNs through Sparsity",
]

RANKING_FIELDS = [
    "rank", "title", "url", "pdf_url", "source", "category",
    "abstract_summary_cn", "abstract_summary_en", "key_innovation",
    "why_it_matters", "business_insight", "product_idea", "target_users",
    "monetization", "mvp_complexity", "commercial_potential_score",
    "solo_founder_feasibility_score", "mvp_speed_score", "total_score",
    "risks", "recommended_next_step", "code_url", "huggingface_url",
]


def write_current_ranking(path: Path) -> Path:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=RANKING_FIELDS)
        writer.writeheader()
        for rank, title in enumerate(CURRENT_TITLES, start=1):
            writer.writerow({
                "rank": rank,
                "title": title,
                "url": f"https://example.com/paper/{rank}",
                "pdf_url": f"https://example.com/paper/{rank}.pdf",
                "source": "arxiv",
                "category": "agents_workflow",
                "abstract_summary_cn": "中文研究摘要",
                "abstract_summary_en": "English research summary",
                "key_innovation": "Key innovation",
                "why_it_matters": "Why it matters",
                "business_insight": "Business insight",
                "product_idea": "Product idea",
                "target_users": "Team A; Team B",
                "monetization": "Subscription",
                "mvp_complexity": "medium",
                "commercial_potential_score": "70",
                "solo_founder_feasibility_score": "65",
                "mvp_speed_score": "60",
                "total_score": str(80 - rank),
                "risks": "Risk",
                "recommended_next_step": "Interview users",
                "code_url": "",
                "huggingface_url": "",
            })
    return path


def test_finds_latest_dated_ranking(tmp_path: Path) -> None:
    (tmp_path / "weekly_paper_rank_2026-07-11.csv").write_text(
        "rank,title,source\n", encoding="utf-8"
    )
    newest = tmp_path / "weekly_paper_rank_2026-07-12.csv"
    newest.write_text("rank,title,source\n", encoding="utf-8")

    assert find_latest_ranking(tmp_path) == newest


def test_rejects_short_or_placeholder_ranking(tmp_path: Path) -> None:
    short = tmp_path / "short.csv"
    short.write_text("rank,title,source\n1,Paper,arxiv\n", encoding="utf-8")

    with pytest.raises(DashboardBuildError, match="exactly 21"):
        load_ranking(short)

    placeholder = tmp_path / "placeholder.csv"
    rows = ["rank,title,source"] + [
        f"{rank},Paper {rank},{'placeholder' if rank == 21 else 'arxiv'}"
        for rank in range(1, 22)
    ]
    placeholder.write_text("\n".join(rows), encoding="utf-8")

    with pytest.raises(DashboardBuildError, match="placeholder"):
        load_ranking(placeholder)


def test_real_top_21_has_complete_curated_playbooks(tmp_path: Path) -> None:
    papers = load_ranking(write_current_ranking(tmp_path / "ranking.csv"))
    playbooks = load_playbooks(Path("dashboard/business_playbooks.yaml"))

    merged = merge_dashboard_data(papers, playbooks)

    assert len(merged) == 21
    for item in merged:
        assert item["playbook_status"] == "curated"
        for field in (
            "product_name", "one_liner", "target_customers", "pain_point", "mvp",
            "pricing_unit", "pilot_price", "steady_state_pricing", "acquisition",
            "validation_30d", "risks",
        ):
            assert item[field], f"{item['title']} is missing {field}"


def test_builds_a_self_contained_interactive_dashboard(tmp_path: Path) -> None:
    ranking = write_current_ranking(tmp_path / "weekly_paper_rank_2026-07-12.csv")
    (tmp_path / "raw_candidates_2026-07-12.json").write_text(
        json.dumps([{"title": str(index)} for index in range(37)]), encoding="utf-8"
    )
    destination = tmp_path / "index.html"

    build_dashboard(
        ranking_path=ranking,
        playbook_path=Path("dashboard/business_playbooks.yaml"),
        template_path=Path("dashboard/template.html"),
        destination=destination,
    )

    html = destination.read_text(encoding="utf-8")
    assert "__DASHBOARD_DATA__" not in html
    assert "__REPORT_META__" not in html
    assert html.count('id="dashboard-data"') == 1
    assert html.count('id="search-input"') == 1
    assert html.count('id="category-filters"') == 1
    assert html.count('id="sort-select"') == 1
    assert html.count('id="paper-list"') == 1
    assert html.count('id="paper-detail"') == 1
    assert '"product_name": "HCC MDT Copilot"' in html
    assert '"product_name": "Sparse Memory Runtime"' in html
    assert '"candidate_count": 37' in html
    assert "fetch(" not in html
    assert len(html.encode("utf-8")) < 1_000_000


def test_weekly_workflow_rebuilds_and_commits_dashboard() -> None:
    workflow = Path(".github/workflows/weekly.yml").read_text(encoding="utf-8")

    assert "python scripts/build_dashboard.py" in workflow
    assert "dashboard/index.html" in workflow


def test_current_leading_papers_have_curated_playbooks() -> None:
    playbooks = load_playbooks(Path("dashboard/business_playbooks.yaml"))
    for title in (
        "LongE2V: Long-Horizon Event-based Video Reconstruction, Prediction, and Frame Interpolation with Video Diffusion Models",
        "Wat3R: Underwater 3D Geometry Learning without Annotations",
        "Jet-Long: Efficient Long-Context Extension with Dynamic Bifocal RoPE",
    ):
        assert normalize_title(title) in playbooks
