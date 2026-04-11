"""Agent — Claude 主力 + Gemini 备选的双模型 fallback 架构。

handle_message() 先尝试 Claude，超时或异常后自动切换 Gemini。
"""

import json
import os

from bot.tools import execute_tool

# --- Claude 配置 ---
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY", "") or os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_BASE_URL = os.getenv("CLAUDE_BASE_URL", "")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "") or "claude-sonnet-4-20250514"
CLAUDE_TIMEOUT = int(os.getenv("CLAUDE_TIMEOUT", "60"))

# --- Gemini 配置 ---
GEMINI_API_KEY = (
    os.getenv("GEMINI_API_KEY", "")
    or os.getenv("GOOGLE_API_KEY", "")
    or os.getenv("YOUTUBE_API_KEY", "")
)
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "") or "gemini-2.5-flash"

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
                    "description": "采集源，逗号分隔。可选: follow_builders,rss,hn,github,hot,tavily,youtube_api,twitter。默认每日来源。",
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


# ============================================================
# Claude 调用逻辑
# ============================================================

def _build_claude_client():
    import anthropic
    kwargs = {"api_key": CLAUDE_API_KEY, "timeout": CLAUDE_TIMEOUT}
    if CLAUDE_BASE_URL:
        kwargs["base_url"] = CLAUDE_BASE_URL
    return anthropic.Anthropic(**kwargs)


def _claude_tool_defs() -> list[dict]:
    """将 TOOL_DEFINITIONS 转为 Claude tools 格式。"""
    return [
        {
            "name": t["name"],
            "description": t["description"],
            "input_schema": t["input_schema"],
        }
        for t in TOOL_DEFINITIONS
    ]


def _handle_claude(text: str) -> str:
    """用 Claude API 处理消息，支持 tool loop。"""
    client = _build_claude_client()
    tools = _claude_tool_defs()
    messages = [{"role": "user", "content": text}]

    for _ in range(MAX_TOOL_ROUNDS):
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=tools,
            messages=messages,
        )

        # 提取文本和工具调用
        text_parts: list[str] = []
        tool_uses: list[dict] = []
        for block in response.content:
            if block.type == "text":
                text_parts.append(block.text)
            elif block.type == "tool_use":
                tool_uses.append({"id": block.id, "name": block.name, "input": block.input})

        if not tool_uses:
            return "\n".join(text_parts) if text_parts else "（无回复内容）"

        # 执行工具并构造 tool_result
        messages.append({"role": "assistant", "content": response.content})
        tool_results = []
        for tu in tool_uses:
            print(f"  [Claude Tool] {tu['name']}({json.dumps(tu['input'], ensure_ascii=False)})")
            result = execute_tool(tu["name"], tu["input"])
            print(f"  [Claude Tool] {tu['name']} → {len(result)} chars")
            tool_results.append({"type": "tool_result", "tool_use_id": tu["id"], "content": result})
        messages.append({"role": "user", "content": tool_results})

    return "工具调用轮次已达上限（10轮），请简化请求后重试。"


# ============================================================
# Gemini 调用逻辑
# ============================================================

def _build_gemini_client():
    from google import genai
    return genai.Client(api_key=GEMINI_API_KEY)


def _build_gemini_tools():
    from google.genai import types
    declarations = []
    for tool in TOOL_DEFINITIONS:
        declarations.append(
            types.FunctionDeclaration(
                name=tool["name"],
                description=tool["description"],
                parameters_json_schema=tool["input_schema"],
            )
        )
    return [types.Tool(function_declarations=declarations)]


def _handle_gemini(text: str) -> str:
    """用 Gemini API 处理消息，支持 tool loop。"""
    from google.genai import types

    if not GEMINI_API_KEY:
        return "错误：Claude 和 Gemini 均不可用（未配置 GEMINI_API_KEY）"

    client = _build_gemini_client()
    tools = _build_gemini_tools()
    contents: list[types.Content] = [
        types.Content(role="user", parts=[types.Part.from_text(text=text)])
    ]

    for _ in range(MAX_TOOL_ROUNDS):
        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    tools=tools,
                    temperature=0.2,
                    max_output_tokens=4096,
                ),
            )
        except Exception as e:
            return f"Gemini API 调用失败: {e}"

        candidate = response.candidates[0] if getattr(response, "candidates", None) else None
        model_content = candidate.content if candidate else None
        if not model_content:
            return "（无回复内容）"

        text_parts: list[str] = []
        tool_uses = []
        for part in model_content.parts or []:
            if part.text:
                text_parts.append(part.text)
            if part.function_call:
                tool_uses.append(part.function_call)

        if not tool_uses:
            return "\n".join(text_parts) if text_parts else "（无回复内容）"

        contents.append(model_content)
        response_parts = []
        for tool_use in tool_uses:
            tool_input = dict(tool_use.args or {})
            print(f"  [Gemini Tool] {tool_use.name}({json.dumps(tool_input, ensure_ascii=False)})")
            result = execute_tool(tool_use.name, tool_input)
            print(f"  [Gemini Tool] {tool_use.name} → {len(result)} chars")
            response_parts.append(
                types.Part.from_function_response(
                    name=tool_use.name,
                    response={"result": result},
                )
            )
        contents.append(types.Content(role="user", parts=response_parts))

    return "工具调用轮次已达上限（10轮），请简化请求后重试。"


# ============================================================
# 入口：Claude 优先，失败 fallback Gemini
# ============================================================

def handle_message(text: str) -> str:
    """处理用户消息：先尝试 Claude，失败后 fallback 到 Gemini。"""
    if CLAUDE_API_KEY:
        try:
            print("  [Agent] 使用 Claude 处理...")
            return _handle_claude(text)
        except Exception as e:
            print(f"  [Agent] Claude 失败，切换 Gemini: {e}")

    if GEMINI_API_KEY:
        print("  [Agent] 使用 Gemini 处理...")
        return _handle_gemini(text)

    return "错误：未配置任何 AI API Key（CLAUDE_API_KEY 或 GEMINI_API_KEY）"
