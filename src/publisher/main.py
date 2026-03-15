"""发布调度入口

用法:
    python src/publisher/main.py content/drafts/2026-02-20-xxx.md
    python src/publisher/main.py content/drafts/2026-02-20-xxx.md --platforms wechat,bilibili
"""

import argparse
import os
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(PROJECT_ROOT / "src" / "wechat_publisher" / ".env")  # 兼容旧版微信配置

import yaml
from packager.common import extract_images_from_cards_html
from packager.main import build_publish_packages, load_draft_package, package_to_article, parse_article
from publisher.registry import get_publisher, list_publishers

# 导入平台模块以触发 @register 装饰器
import publisher.platforms.wechat  # noqa: F401
import publisher.platforms.bilibili  # noqa: F401
import publisher.platforms.zhihu  # noqa: F401
import publisher.platforms.toutiao  # noqa: F401
import publisher.platforms.xiaohongshu  # noqa: F401
import publisher.platforms.dongchedi  # noqa: F401


def load_config() -> dict:
    config_path = PROJECT_ROOT / "src" / "config" / "publishers.yaml"
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)

def suggest_platforms(article) -> list[str]:
    """根据文章内容推荐平台组合"""
    try:
        from generator.gemini_client import generate_text
    except ImportError:
        return []

    # 提取文章特征
    content_sample = article.content[:1000]
    tags_str = ", ".join(article.tags) if article.tags else "无"

    prompt = f"""根据以下文章特征，推荐最适合的发布平台组合。

标题: {article.title}
标签: {tags_str}
内容摘要: {content_sample}

可选平台：
- wechat: 微信公众号（适合所有内容）
- zhihu: 知乎（适合深度技术文、观点文）
- xiaohongshu: 小红书（适合轻量资讯、盘点、生活化内容）
- toutiao: 今日头条（适合热点评论、资讯）
- dongchedi: 懂车帝（适合汽车/出行相关）
- bilibili: B站（适合视频内容，目前仅骨架）

请输出推荐的平台列表（逗号分隔）和推荐理由。

输出格式：
platforms: wechat,zhihu,xiaohongshu
reason: ...
"""

    try:
        result = generate_text(prompt, task="summary", temperature=0.3)
        # 解析输出
        platforms_match = re.search(r"platforms:\s*(.+)", result)
        reason_match = re.search(r"reason:\s*(.+)", result, re.DOTALL)

        if platforms_match:
            platforms = [p.strip() for p in platforms_match.group(1).split(",")]
            reason = reason_match.group(1).strip() if reason_match else "AI 推荐"
            return platforms, reason
        return [], "解析失败"
    except Exception as e:
        return [], f"推荐失败: {str(e)[:100]}"


def main():
    parser = argparse.ArgumentParser(description="内容发布器")
    parser.add_argument("filepath", help="Markdown 文件路径")
    parser.add_argument("--platforms", default=None, help="目标平台，逗号分隔（默认发布到所有 enabled 平台）")
    parser.add_argument("--suggest", action="store_true", help="AI 推荐平台（不执行发布）")
    args = parser.parse_args()

    config = load_config()
    try:
        draft = load_draft_package(args.filepath)
        article = parse_article(args.filepath)
    except FileNotFoundError as e:
        print(str(e))
        sys.exit(1)

    # AI 推荐模式
    if getattr(args, "suggest", False):
        print(f"文章: {article.title}")
        print(f"标签: {', '.join(article.tags) if article.tags else '无'}\n")
        print("🤖 AI 分析中...")
        platforms, reason = suggest_platforms(article)
        if platforms:
            print(f"\n推荐平台: {', '.join(platforms)}")
            print(f"推荐理由: {reason}")
        else:
            print(f"⚠ {reason}")
        return

    if args.platforms:
        targets = [p.strip() for p in args.platforms.split(",")]
    else:
        targets = [name for name, cfg in config.items() if isinstance(cfg, dict) and cfg.get("enabled")]

    if not targets:
        print("没有启用的发布平台，请检查 src/config/publishers.yaml")
        sys.exit(1)

    print(f"发布: {article.title}")
    print(f"平台: {', '.join(targets)}\n")

    packages = build_publish_packages(draft, targets)
    results = []
    for package in packages:
        name = package.platform
        print(f"[{name}] 发布中...")
        try:
            pub = get_publisher(name)
            result = pub.publish(package_to_article(package), config.get(name, {}))
            print(f"[{name}] {result.status.value}: {result.message}")
            results.append({
                "platform": name,
                "status": result.status.value,
                "message": result.message,
                "url": result.url or "",
            })
        except ValueError as e:
            print(f"[{name}] 错误: {e}")
            results.append({
                "platform": name,
                "status": "failed",
                "message": str(e),
                "url": "",
            })
        except Exception as e:
            print(f"[{name}] 错误: {e}")
            results.append({
                "platform": name,
                "status": "failed",
                "message": str(e),
                "url": "",
            })

    # 同步到 Notion 发布记录
    if results and os.getenv("NOTION_API_KEY") and os.getenv("NOTION_PUBLISH_DB_ID"):
        print(f"\n▶ 同步到 Notion 发布记录...")
        try:
            from publisher.notion_records import NotionRecords
            notion = NotionRecords()
            saved = notion.save_batch_results(
                title=article.title,
                results=results,
                draft_title=article.title
            )
            print(f"✓ Notion 发布记录已更新: {saved}/{len(results)} 条")
        except Exception as e:
            print(f"⚠ Notion 同步失败: {e}")

    print("\n发布完成。")


if __name__ == "__main__":
    main()
