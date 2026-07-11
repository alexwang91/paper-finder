# Weekly Paper Commercial Radar

每周自动发现研究论文，以商业价值和独立开发者可执行性为核心选出 21 篇，并生成周报、排名表和 7 天社媒内容。

它不是学术影响力排行榜。评分优先考虑论文能否变成 AI Skill、Agent、Micro SaaS、API、浏览器插件、垂直工作流或数据产品。

## 能做什么

完整流程为：

1. 从 arXiv、Semantic Scholar、Hugging Face Papers 和 Papers with Code 收集近期候选。
2. 用 GitHub 搜索关联实现，补充代码地址、Star 和主要语言。
3. 按标准化标题、规范化 URL 和相似标题去重，并合并来源元数据。
4. 使用 OpenAI Structured Outputs 或本地启发式规则生成商业分析和七维评分。
5. 保证默认榜单恰好 21 篇、AI 论文至少 70%，并控制窄主题集中度。
6. 生成排名 CSV、Markdown 周报、原始 JSON 和恰好 21 行的社媒排期 CSV。

单个来源失败不会中断其他来源。没有 OpenAI 密钥时，系统自动降级到确定性评分和文案模板。

## 项目结构

```text
main.py                         CLI 入口
pipeline.py                     抓取、去重、分析、选择和输出编排
models.py                       Pydantic 领域模型
config_loader.py                YAML、环境变量和 CLI 配置
deduplication.py                论文去重及元数据合并
selection.py                    主题多样化与 21 篇选择
reporting.py                    JSON、CSV 和 Markdown 输出
sources/                        五类数据源适配器
scoring/                        启发式和 OpenAI 分析
generation/                     摘要、产品方向和社媒内容
scheduler/weekly_job.py         APScheduler 周任务
scripts/generate_demo.py        不联网的确定性演示
examples/demo_candidates.json   25 条明确标记的虚构演示候选
tests/                          离线测试和来源 fixtures
```

## 安装

需要 Python 3.11 或更高版本。

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

## 配置密钥

编辑 `.env`：

```text
OPENAI_API_KEY=
SEMANTIC_SCHOLAR_API_KEY=
GITHUB_TOKEN=
NOTION_API_KEY=
NOTION_DATABASE_ID=
```

所有密钥都是可选的：

- 没有 `OPENAI_API_KEY`：使用启发式分析。
- 没有 `SEMANTIC_SCHOLAR_API_KEY`：使用公开限额。
- 没有 `GITHUB_TOKEN`：使用 GitHub 公开限额，关联仓库数量可能受限。
- Notion 字段预留，本项目当前通过 Notion/Airtable 可直接导入的 CSV 交付，不主动写入第三方数据库。

运行参数、关键词、来源开关、评分权重和发布时间都在 `config.yaml` 中。优先级为 CLI 覆盖 YAML；密钥只从环境变量读取。

## 手动运行

```bash
python main.py --days-back 7 --final-count 21
python main.py --week-start 2026-07-06 --week-end 2026-07-12
python main.py --no-llm
python main.py --output-format csv markdown
python main.py --max-candidates 120 --output-dir outputs
python main.py --config config.yaml
```

显式 `--week-start` 与 `--week-end` 优先于 `--days-back`，两者必须一起提供且不能倒置。

如果 `--final-count` 不是 21，排名表遵循该参数；社媒日历仍使用 21 篇结构，因为固定排期要求 7 天 × 3 篇。正常周报建议保持默认值 21。

## 不联网演示

演示数据使用 `example.com` 链接并标记为 `demo_fixture`，不会被误认为真实论文：

```bash
python scripts/generate_demo.py --output-dir outputs --report-date 2026-07-12
```

这条命令会通过真实的去重、启发式分析、选择、报告和排期代码生成四个示例文件，不访问网络，也不调用 LLM。

## 输出文件

每次运行以报告结束日期命名：

```text
outputs/raw_candidates_YYYY-MM-DD.json
outputs/weekly_paper_rank_YYYY-MM-DD.csv
outputs/weekly_report_YYYY-MM-DD.md
outputs/social_calendar_YYYY-MM-DD.csv
```

- 原始 JSON：去重后的候选及全部来源元数据。
- 排名 CSV：论文、商业分析、七项评分、代码链接、LLM 状态和置信度。
- Markdown 周报：趋势摘要、Top 21、逐篇分析、Top 5 创业机会和 10 个内容角度。
- 社媒 CSV：周一到周日每天三篇，含 X 短帖、六段 Thread、小红书标题/正文/标签和英文封面提示词。

CSV 使用 UTF-8 BOM，Excel 可直接显示中文，也能导入 Notion 和 Airtable。

## 评分模型

每个维度为 0–100，总分由本地代码重新计算：

```text
technical_novelty            × 0.15
commercial_potential         × 0.25
solo_founder_feasibility     × 0.20
market_need                  × 0.15
mvp_speed                    × 0.10
virality                     × 0.10
moat                         × 0.05
```

LLM 不能直接决定最终总分，避免模型算术错误或越权改变权重。无 LLM 时，规则会综合关键词、商业语义、代码/演示、GitHub/Hugging Face 热度、引用、资源要求和数据资产。

`llm_analysis_status` 有三种值：

- `completed`：结构化 LLM 分析成功。
- `failed_fallback`：该篇 LLM 调用失败，已回退规则分析。
- `failed_or_skipped`：使用 `--no-llm` 或没有密钥。

## 每周自动运行

### APScheduler

```bash
python -m scheduler.weekly_job
```

默认按 `Europe/Budapest` 时区每周一 07:00 运行。进程必须常驻。

### GitHub Actions

`.github/workflows/weekly.yml` 每周一运行，也支持手动触发。把可选密钥加入仓库 Secrets。工作流会生成输出；有变化时提交回当前分支，无变化时正常结束。

GitHub cron 使用 UTC，因此夏令时切换时本地时间可能相差一小时。需要严格本地时间时，使用 APScheduler 或调整 cron。

## 测试

所有自动测试不访问网络：

```bash
python -m pytest -q
python -m compileall -q .
```

来源测试使用本地 Atom、JSON 和 HTML fixtures；流水线测试使用依赖注入的假来源；OpenAI 失败测试使用假客户端。

## 数据源行为和限制

- arXiv 与 Semantic Scholar 是主要候选来源。
- Hugging Face Papers 使用官方 `huggingface_hub` 客户端。
- GitHub 是代码元数据增强器，只有标题或 arXiv ID 足够相关时才关联仓库，避免把普通热门项目当作论文实现。
- Papers with Code 使用公开 API 并提供 HTML 解析回退；上游接口或页面变化时可能被安全跳过。
- 公开 API 有限流。配置 token 能提高 GitHub/Semantic Scholar 的稳定性，但不能保证上游服务可用。
- 论文商业评分是发现工具，不是市场事实。定价、客户需求、合规性和技术效果仍需访谈与真实数据验证。
- 当成功来源提供的唯一论文不足 21 篇时，系统以低置信度占位行补齐结构，并明确说明它不是真实论文；所有来源都失败时则返回非零退出码，不生成虚假成功报告。

## 常见问题

**运行后没有报告**

查看日志中的来源错误。若所有来源失败，检查网络、代理和上游限流。

**OpenAI 调用失败**

单篇失败会自动回退。也可以显式运行 `python main.py --no-llm`。

**GitHub 没有关联到代码**

这是保守设计。没有足够标题或 arXiv ID 相关性时，系统宁可保持 `code_url` 为空。

**想换模型**

修改 `config.yaml` 的 `llm.model`。模型必须支持 Structured Outputs，并与当前 OpenAI Python SDK 兼容。
