"""文章生成 — 加载 prompt 模板 + 素材，调 Gemini 生成 Markdown 文章"""

import re
import yaml
from datetime import datetime
from pathlib import Path
from typing import Optional

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


def generate_article(topic: str, sources: Optional[list[str]] = None) -> tuple[str, Path]:
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


def review_article(article_path: Path) -> dict:
    """AI 质量审核，返回评分和建议"""
    content = article_path.read_text(encoding="utf-8")
    word_count = len(content)

    prompt = f"""你是一位资深内容编辑。请审核以下公众号文章，给出质量评估。

文章内容：
{content[:3000]}  # 截取前 3000 字符

请从以下维度评分（1-5 星）：
1. **标题吸引力** - 是否能引发点击欲望
2. **结构完整性** - 是否有清晰的开头→正文→结尾
3. **内容深度** - 是否有干货和独特观点
4. **风格一致性** - 是否符合科技公众号定位

输出格式：
标题吸引力: ⭐⭐⭐⭐ | 说明
结构完整性: ⭐⭐⭐⭐⭐ | 说明
内容深度: ⭐⭐⭐⭐ | 说明
风格一致性: ⭐⭐⭐⭐ | 说明

整体评级: A/B/C
修改建议: ...（如有）
"""

    try:
        review = generate_text(prompt, task="summary", temperature=0.3)
        return {
            "word_count": word_count,
            "review": review,
        }
    except Exception as e:
        return {
            "word_count": word_count,
            "review": f"⚠ 审核失败: {str(e)[:100]}",
        }


def complete_frontmatter(article_path: Path) -> dict:
    """补全 frontmatter 缺失字段（digest, tags）"""
    content = article_path.read_text(encoding="utf-8")

    # 解析 frontmatter
    if not content.startswith("---"):
        return {"error": "文章缺少 frontmatter"}

    parts = content.split("---", 2)
    if len(parts) < 3:
        return {"error": "frontmatter 格式错误"}

    try:
        frontmatter = yaml.safe_load(parts[1])
    except Exception as e:
        return {"error": f"frontmatter 解析失败: {e}"}

    # 检查缺失字段
    needs_digest = not frontmatter.get("digest")
    needs_tags = not frontmatter.get("tags")

    if not needs_digest and not needs_tags:
        return {"status": "ok", "message": "frontmatter 已完整"}

    # 用 AI 生成缺失字段
    article_body = parts[2].strip()
    prompt = f"""根据以下文章内容，生成：

文章内容：
{article_body[:2000]}

请输出：
digest: [100 字以内的摘要，用于公众号分享描述]
tags: [3-5 个话题标签，逗号分隔，如: AI, 编程, GPT]
"""

    try:
        result = generate_text(prompt, task="summary", temperature=0.3)
        # 解析 AI 输出
        digest_match = re.search(r"digest:\s*(.+)", result)
        tags_match = re.search(r"tags:\s*(.+)", result)

        if needs_digest and digest_match:
            frontmatter["digest"] = digest_match.group(1).strip()
        if needs_tags and tags_match:
            tags_str = tags_match.group(1).strip()
            frontmatter["tags"] = [t.strip() for t in tags_str.split(",")]

        # 写回文件
        new_frontmatter = yaml.dump(frontmatter, allow_unicode=True, sort_keys=False)
        new_content = f"---\n{new_frontmatter}---\n{article_body}"
        article_path.write_text(new_content, encoding="utf-8")

        return {
            "status": "completed",
            "digest": frontmatter.get("digest"),
            "tags": frontmatter.get("tags"),
        }
    except Exception as e:
        return {"error": f"补全失败: {str(e)[:100]}"}
