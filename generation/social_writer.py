from __future__ import annotations

from datetime import date, timedelta

from models import RankedPaper, SocialCalendarEntry

RANK_MATRIX = [
    [1, 8, 15],
    [2, 9, 16],
    [3, 10, 17],
    [4, 11, 18],
    [5, 12, 19],
    [6, 13, 20],
    [7, 14, 21],
]
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def _x_post(item: RankedPaper) -> tuple[str, str]:
    hashtags = "#AIResearch #IndieHackers #BuildInPublic"
    product = item.analysis.product_idea or "a focused product for one workflow"
    post = (
        f"Paper #{item.rank} worth watching: {item.paper.title}. "
        f"Founder angle: turn it into {product.lower()}. Validate one painful use case first. "
        f"{hashtags}"
    )
    if len(post) > 280:
        post = f"Paper #{item.rank}: {item.paper.title[:80]}. Founder angle: {product[:80]}. Validate one painful use case first. {hashtags}"
    return post[:280], hashtags


def _thread(item: RankedPaper) -> str:
    return "\n\n".join([
        f"1/ New research with a founder angle: {item.paper.title}",
        f"2/ What it does: {item.analysis.abstract_summary_en or item.analysis.key_innovation or 'It introduces a new method.'}",
        f"3/ Why it matters: {item.analysis.why_it_matters or 'It could simplify a repeated workflow.'}",
        f"4/ Product opportunity: {item.analysis.product_idea or 'Build a narrow workflow product.'}",
        f"5/ Solo-founder MVP: test one user, one input, and one measurable output in two weeks.",
        f"6/ Risk and takeaway: {item.analysis.risks or 'Research quality may not transfer to production.'} Start with evidence, not hype.",
    ])


def _xiaohongshu(item: RankedPaper) -> tuple[str, str, str]:
    titles = "｜".join([
        f"这篇论文可能藏着一个小而美 SaaS 机会",
        f"一个人也能验证的 AI 产品方向：{item.paper.title[:18]}",
        "本周最值得产品经理看的研究机会",
    ])
    body = (
        f"📄 今天看的是：{item.paper.title}\n\n"
        f"✨ 为什么值得关注\n{item.analysis.why_it_matters or '它可能把复杂能力变成更容易使用的工作流。'}\n\n"
        f"👥 适合谁\n{('、'.join(item.analysis.target_users) if item.analysis.target_users else 'AI 产品经理、独立开发者、小团队')}\n\n"
        f"🛠️ 可以做成什么产品\n{item.analysis.product_idea or '先做一个只解决单一高频问题的工具。'}\n\n"
        f"⚠️ 别急着追热点：{item.analysis.risks or '先用真实用户和真实数据验证效果。'}"
    )
    return titles, body, "#AI创业 #独立开发 #论文商业化 #效率工具"


def build_social_calendar(
    ranked: list[RankedPaper],
    monday: date,
    x_times: list[str],
    xiaohongshu_times: list[str],
) -> list[SocialCalendarEntry]:
    if len(x_times) != 3 or len(xiaohongshu_times) != 3:
        raise ValueError("social schedules require exactly three time slots per platform")
    by_rank = {item.rank: item for item in ranked}
    missing = [rank for rank in range(1, 22) if rank not in by_rank]
    if missing:
        raise ValueError(f"social calendar requires ranks 1-21; missing {missing}")
    rows: list[SocialCalendarEntry] = []
    for day_index, ranks in enumerate(RANK_MATRIX):
        publish_date = monday + timedelta(days=day_index)
        for slot, rank in enumerate(ranks):
            item = by_rank[rank]
            x_post, x_hashtags = _x_post(item)
            titles, body, tags = _xiaohongshu(item)
            rows.append(SocialCalendarEntry(
                date=publish_date,
                weekday=WEEKDAYS[day_index],
                rank=rank,
                paper_title=item.paper.title,
                paper_url=item.paper.url,
                x_post_time=x_times[slot],
                x_post=x_post,
                x_thread=_thread(item),
                x_hashtags=x_hashtags,
                xiaohongshu_post_time=xiaohongshu_times[slot],
                xiaohongshu_title=titles,
                xiaohongshu_body=body,
                xiaohongshu_tags=tags,
                image_prompt=(
                    "Clean editorial tech cover, modern startup product mood, subtle data visualization, "
                    f"concept inspired by {item.analysis.category.replace('_', ' ')}, futuristic but not sci-fi, "
                    "blue and warm orange accents, generous whitespace, no text, vertical 3:4 composition"
                ),
            ))
    return rows
