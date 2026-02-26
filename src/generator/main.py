"""内容生成 CLI 入口

用法:
    python src/generator/main.py "选题标题"                        # 文章 + 卡片
    python src/generator/main.py "选题标题" --sources url1,url2    # 指定素材
    python src/generator/main.py "选题标题" --no-cards             # 仅文章
    python src/generator/main.py "选题标题" --cards-only           # 仅卡片（需已有文章）
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

# 确保项目根目录在 sys.path 中
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))


def ensure_utf8():
    """Windows 控制台 UTF-8 兼容"""
    if sys.stdout.encoding != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except AttributeError:
            import codecs
            sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer)
    if sys.stderr.encoding != "utf-8":
        try:
            sys.stderr.reconfigure(encoding="utf-8")
        except AttributeError:
            import codecs
            sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer)


ensure_utf8()

from dotenv import load_dotenv
load_dotenv()

from generator.writer import generate_article, _make_slug, DRAFTS_DIR
from generator.card_generator import generate_cards


def find_existing_article(topic: str) -> Path | None:
    """查找已有的文章草稿"""
    slug = _make_slug(topic)
    date_str = datetime.now().strftime("%Y-%m-%d")
    target = DRAFTS_DIR / f"{date_str}-{slug}.md"
    if target.exists():
        return target
    # 模糊匹配：同日期含 slug 的文件
    for f in DRAFTS_DIR.glob(f"{date_str}-*{slug}*.md"):
        return f
    return None


def main():
    parser = argparse.ArgumentParser(description="内容生成器")
    parser.add_argument("topic", help="选题标题")
    parser.add_argument("--sources", help="素材来源：逗号分隔的 URL 或文本文件路径（.txt）", default=None)
    parser.add_argument("--no-cards", action="store_true", help="仅生成文章")
    parser.add_argument("--cards-only", action="store_true", help="仅生成卡片")
    args = parser.parse_args()

    topic = args.topic
    # 解析 sources：支持文件路径（.txt）或逗号分隔的 URL/文本
    sources = None
    if args.sources:
        source_path = Path(args.sources)
        if source_path.suffix == ".txt" and source_path.exists():
            sources = [
                line.strip()
                for line in source_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            print(f"✓ 从文件加载 {len(sources)} 条素材: {source_path}")
        else:
            sources = args.sources.split(",")

    date_str = datetime.now().strftime("%Y-%m-%d")
    slug = f"{date_str}-{_make_slug(topic)}"

    # --cards-only: 需要已有文章
    if args.cards_only:
        existing = find_existing_article(topic)
        if not existing:
            print(f"✗ 未找到已有文章，请先生成文章或去掉 --cards-only")
            sys.exit(1)
        article = existing.read_text(encoding="utf-8")
        print(f"✓ 读取已有文章: {existing}")
    else:
        print(f"▶ 生成文章: {topic}")
        article, article_path = generate_article(topic, sources)
        print(f"✓ 文章已保存: {article_path}")

    # 生成卡片
    if not args.no_cards:
        print(f"▶ 生成视觉卡片...")
        cards_path = generate_cards(article, slug, DRAFTS_DIR)
        print(f"✓ 卡片已保存: {cards_path}")

    print("✓ 完成！")


if __name__ == "__main__":
    main()
