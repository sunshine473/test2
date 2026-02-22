"""文章生成 — 加载 prompt 模板 + 素材，调 Gemini 生成 Markdown 文章"""

import re
from datetime import datetime
from pathlib import Path

from generator.gemini_client import generate_text

TEMPLATES_DIR = Path(__file__).parent / "templates"
DRAFTS_DIR = Path(__file__).resolve().parent.parent.parent / "content" / "drafts"


def _load_template(name: str) -> str:
    return (TEMPLATES_DIR / name).read_text(encoding="utf-8")


def _make_slug(title: str) -> str:
    """从标题生成文件名 slug：保留中文和字母数字，空格转连字符"""
    slug = re.sub(r"[^\w\u4e00-\u9fff\s-]", "", title)
    slug = re.sub(r"\s+", "-", slug.strip())
    return slug[:60]


def generate_article(topic: str, sources: list[str] | None = None) -> tuple[str, Path]:
    """生成文章，返回 (markdown_content, output_path)"""
    DRAFTS_DIR.mkdir(parents=True, exist_ok=True)

    template = _load_template("article_prompt.txt")
    sources_text = "无额外素材，请根据选题自行发挥。"
    if sources:
        sources_text = "\n".join(f"- {s}" for s in sources)

    prompt = template.replace("{topic}", topic).replace("{sources}", sources_text)
    article = generate_text(prompt, task="article")

    date_str = datetime.now().strftime("%Y-%m-%d")
    slug = _make_slug(topic)
    filename = f"{date_str}-{slug}.md"
    output_path = DRAFTS_DIR / filename
    output_path.write_text(article, encoding="utf-8")

    return article, output_path
