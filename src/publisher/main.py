"""发布调度入口

用法:
    python src/publisher/main.py content/drafts/2026-02-20-xxx.md
    python src/publisher/main.py content/drafts/2026-02-20-xxx.md --platforms wechat,bilibili
"""

import argparse
import base64
import re
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(PROJECT_ROOT / "src" / "wechat_publisher" / ".env")  # 兼容旧版微信配置

import yaml
from publisher.models import Article
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


def extract_images_from_cards_html(cards_html_path: Path) -> list[str]:
    """从 -cards.html 中提取 base64 图片，保存为临时 PNG 文件，返回路径列表"""
    if not cards_html_path.exists():
        return []

    html = cards_html_path.read_text(encoding="utf-8")
    # 匹配 base64 图片: src="data:image/png;base64,..."
    pattern = r'src="data:image/png;base64,([A-Za-z0-9+/=]+)"'
    matches = re.findall(pattern, html)

    if not matches:
        return []

    tmp_dir = Path(tempfile.mkdtemp(prefix="publisher_imgs_"))
    paths = []
    for i, b64 in enumerate(matches[:9]):  # 小红书最多 9 张
        img_path = tmp_dir / f"card_{i}.png"
        img_path.write_bytes(base64.b64decode(b64))
        paths.append(str(img_path))

    return paths


def parse_article(filepath: str) -> Article:
    """从 Markdown 文件解析 Article 对象，自动查找配套卡片图"""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {filepath}")

    raw = path.read_text(encoding="utf-8")

    title = path.stem
    author = ""
    digest = ""
    cover_image = ""
    tags = []
    content = raw

    if raw.startswith("---"):
        parts = raw.split("---", 2)
        if len(parts) >= 3:
            try:
                frontmatter = yaml.safe_load(parts[1]) or {}
            except Exception:
                frontmatter = {}
            if isinstance(frontmatter, dict):
                title = str(frontmatter.get("title", title) or title)
                author = str(frontmatter.get("author", author) or author)
                digest = str(frontmatter.get("digest", digest) or digest)
                cover_image = str(frontmatter.get("cover_image", cover_image) or cover_image)
                raw_tags = frontmatter.get("tags", tags)
                if isinstance(raw_tags, list):
                    tags = [str(t).strip() for t in raw_tags if str(t).strip()]
                elif isinstance(raw_tags, str):
                    tags = [t.strip() for t in raw_tags.split(",") if t.strip()]
            content = parts[2]

    # 自动查找同名 -cards.html 提取卡片图
    cards_html = path.with_name(path.stem + "-cards.html")
    images = extract_images_from_cards_html(cards_html)
    if images:
        print(f"从卡片 HTML 提取了 {len(images)} 张配图")

    return Article(
        title=title,
        content=content,
        author=author,
        digest=digest,
        cover_image=cover_image,
        source_path=str(path.resolve()),
        images=images,
        tags=tags,
    )


def suggest_platforms(article: Article) -> list[str]:
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
        article = parse_article(args.filepath)
    except FileNotFoundError as e:
        print(str(e))
        sys.exit(1)

    # AI 推荐模式
    if args.suggest:
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

    for name in targets:
        print(f"[{name}] 发布中...")
        try:
            pub = get_publisher(name)
            result = pub.publish(article, config.get(name, {}))
            print(f"[{name}] {result.status.value}: {result.message}")
        except ValueError as e:
            print(f"[{name}] 错误: {e}")
        except Exception as e:
            print(f"[{name}] 错误: {e}")

    print("\n发布完成。")


if __name__ == "__main__":
    main()
