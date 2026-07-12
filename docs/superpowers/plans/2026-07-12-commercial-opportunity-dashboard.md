# Commercial Opportunity Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generate a polished, offline-capable HTML dashboard that compares the current Top 21 papers and exposes a specific product concept, customer, monetization hypothesis, acquisition path, 30-day validation plan, and risks for every item.

**Architecture:** A Python build script reads the newest valid ranking CSV, validates the 21-paper contract, merges title-keyed business playbooks from YAML, and injects safely encoded data into a static HTML template. All search, category filters, sorting, selection, and responsive detail behavior run locally in the generated page with no backend or network request.

**Tech Stack:** Python 3.11+, csv/json/html standard libraries, PyYAML, pytest, semantic HTML, CSS, vanilla JavaScript.

---

## File map

```text
dashboard/
├── business_playbooks.yaml   # Human-written commercial hypotheses for the current Top 21
├── template.html             # Approved light Founder Terminal UI and local interactions
└── index.html                # Generated standalone dashboard
scripts/
└── build_dashboard.py        # CSV selection, validation, merge, and rendering
tests/
└── test_dashboard.py         # Generator, content, failure, and output contracts
.github/workflows/weekly.yml  # Regenerates and commits dashboard/index.html
README.md                     # Dashboard build/open instructions
```

### Task 1: Ranking loader and hard input contract

**Files:**
- Create: `scripts/build_dashboard.py`
- Create: `tests/test_dashboard.py`

- [ ] **Step 1: Write the first failing test for newest CSV selection**

```python
from pathlib import Path

from scripts.build_dashboard import find_latest_ranking


def test_finds_latest_dated_ranking(tmp_path: Path) -> None:
    (tmp_path / "weekly_paper_rank_2026-07-11.csv").write_text("rank,title,source\n", encoding="utf-8")
    newest = tmp_path / "weekly_paper_rank_2026-07-12.csv"
    newest.write_text("rank,title,source\n", encoding="utf-8")

    assert find_latest_ranking(tmp_path) == newest
```

- [ ] **Step 2: Run the test and verify RED**

Run: `python -m pytest tests/test_dashboard.py::test_finds_latest_dated_ranking -q`

Expected: FAIL because `scripts.build_dashboard` does not exist.

- [ ] **Step 3: Implement filename-based latest selection**

`find_latest_ranking(output_dir: Path) -> Path` must match only `weekly_paper_rank_YYYY-MM-DD.csv`, parse dates with `date.fromisoformat`, sort by date, and raise `DashboardBuildError("no weekly ranking CSV found")` when none exist.

- [ ] **Step 4: Add one failing test for the 21-real-paper contract**

```python
import pytest

from scripts.build_dashboard import DashboardBuildError, load_ranking


def test_rejects_short_or_placeholder_ranking(tmp_path: Path) -> None:
    short = tmp_path / "short.csv"
    short.write_text("rank,title,source\n1,Paper,arxiv\n", encoding="utf-8")
    with pytest.raises(DashboardBuildError, match="exactly 21"):
        load_ranking(short)
```

Add a second fixture with 21 rows where one `source` is `placeholder` and assert a `DashboardBuildError` mentioning placeholders.

- [ ] **Step 5: Verify RED, implement CSV validation, and verify GREEN**

`load_ranking(path: Path) -> list[dict[str, str]]` uses `csv.DictReader`, requires all dashboard fields, requires ranks 1–21 exactly once, rejects placeholders, and preserves the original default rank order.

Run: `python -m pytest tests/test_dashboard.py -q`

Expected: all Task 1 tests pass.

### Task 2: Write and validate 21 specific commercial playbooks

**Files:**
- Create: `dashboard/business_playbooks.yaml`
- Modify: `tests/test_dashboard.py`

- [ ] **Step 1: Add a failing playbook coverage test**

```python
from scripts.build_dashboard import load_playbooks, merge_dashboard_data


def test_current_ranking_has_complete_specific_playbooks(current_ranking_path: Path) -> None:
    papers = load_ranking(current_ranking_path)
    playbooks = load_playbooks(Path("dashboard/business_playbooks.yaml"))
    merged = merge_dashboard_data(papers, playbooks)

    assert len(merged) == 21
    for item in merged:
        assert item["playbook_status"] == "curated"
        assert item["product_name"]
        assert item["mvp"]
        assert item["pilot_price"]
        assert item["steady_state_pricing"]
        assert item["acquisition"]
        assert item["validation_30d"]
        assert item["risks"]
```

- [ ] **Step 2: Verify RED**

Run: `python -m pytest tests/test_dashboard.py::test_current_ranking_has_complete_specific_playbooks -q`

Expected: FAIL because the YAML file and loader do not exist.

- [ ] **Step 3: Create all 21 curated records**

Use the exact paper titles as YAML keys. The core commercial directions are:

| Rank | Product name | Buyer and monetization hypothesis |
| ---: | --- | --- |
| 1 | HCC MDT Copilot | Oncology centers; €8k–20k pilot, €30k–80k annual private deployment |
| 2 | DSpark Accelerator | LLM product teams; usage meter plus $299–1,999 monthly developer plans |
| 3 | Agent QA Lab | Agent builders; per evaluation run plus $299–1,499 monthly team plan |
| 4 | Causal Analyst | Analytics and life-science teams; $99–399 per seat plus paid audit projects |
| 5 | HumanForge Verify | Media platforms and insurers; per video minute plus enterprise minimum |
| 6 | Context Access Audit | Enterprises and public bodies; €5k–20k audit plus governance subscription |
| 7 | Authenticity Check | Marketplaces and content teams; freemium extension plus image API credits |
| 8 | Materials Reasoning Desk | Materials R&D teams; research seats and private deployment |
| 9 | ARDY Motion Studio | Game and animation studios; generation credits plus team seats |
| 10 | Tactile Alignment Kit | Robotics labs and integrators; dataset tooling license and implementation services |
| 11 | AlayaWorld Prototyper | Game studios; world-generation credits and studio plans |
| 12 | Idea Lineage Intelligence | R&D strategy and patent teams; $149–599 seats plus enterprise knowledge base |
| 13 | Exploration Optimizer | Model training teams; benchmark engagement plus enterprise library license |
| 14 | Pharo Copilot | Legacy Pharo teams; per-developer subscription and migration services |
| 15 | Video Reasoning Foundry | Video-agent teams; synthetic training data priced per generated hour |
| 16 | DrugGen Workspace | Biotech and CRO teams; paid research pilot and annual private workspace |
| 17 | Judge Reliability Auditor | AI quality teams; per test suite plus $199–999 monthly plan |
| 18 | Action Shortcut Debugger | Robotics and vision teams; dataset/evaluation license plus consulting |
| 19 | Edge Audio Runtime | Mobile and IoT OEMs; SDK license plus per-device royalty |
| 20 | Super Weight Inspector | Foundation-model teams; diagnostic engagement plus enterprise tooling |
| 21 | Sparse Memory Runtime | Edge sequence-model teams; commercial library and OEM license |

Every record must include a specific one-liner, target customers, pain point, 2–4 week MVP, pricing unit, pilot price, steady-state price, acquisition route, 30-day validation steps, and risks. Mark every numeric price as a hypothesis.

- [ ] **Step 4: Implement safe YAML loading and fallback merge**

`load_playbooks(path)` validates mapping shape and required fields. `normalize_title()` uses NFKC, case-folding, punctuation removal, and whitespace compression. `merge_dashboard_data()` joins by normalized title. Missing playbooks use CSV product/user/monetization fields, set `playbook_status="fallback"`, and use `"待客户访谈验证"` instead of invented prices.

- [ ] **Step 5: Run playbook tests**

Run: `python -m pytest tests/test_dashboard.py -q`

Expected: all current tests pass and all current 21 records are curated.

### Task 3: Static HTML renderer and interactions

**Files:**
- Create: `dashboard/template.html`
- Create: `dashboard/index.html`
- Modify: `scripts/build_dashboard.py`
- Modify: `tests/test_dashboard.py`

- [ ] **Step 1: Write a failing render-contract test**

```python
from scripts.build_dashboard import build_dashboard


def test_builds_offline_dashboard_with_all_21_titles(tmp_path: Path, current_ranking_path: Path) -> None:
    destination = tmp_path / "index.html"
    build_dashboard(
        ranking_path=current_ranking_path,
        playbook_path=Path("dashboard/business_playbooks.yaml"),
        template_path=Path("dashboard/template.html"),
        destination=destination,
    )
    html = destination.read_text(encoding="utf-8")
    assert html.count('class="paper-row"') == 0
    assert "__DASHBOARD_DATA__" not in html
    assert "HCC MDT Copilot" in html
    assert "Sparse Memory Runtime" in html
    assert "104" in html
```

The zero `paper-row` assertion ensures rows are rendered from safely encoded inline JSON by JavaScript, not unsafe string interpolation.

- [ ] **Step 2: Verify RED**

Run: `python -m pytest tests/test_dashboard.py::test_builds_offline_dashboard_with_all_21_titles -q`

Expected: FAIL because renderer and template do not exist.

- [ ] **Step 3: Implement `build_dashboard()` and CLI**

Serialize data with `json.dumps(items, ensure_ascii=False).replace("</", "<\\/")`. Replace exactly one `__DASHBOARD_DATA__` token and one `__REPORT_META__` token. Write UTF-8 through a temporary sibling file and atomic replace. CLI options:

```text
--output-dir outputs
--ranking PATH
--playbooks dashboard/business_playbooks.yaml
--template dashboard/template.html
--destination dashboard/index.html
```

- [ ] **Step 4: Implement the approved light Founder Terminal template**

The template must contain:

- White/cool-gray surface, black text, blue selection, fluorescent-green status accents.
- Four summary metrics derived from data.
- Search input, category buttons, sort select, and reset button.
- Desktop two-column list/detail layout.
- Rank, score, product, pricing unit, MVP, and category columns.
- Detail sections for research, product, customer, MVP, pricing hypothesis, acquisition, 30-day validation, risks, links, and four core scores.
- Keyboard-accessible native controls and row buttons.
- Mobile single-column layout with selected detail after the list.
- No external fonts, scripts, images, CDN, `fetch`, XHR, or WebSocket.

Dynamic text must be assigned with `textContent`; links must validate `http:` or `https:` before assigning `href` and use `rel="noopener noreferrer"`.

- [ ] **Step 5: Implement local interactions**

Use a single state object `{query, category, sort, selectedRank}`. `render()` filters and sorts without mutating the source list, updates result count, renders row buttons, and either renders the selected item or a clear empty state. Events: search `input`, category `click`, sort `change`, reset `click`, row `click`.

- [ ] **Step 6: Add and run output tests**

Tests assert unique required IDs, inline 21-item JSON, all current product names, all detail section labels, no `fetch(`, and output below 1 MB.

Run: `python -m pytest tests/test_dashboard.py -q`

Expected: all dashboard tests pass.

### Task 4: Weekly automation and documentation

**Files:**
- Modify: `.github/workflows/weekly.yml`
- Modify: `README.md`
- Modify: `tests/test_dashboard.py`

- [ ] **Step 1: Add a failing workflow contract test**

Assert `.github/workflows/weekly.yml` runs `python scripts/build_dashboard.py` after `python main.py` and stages `dashboard/index.html`.

- [ ] **Step 2: Verify RED and update workflow**

Keep the existing generation command unchanged. Add a dashboard build step immediately afterward and include `dashboard/index.html` in the commit step. Dashboard build failure must fail the workflow.

- [ ] **Step 3: Document local build and opening**

README must include:

```bash
python scripts/build_dashboard.py
python -m http.server 8000
```

Explain that `dashboard/index.html` works by double-clicking, the server command is only for a browser URL, the dashboard uses the latest valid CSV, prices are hypotheses, and weekly automation rebuilds it.

- [ ] **Step 4: Run workflow and documentation tests**

Run: `python -m pytest tests/test_dashboard.py -q`

Expected: all dashboard tests pass.

### Task 5: Full verification, browser QA, and publication

**Files:**
- Review: `dashboard/index.html`
- Review: all dashboard-related source and test files

- [ ] **Step 1: Run the complete suite and compilation**

Run: `python -m pytest -q`

Expected: all project tests pass.

Run: `python -m compileall -q .`

Expected: exit code 0.

- [ ] **Step 2: Regenerate from the latest real Top 21**

Run: `python scripts/build_dashboard.py`

Expected: reports 21 curated projects and writes `dashboard/index.html`.

- [ ] **Step 3: Verify data and HTML contracts**

Check generated HTML contains 21 project records, no placeholder sources, no unreplaced template tokens, no secrets, and is below 1 MB.

- [ ] **Step 4: Perform browser QA**

Open the generated page at desktop and mobile widths. Verify initial render, all 21 rows, search, each category filter, each sort order, reset, selection detail switching, external links, empty state, focus visibility, no console errors, no clipping, and no horizontal overflow.

- [ ] **Step 5: Commit and publish to `alexwang91/paper-finder`**

Commit the dashboard source, generated HTML, tests, workflow, and README. Publish the `weekly-paper-radar/` subtree to the target repository while preserving workflow-generated output history. Re-run the GitHub Action and verify it regenerates the dashboard successfully.

## Plan self-review result

- Every approved visual, content, interaction, automation, error, and test requirement maps to a task.
- Current Top 21 commercial directions are enumerated; no playbook record is left unspecified.
- TDD uses vertical slices: loader, validation, playbook merge, renderer, then workflow.
- The generated HTML is offline-capable and contains no runtime data fetch.
- Future missing playbooks degrade visibly without invented exact prices.
