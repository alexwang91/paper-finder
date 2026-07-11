from __future__ import annotations

from models import Category, Paper

_TEMPLATES: dict[Category, tuple[str, str, list[str], str]] = {
    "agents_workflow": ("面向单一工作流的 AI Agent SaaS", "Turn the method into a narrow workflow copilot.", ["operations teams", "consultants", "SMBs"], "Usage-based subscription"),
    "multimodal": ("多模态内容处理 API", "Package the capability as a media-processing API and review tool.", ["content teams", "e-commerce sellers"], "API credits plus team plans"),
    "vertical_ai": ("垂直行业 AI 助手", "Build a domain-specific assistant with auditable workflows.", ["domain professionals", "specialist firms"], "Per-seat SaaS"),
    "robotics": ("机器人仿真与评测工具", "Offer simulation, testing, or monitoring before hardware deployment.", ["robotics labs", "automation teams"], "Developer subscription"),
    "infrastructure": ("AI 开发者基础设施服务", "Expose the method as an observability, evaluation, or deployment service.", ["AI engineers", "product teams"], "Tiered developer plans"),
    "non_ai_commercial": ("研究驱动的数据产品", "Translate the finding into a focused data or decision-support product.", ["analysts", "specialist operators"], "Report and subscription sales"),
    "general_ai": ("窄场景 AI 效率工具", "Validate one repeatable user job before expanding the product.", ["knowledge workers", "small teams"], "Freemium SaaS"),
}


def product_template(paper: Paper, category: Category) -> dict[str, object]:
    chinese_name, product, users, monetization = _TEMPLATES[category]
    return {
        "business_insight": f"优先把论文能力收窄成一个高频、可衡量的客户任务：{chinese_name}。",
        "product_idea": product,
        "skill_or_agent_idea": f"Create a reusable skill that applies {paper.title} to one customer workflow.",
        "target_users": users,
        "monetization": monetization,
        "risks": "The research result may not transfer to real customer data; validate quality and cost early.",
        "recommended_next_step": "Interview five target users and build one measurable demo within seven days.",
    }

