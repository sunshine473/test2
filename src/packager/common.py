"""包装层公共工具。"""

from __future__ import annotations

import base64
import re
import tempfile
from pathlib import Path


def extract_images_from_cards_html(cards_html_path: Path) -> list[str]:
    """从 -cards.html 中提取 base64 图片，保存为临时 PNG 文件，返回路径列表。"""
    if not cards_html_path.exists():
        return []

    html = cards_html_path.read_text(encoding="utf-8")
    matches = re.findall(r'src="data:image/png;base64,([A-Za-z0-9+/=]+)"', html)
    if not matches:
        return []

    tmp_dir = Path(tempfile.mkdtemp(prefix="publisher_imgs_"))
    paths = []
    for index, b64 in enumerate(matches[:9]):
        img_path = tmp_dir / f"card_{index}.png"
        img_path.write_bytes(base64.b64decode(b64))
        paths.append(str(img_path))
    return paths


def markdown_to_zhihu_html(md: str) -> str:
    """简易 Markdown → HTML，供知乎包装层使用。"""
    lines = md.strip().split("\n")
    html_parts = []
    in_code_block = False
    in_list = False

    for line in lines:
        if line.strip().startswith("```"):
            if in_code_block:
                html_parts.append("</code></pre>")
                in_code_block = False
            else:
                lang = line.strip()[3:].strip()
                html_parts.append(f'<pre><code class="language-{lang}">' if lang else "<pre><code>")
                in_code_block = True
            continue
        if in_code_block:
            html_parts.append(line)
            continue

        stripped = line.strip()
        if in_list and not stripped.startswith(("* ", "- ")) and not re.match(r"^\d+\.\s+", stripped):
            html_parts.append("</ul>")
            in_list = False

        if not stripped:
            html_parts.append("<p><br></p>")
            continue

        heading = re.match(r"^(#{1,4})\s+(.+)$", stripped)
        if heading:
            level = len(heading.group(1))
            html_parts.append(f"<h{level}>{_inline(heading.group(2))}</h{level}>")
            continue

        bullet = re.match(r"^[*\-]\s+(.+)$", stripped)
        if bullet:
            if not in_list:
                html_parts.append("<ul>")
                in_list = True
            html_parts.append(f"<li>{_inline(bullet.group(1))}</li>")
            continue

        html_parts.append(f"<p>{_inline(stripped)}</p>")

    if in_list:
        html_parts.append("</ul>")
    if in_code_block:
        html_parts.append("</code></pre>")
    return "\n".join(html_parts)


def _inline(text: str) -> str:
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"`(.+?)`", r"<code>\1</code>", text)
    text = re.sub(r"\[(.+?)\]\((.+?)\)", r'<a href="\2">\1</a>', text)
    return text
