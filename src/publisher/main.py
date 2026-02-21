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
        print(f"文件不存在: {filepath}")
        sys.exit(1)

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
            for line in parts[1].strip().split("\n"):
                if ":" in line:
                    k, v = line.split(":", 1)
                    k, v = k.strip(), v.strip()
                    if k == "title": title = v
                    elif k == "author": author = v
                    elif k == "digest": digest = v
                    elif k == "cover_image": cover_image = v
                    elif k == "tags": tags = [t.strip() for t in v.split(",") if t.strip()]
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


def main():
    parser = argparse.ArgumentParser(description="内容发布器")
    parser.add_argument("filepath", help="Markdown 文件路径")
    parser.add_argument("--platforms", default=None, help="目标平台，逗号分隔（默认发布到所有 enabled 平台）")
    args = parser.parse_args()

    config = load_config()
    article = parse_article(args.filepath)

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

    print("\n发布完成。")


if __name__ == "__main__":
    main()
