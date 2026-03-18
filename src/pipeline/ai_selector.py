"""AI 选题评估器 — 让 Claude 分析推荐选题并选择最佳选题。

用法:
    from pipeline.ai_selector import select_best_topic

    topics = [
        {"title": "选题1", "score": 85, "reason": "...", "source_urls": [...]},
        {"title": "选题2", "score": 90, "reason": "...", "source_urls": [...]},
    ]

    selected = select_best_topic(topics, direction="tech_ai")
    print(selected["title"])
"""

from typing import Optional


def select_best_topic(topics: list[dict], direction: str = "tech_ai") -> Optional[dict]:
    """让 Claude 分析推荐选题并选择最佳选题

    Args:
        topics: AI 推荐的选题列表，每个选题包含 title, score, reason, source_urls
        direction: 内容方向（tech_ai / auto）

    Returns:
        选中的选题 dict，如果没有合适选题则返回 None
    """
    if not topics:
        return None

    # 如果只有一个选题，直接返回
    if len(topics) == 1:
        return topics[0]

    try:
        from generator.gemini_client import generate_text
    except ImportError:
        # 如果无法导入 AI 客户端，返回评分最高的选题
        return max(topics, key=lambda t: t.get("score", 0))

    # 准备选题摘要
    topics_summary = []
    for i, topic in enumerate(topics, 1):
        topics_summary.append(
            f"{i}. **{topic['title']}** (评分: {topic.get('score', 0)})\n"
            f"   推荐理由: {topic.get('reason', '无')[:200]}\n"
            f"   关联素材数: {len(topic.get('source_urls', []))}"
        )

    direction_label = "AI 科技" if direction == "tech_ai" else "汽车"

    prompt = f"""你是一位资深内容策划师。以下是 {direction_label} 方向的 {len(topics)} 个推荐选题：

{chr(10).join(topics_summary)}

请分析这些选题，选择**最值得写**的一个。评估标准：
1. **时效性**：是否是当下热点，时效性强的优先
2. **话题热度**：是否有足够的讨论度和关注度
3. **内容深度**：是否有足够的素材支撑深度内容
4. **差异化**：是否有独特角度，避免同质化
5. **读者价值**：是否能给读者带来实际价值

请直接输出你选择的选题序号（1-{len(topics)}），并简要说明理由（1-2 句话）。

输出格式：
选择: N
理由: [简要说明]
"""

    try:
        result = generate_text(prompt, task="summary", temperature=0.3)

        # 解析选择结果
        import re
        match = re.search(r'选择[：:]\s*(\d+)', result)
        if match:
            choice_idx = int(match.group(1)) - 1
            if 0 <= choice_idx < len(topics):
                selected = topics[choice_idx]

                # 提取理由
                reason_match = re.search(r'理由[：:]\s*(.+)', result, re.DOTALL)
                if reason_match:
                    ai_reason = reason_match.group(1).strip()
                    selected['ai_selection_reason'] = ai_reason

                return selected

        # 如果解析失败，返回评分最高的
        return max(topics, key=lambda t: t.get("score", 0))

    except Exception as e:
        print(f"  ⚠ AI 选题失败: {e}，使用评分最高的选题")
        return max(topics, key=lambda t: t.get("score", 0))


def select_best_topic_from_plan_result(plan_result: dict, direction: str = "tech_ai") -> Optional[dict]:
    """从 plan_result 中提取推荐选题并选择最佳选题

    Args:
        plan_result: planner.py 返回的策划结果
        direction: 内容方向

    Returns:
        选中的选题 dict，包含 title, score, reason, source_urls
    """
    # 从 plan_result 中提取指定方向的选题
    direction_data = plan_result.get(direction, {})
    items = direction_data.get("items", [])

    if not items:
        return None

    # 如果有 AI 推荐的选题（从 Notion 或其他来源），优先使用
    # 否则从 Top 素材中构造选题
    topics = []

    # 取 Top 3 素材作为候选选题
    for item in items[:3]:
        topics.append({
            "title": item.get("title", ""),
            "score": (item.get("raw_data") or {}).get("score", 0),
            "reason": item.get("summary", "")[:200],
            "source_urls": [item.get("url", "")],
        })

    return select_best_topic(topics, direction)
