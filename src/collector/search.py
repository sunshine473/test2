"""搜索阶段入口 — 采集 + 整理层输出素材池 JSON + Notion 同步（不含打分）。

用法:
    python -m collector.search                          # 默认源
    python -m collector.search --sources hn,github      # 指定源
    python -m collector.search --output path/to/out.json
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# 确保项目根目录在 sys.path 中
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from dotenv import load_dotenv
load_dotenv()

from collector.main import load_config, collect_all, ensure_utf8, parse_sources_arg
from normalizer.main import normalize, save_material_pool

POOL_DIR = PROJECT_ROOT / "content" / "pool"


def search(sources: list[str], output_path: str | None = None) -> dict:
    """执行搜索阶段：采集 → 去重聚类 → 输出素材池 JSON → Notion 同步。"""
    ensure_utf8()
    config = load_config()

    print(f"=== 素材搜索开始 ({datetime.now().strftime('%Y-%m-%d %H:%M')}) ===")
    print(f"采集源: {', '.join(sources)}\n")

    raw_items, stats = collect_all(config, sources)
    print(f"\n=== 原始采集 {len(raw_items)} 条 ===")
    print(f"分源统计: {' | '.join(f'{k}: {v} 条' for k, v in stats.items())}")
    print(f"\n开始整理层处理...")
    pool_model = normalize(raw_items, stats)
    dedup_items = [item.to_collected_item() for item in pool_model.items]
    cluster_summary = pool_model.cluster_summary
    print(
        f"整理后 {len(dedup_items)} 条，聚类 {cluster_summary['cluster_count']} 组，"
        f"最大簇 {cluster_summary['max_cluster_size']} 条"
    )
    pool = pool_model.to_dict()
    pool["stage"] = "search"

    if not output_path:
        POOL_DIR.mkdir(parents=True, exist_ok=True)
        output_path = str(POOL_DIR / f"{pool['date']}-pool.json")

    save_material_pool(pool_model, output_path)
    # 对外仍保持 search 阶段标识，避免旧调用方受影响。
    Path(output_path).write_text(json.dumps(pool, indent=2, ensure_ascii=False), encoding="utf-8")
    pool["_output_path"] = output_path
    print(f"\n素材池已保存: {output_path}")

    # Notion 同步（不含打分）
    if os.getenv("NOTION_API_KEY") and os.getenv("NOTION_DATABASE_ID"):
        print(f"\n[Notion] 正在写入 {len(dedup_items)} 条素材...")
        try:
            from collector.notion_output import NotionOutput
            notion = NotionOutput()
            saved = notion.save(dedup_items)
            print(f"[Notion] 成功写入 {saved}/{len(dedup_items)} 条")
            pool["notion_saved"] = saved
        except Exception as e:
            print(f"[Notion] 写入失败: {e}")
            pool["notion_error"] = str(e)
    else:
        print("\n[Notion] 未配置凭据，跳过同步")

    print(f"\n=== 搜索完成，素材池 {len(dedup_items)} 条 ===")
    return pool


def main():
    parser = argparse.ArgumentParser(description="素材搜索（采集+去重，不含打分）")
    parser.add_argument(
        "--sources",
        default="rss,hn,github,hot,tavily,youtube_api",
        help="要采集的信息源，逗号分隔",
    )
    parser.add_argument("--output", default=None, help="素材池 JSON 输出路径")
    args = parser.parse_args()

    try:
        source_list = parse_sources_arg(args.sources)
    except ValueError as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)
    pool = search(source_list, args.output)
    print(json.dumps(pool, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
