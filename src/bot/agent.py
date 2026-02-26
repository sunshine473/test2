"""Claude Agent — 接收用户消息，通过 tool use 调用项目工具，返回最终回复。

使用 anthropic SDK，支持 base_url 中转。Tool loop 最多 10 轮。
"""

import json
import os

import anthropic

from bot.tools import execute_tool

CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY", "")
CLAUDE_BASE_URL = os.getenv("CLAUDE_BASE_URL", "")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "") or "claude-sonnet-4-20250514"
MAX_TOOL_ROUNDS = 10

SYSTEM_PROMPT = """你是一个内容工厂助手 Bot，帮助用户管理从素材采集到内容发布的全流程。

你可以使用以下工具：
- collect: 采集素材（搜索+策划），支持指定采集源和方向
- plan: 从已有素材池筛选打分推荐选题
- check_pool: 查看最新素材池概况
- check_drafts: 查看草稿列表
- write: 根据选题生成文章草稿
- publish: 发布文章到各平台
- check_status: 查看系统整体状态

交互风格：
- 用中文回复，简洁友好
- 主动汇报工具执行结果
- 如果操作耗时较长（如采集），先告知用户正在执行
- 遇到错误时给出可行的建议"""

TOOL_DEFINITIONS = [
    {
        "name": "collect",
        "description": "采集素材：从多个信息源搜索+去重+策划推荐。耗时较长（1-3分钟）。",
        "input_schema": {
            "type": "object",
            "properties": {
                "sources": {
                    "type": "string",
                    "description": "采集源，逗号分隔。可选: rss,hn,github,hot,tavily,youtube_api,twitter。默认全部。",
                },
                "direction": {
                    "type": "string",
                    "enum": ["tech_ai", "auto"],
                    "description": "指定方向：tech_ai(AI科技) 或 auto(汽车)。不传则两个方向都跑。",
                },
                "search_only": {
                    "type": "boolean",
                    "description": "仅搜索不策划，默认 false",
                },
            },
        },
    },
    {
        "name": "plan",
        "description": "从已有素材池按方向筛选打分，推荐选题 Top5。",
        "input_schema": {
            "type": "object",
            "properties": {
                "direction": {
                    "type": "string",
                    "enum": ["tech_ai", "auto"],
                    "description": "指定方向，不传则两个方向都跑",
                },
                "pool_path": {
                    "type": "string",
                    "description": "素材池 JSON 路径，不传则自动取最新",
                },
            },
        },
    },
    {
        "name": "check_pool",
        "description": "查看最新素材池：日期、条数、前10条摘要。",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "check_drafts",
        "description": "列出 content/drafts/ 下的草稿文件。",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "write",
        "description": "根据选题生成 Markdown 文章草稿。",
        "input_schema": {
            "type": "object",
            "properties": {
                "topic": {"type": "string", "description": "选题标题（必填）"},
                "no_cards": {"type": "boolean", "description": "不生成卡片，默认 true"},
            },
            "required": ["topic"],
        },
    },
    {
        "name": "publish",
        "description": "发布文章到各平台（微信公众号、B站、知乎等）。",
        "input_schema": {
            "type": "object",
            "properties": {
                "filepath": {"type": "string", "description": "Markdown 文件路径，不传则取最新草稿"},
                "platforms": {"type": "string", "description": "目标平台，逗号分隔。不传则发布到所有已启用平台。"},
            },
        },
    },
    {
        "name": "check_status",
        "description": "查看系统整体状态：素材池、草稿数、已启用发布平台。",
        "input_schema": {"type": "object", "properties": {}},
    },
]


def _build_client() -> anthropic.Anthropic:
    kwargs = {"api_key": CLAUDE_API_KEY}
    if CLAUDE_BASE_URL:
        kwargs["base_url"] = CLAUDE_BASE_URL
    return anthropic.Anthropic(**kwargs)


def handle_message(text: str) -> str:
    """处理用户消息：发给 Claude，执行 tool loop，返回最终文本回复。"""
    if not CLAUDE_API_KEY:
        return "错误：未配置 CLAUDE_API_KEY"

    client = _build_client()
    messages = [{"role": "user", "content": text}]

    for round_num in range(MAX_TOOL_ROUNDS):
        try:
            response = client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                tools=TOOL_DEFINITIONS,
                messages=messages,
            )
        except Exception as e:
            return f"Claude API 调用失败: {e}"

        # 提取文本和工具调用
        text_parts = []
        tool_uses = []
        for block in response.content:
            if block.type == "text":
                text_parts.append(block.text)
            elif block.type == "tool_use":
                tool_uses.append(block)

        # 没有工具调用 → 返回最终回复
        if response.stop_reason == "end_turn" or not tool_uses:
            return "\n".join(text_parts) if text_parts else "（无回复内容）"

        # 执行工具调用
        messages.append({"role": "assistant", "content": response.content})

        tool_results = []
        for tool_use in tool_uses:
            print(f"  [Tool] {tool_use.name}({json.dumps(tool_use.input, ensure_ascii=False)})")
            result = execute_tool(tool_use.name, tool_use.input)
            print(f"  [Tool] {tool_use.name} → {len(result)} chars")
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tool_use.id,
                "content": result,
            })

        messages.append({"role": "user", "content": tool_results})

    return "工具调用轮次已达上限（10轮），请简化请求后重试。"
