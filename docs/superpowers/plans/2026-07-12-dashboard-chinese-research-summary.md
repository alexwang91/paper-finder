# 看板中文化与论文结论前置 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为当前 Top 21 每篇论文增加专属中文研究结论，并把非专业界面文字全部中文化。

**Architecture:** 商业方案 YAML 作为人工策划内容的唯一来源，新增必填字段 `research_takeaway`。Python 生成器负责完整性校验和数据合并；单文件 HTML 只负责按“论文结论优先”的顺序渲染，并用固定中文映射显示分类。

**Tech Stack:** Python 3.11+、PyYAML、pytest、原生 HTML/CSS/JavaScript

---

### Task 1: 锁定论文结论数据契约

**Files:**
- Modify: `tests/test_dashboard.py`
- Modify: `scripts/build_dashboard.py`

- [ ] **Step 1: Write the failing test**

在 `test_real_top_21_has_complete_curated_playbooks` 的字段列表加入 `research_takeaway`，并断言每条文字包含“方法”“验证”“价值”三个语义段落所需的非空内容。

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_dashboard.py::test_real_top_21_has_complete_curated_playbooks -q`
Expected: FAIL，提示缺少 `research_takeaway`。

- [ ] **Step 3: Write minimal implementation**

把 `research_takeaway` 加入 `_PLAYBOOK_FIELDS`，使缺字段的方案在生成阶段直接报错。

- [ ] **Step 4: Run test to verify validation is active**

Run: `python -m pytest tests/test_dashboard.py::test_real_top_21_has_complete_curated_playbooks -q`
Expected: 仍失败，但错误位置进入 YAML 内容缺失，而不是字段未被校验。

### Task 2: 编写当前 21 篇专属论文结论

**Files:**
- Modify: `dashboard/business_playbooks.yaml`
- Test: `tests/test_dashboard.py`

- [ ] **Step 1: Add one `research_takeaway` to every playbook**

每条使用一段自然中文，严格回答：论文采用的关键方法；实验验证或证明的结论；对准确率、速度、成本、可靠性或具体工作流的提升价值。技术专名保持原文，不写无法从论文题目、摘要和已有分析支持的绝对结论。

- [ ] **Step 2: Run curated-content test**

Run: `python -m pytest tests/test_dashboard.py -q`
Expected: 所有 dashboard 数据测试通过，当前 Top 21 的 `playbook_status` 均为 `curated`。

### Task 3: 论文结论前置与界面中文化

**Files:**
- Modify: `dashboard/template.html`
- Modify: `tests/test_dashboard.py`

- [ ] **Step 1: Write the failing render-contract test**

断言生成 HTML 包含“论文结论”“创始人机会看板”“排名”，且不包含 `Founder opportunity terminal`、界面标签 `Rank `；断言 `research_takeaway` 在产品定位字段之前渲染。

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_dashboard.py::test_builds_a_self_contained_interactive_dashboard -q`
Expected: FAIL，缺少中文标签。

- [ ] **Step 3: Implement Chinese labels and ordering**

加入固定分类映射：`agents_workflow → 智能体与工作流`、`infrastructure → 基础设施`、`multimodal → 多模态`、`vertical_ai → 垂直领域 AI`、`general_ai → 通用 AI`。详情页依次渲染论文标题、“论文结论”、产品名称与一句话定位，再渲染评分和商业模块。

- [ ] **Step 4: Rebuild and run tests**

Run: `python scripts/build_dashboard.py && python -m pytest -q`
Expected: HTML 生成成功，全部测试通过。

### Task 4: 浏览器与发布验证

**Files:**
- Regenerate: `dashboard/index.html`

- [ ] **Step 1: Verify locally**

用本地浏览器检查首条项目先显示“论文结论”，搜索、分类、排序、项目切换正常，桌面和手机无横向溢出，控制台无错误。

- [ ] **Step 2: Run full verification**

Run: `python -m pytest -q; python -m compileall -q .; git diff --check`
Expected: 0 failures，0 syntax errors，0 whitespace errors。

- [ ] **Step 3: Publish to target repository**

提交源分支，经 `weekly-paper-radar` subtree 合并到 `alexwang91/paper-finder` 的 `main`，触发 `weekly.yml`，确认线上 HTML 为 21 篇、0 fallback、0 placeholder。
