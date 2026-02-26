"""Bot 工具实现 — 封装现有模块供 Claude Agent 调用。

每个工具函数接收 dict 参数，返回 str 结果（截断到 MAX_RESULT_LEN）。
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

POOL_DIR = PROJECT_ROOT / "content" / "pool"
DRAFTS_DIR = PROJECT_ROOT / "content" / "drafts"
MAX_RESULT_LEN = 8000


def _truncate(text: str) -> str:
    if len(text) <= MAX_RESULT_LEN:
        return text
    return text[:MAX_RESULT_LEN] + f"\n...(已截断，原文 {len(text)} 字符)"


def _find_latest_pool() -> Path | None:
    if not POOL_DIR.exists():
        return None
    pools = sorted(POOL_DIR.glob("*-pool.json"), reverse=True)
    return pools[0] if pools else None


# --- 工具实现 ---

def tool_collect(params: dict) -> str:
    """采集素材：搜索 + 策划。"""
    from collector.search import search
    from collector.planner import plan

    sources_str = params.get("sources", "rss,hn,github,hot,tavily,youtube_api")
    source_list = [s.strip() for s in sources_str.split(",")]
    direction = params.get("direction")
    search_only = params.get("search_only", False)

    pool = search(source_list)
    if search_only:
        return _truncate(json.dumps({
            "status": "ok",
            "date": pool["date"],
            "raw_total": pool["raw_total"],
            "dedup_total": pool["dedup_total"],
        }, ensure_ascii=False))

    pool_path = str(POOL_DIR / f"{pool['date']}-pool.json")
    results = plan(pool_path, direction)

    summary = {
        "status": "ok",
        "date": pool["date"],
        "raw_total": pool["raw_total"],
        "dedup_total": pool["dedup_total"],
        "directions": {},
    }
    for d_name, d_data in results.items():
        top5 = d_data.get("items", [])[:5]
        summary["directions"][d_name] = {
            "label": d_data.get("label", d_name),
            "filtered_count": d_data.get("filtered_count", 0),
            "top5": [{"title": it.get("title", "")[:80], "url": it.get("url", "")} for it in top5],
        }
    return _truncate(json.dumps(summary, ensure_ascii=False, indent=2))


def tool_plan(params: dict) -> str:
    """从素材池按方向筛选打分，推荐选题。"""
    from collector.planner import plan, find_latest_pool

    pool_path = params.get("pool_path") or find_latest_pool()
    if not pool_path:
        return json.dumps({"error": "未找到素材池，请先执行 collect"}, ensure_ascii=False)

    direction = params.get("direction")
    results = plan(str(pool_path), direction)

    summary = {"status": "ok", "pool": str(pool_path), "directions": {}}
    for d_name, d_data in results.items():
        top5 = d_data.get("items", [])[:5]
        summary["directions"][d_name] = {
            "label": d_data.get("label", d_name),
            "filtered_count": d_data.get("filtered_count", 0),
            "score_summary": d_data.get("score_summary", {}),
            "top5": [
                {"title": it.get("title", "")[:80], "url": it.get("url", ""),
                 "score": (it.get("raw_data") or {}).get("score", 0)}
                for it in top5
            ],
        }
    return _truncate(json.dumps(summary, ensure_ascii=False, indent=2))


def tool_check_pool(params: dict) -> str:
    """查看最新素材池概况。"""
    pool_path = _find_latest_pool()
    if not pool_path:
        return json.dumps({"error": "content/pool/ 下没有素材池文件"}, ensure_ascii=False)

    with open(pool_path, encoding="utf-8") as f:
        data = json.load(f)

    items = data.get("items", [])
    preview = [
        {"title": it.get("title", "")[:60], "source": it.get("source_name", ""), "url": it.get("url", "")}
        for it in items[:10]
    ]
    return _truncate(json.dumps({
        "status": "ok",
        "file": pool_path.name,
        "date": data.get("date", ""),
        "total": len(items),
        "raw_total": data.get("raw_total", 0),
        "preview": preview,
    }, ensure_ascii=False, indent=2))


def tool_check_drafts(params: dict) -> str:
    """列出草稿目录中的文件。"""
    if not DRAFTS_DIR.exists():
        return json.dumps({"error": "content/drafts/ 目录不存在"}, ensure_ascii=False)

    files = sorted(DRAFTS_DIR.glob("*.md"), reverse=True)
    file_list = [
        {"name": f.name, "size_kb": round(f.stat().st_size / 1024, 1)}
        for f in files[:20]
    ]
    return _truncate(json.dumps({
        "status": "ok",
        "total": len(files),
        "files": file_list,
    }, ensure_ascii=False, indent=2))


def tool_write(params: dict) -> str:
    """根据选题生成文章草稿。"""
    from generator.writer import generate_article

    topic = params.get("topic", "")
    if not topic:
        return json.dumps({"error": "缺少 topic 参数"}, ensure_ascii=False)

    no_cards = params.get("no_cards", True)  # bot 场景默认不生成卡片
    article_text, article_path = generate_article(topic)

    result = {"status": "ok", "topic": topic, "path": str(article_path), "length": len(article_text)}

    if not no_cards:
        try:
            from generator.card_generator import generate_cards
            from generator.writer import _make_slug, DRAFTS_DIR as GEN_DRAFTS
            date_str = datetime.now().strftime("%Y-%m-%d")
            slug = f"{date_str}-{_make_slug(topic)}"
            cards_path = generate_cards(article_text, slug, GEN_DRAFTS)
            result["cards_path"] = str(cards_path)
        except Exception as e:
            result["cards_error"] = str(e)

    return _truncate(json.dumps(result, ensure_ascii=False, indent=2))


def tool_publish(params: dict) -> str:
    """发布文章到指定平台。"""
    filepath = params.get("filepath", "")
    if not filepath:
        # 尝试找最新草稿
        if DRAFTS_DIR.exists():
            mds = sorted(DRAFTS_DIR.glob("*.md"), reverse=True)
            if mds:
                filepath = str(mds[0])
        if not filepath:
            return json.dumps({"error": "缺少 filepath，且未找到草稿"}, ensure_ascii=False)

    from publisher.main import parse_article, load_config
    from publisher.registry import get_publisher

    # 导入平台模块触发注册
    import publisher.platforms.wechat  # noqa: F401
    import publisher.platforms.bilibili  # noqa: F401
    import publisher.platforms.zhihu  # noqa: F401
    import publisher.platforms.toutiao  # noqa: F401
    import publisher.platforms.xiaohongshu  # noqa: F401
    import publisher.platforms.dongchedi  # noqa: F401

    config = load_config()
    article = parse_article(filepath)

    platforms_str = params.get("platforms", "")
    if platforms_str:
        targets = [p.strip() for p in platforms_str.split(",")]
    else:
        targets = [n for n, c in config.items() if isinstance(c, dict) and c.get("enabled")]

    results = []
    for name in targets:
        try:
            pub = get_publisher(name)
            r = pub.publish(article, config.get(name, {}))
            results.append({"platform": name, "status": r.status.value, "message": r.message})
        except Exception as e:
            results.append({"platform": name, "status": "FAILED", "message": str(e)})

    return _truncate(json.dumps({"status": "ok", "results": results}, ensure_ascii=False, indent=2))


def tool_check_status(params: dict) -> str:
    """查看系统整体状态。"""
    import yaml

    status = {}

    # 素材池
    pool = _find_latest_pool()
    if pool:
        with open(pool, encoding="utf-8") as f:
            pd = json.load(f)
        status["pool"] = {"file": pool.name, "date": pd.get("date"), "count": len(pd.get("items", []))}
    else:
        status["pool"] = None

    # 草稿
    if DRAFTS_DIR.exists():
        mds = list(DRAFTS_DIR.glob("*.md"))
        status["drafts"] = {"count": len(mds), "latest": sorted(mds, reverse=True)[0].name if mds else None}
    else:
        status["drafts"] = {"count": 0}

    # 发布平台
    pub_config = PROJECT_ROOT / "src" / "config" / "publishers.yaml"
    if pub_config.exists():
        with open(pub_config, encoding="utf-8") as f:
            pc = yaml.safe_load(f)
        enabled = [n for n, c in pc.items() if isinstance(c, dict) and c.get("enabled")]
        status["publishers"] = {"enabled": enabled}

    return _truncate(json.dumps(status, ensure_ascii=False, indent=2))


# --- 工具注册表 ---

TOOLS = {
    "collect": tool_collect,
    "plan": tool_plan,
    "check_pool": tool_check_pool,
    "check_drafts": tool_check_drafts,
    "write": tool_write,
    "publish": tool_publish,
    "check_status": tool_check_status,
}


def execute_tool(name: str, params: dict) -> str:
    """执行指定工具，返回结果字符串。"""
    fn = TOOLS.get(name)
    if not fn:
        return json.dumps({"error": f"未知工具: {name}"}, ensure_ascii=False)
    try:
        return fn(params)
    except Exception as e:
        return json.dumps({"error": f"工具 {name} 执行失败: {e}"}, ensure_ascii=False)
