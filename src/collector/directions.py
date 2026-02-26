"""方向配置 — 定义不同内容方向的权重、关键词和筛选规则。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Set


@dataclass
class Direction:
    """一个内容方向的完整配置。"""
    name: str                           # tech_ai / auto
    label: str                          # "AI 科技" / "汽车"
    categories: Set[str]                # 该方向关注的 category
    source_weight: Dict[str, int]       # 来源 → 基础分
    category_weight: Dict[str, int]     # 分类 → 基础分
    keyword_bonus: Dict[str, float]     # 关键词 → 加分
    preferred_sources: Set[str]         # 偏好来源，额外加分
    preferred_source_bonus: int = 3


TECH_AI = Direction(
    name="tech_ai",
    label="AI 科技",
    categories={"tech_ai", "trending"},
    source_weight={
        "Hacker News": 25,
        "GitHub Trending": 24,
        "OpenAI Blog": 22,
        "Anthropic Blog": 22,
        "Google DeepMind Blog": 22,
        "微博热搜": 14,
        "百度热搜": 14,
    },
    category_weight={
        "tech_ai": 18,
        "trending": 10,
        "auto": 4,
    },
    keyword_bonus={
        "agent": 4, "llm": 4, "模型": 4, "openai": 5, "anthropic": 4,
        "deepmind": 4, "机器人": 4, "开源": 3, "gpu": 3, "transformer": 4,
        "rag": 3, "ai": 3, "gpt": 3, "claude": 3, "gemini": 3,
    },
    preferred_sources={"Hacker News", "GitHub Trending", "OpenAI Blog",
                       "Anthropic Blog", "Google DeepMind Blog"},
)

TECH_AI_TRENDING_KEYWORDS = {
    "ai", "llm", "gpt", "openai", "anthropic", "deepmind", "模型", "机器人",
    "agent", "transformer", "开源", "gpu", "芯片", "算力", "大模型",
    "claude", "gemini", "copilot", "编程", "程序员", "开发者",
}

AUTO = Direction(
    name="auto",
    label="汽车",
    categories={"auto", "trending"},
    source_weight={
        "微博热搜": 20,
        "百度热搜": 20,
        "Hacker News": 8,
        "GitHub Trending": 8,
        "OpenAI Blog": 6,
        "Anthropic Blog": 6,
        "Google DeepMind Blog": 6,
    },
    category_weight={
        "auto": 18,
        "trending": 10,
        "tech_ai": 4,
    },
    keyword_bonus={
        "自动驾驶": 5, "新能源": 4, "电动车": 4, "智驾": 5, "比亚迪": 3,
        "特斯拉": 3, "销量": 3, "补贴": 3, "充电": 3, "懂车帝": 3,
        "汽车之家": 3, "蔚来": 3, "理想": 3, "小鹏": 3, "华为": 3,
        "问界": 3, "小米汽车": 3,
    },
    preferred_sources={"微博热搜", "百度热搜"},
)

AUTO_TRENDING_KEYWORDS = {
    "自动驾驶", "新能源", "电动车", "智驾", "比亚迪", "特斯拉", "销量",
    "补贴", "充电", "懂车帝", "汽车之家", "蔚来", "理想", "小鹏",
    "华为", "问界", "小米汽车", "车", "驾驶", "油价", "电池",
}

# 方向注册表
DIRECTIONS: Dict[str, Direction] = {
    "tech_ai": TECH_AI,
    "auto": AUTO,
}

# 方向对应的 trending 关键词（用于从热搜中二次筛选）
TRENDING_KEYWORDS: Dict[str, set] = {
    "tech_ai": TECH_AI_TRENDING_KEYWORDS,
    "auto": AUTO_TRENDING_KEYWORDS,
}


def get_direction(name: str) -> Direction:
    """按名称获取方向配置，不存在则 KeyError。"""
    return DIRECTIONS[name]
