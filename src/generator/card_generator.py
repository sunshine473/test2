"""视觉卡片生成 — 拆分文章为卡片 JSON → 生图 → 渲染 HTML"""

import json
import re
import time
from pathlib import Path

from generator.gemini_client import generate_text, get_rate_limit_config
from generator.image_gen import create_illustration

TEMPLATES_DIR = Path(__file__).parent / "templates"
_RATE_CFG = get_rate_limit_config()


def _load_template(name: str) -> str:
    return (TEMPLATES_DIR / name).read_text(encoding="utf-8")


def _split_to_cards(article: str) -> list[dict]:
    """调 Gemini 将文章拆分为卡片 JSON"""
    template = _load_template("card_prompt.txt")
    prompt = template.replace("{article}", article)
    raw = generate_text(prompt, task="card_split")

    # 提取 JSON（兼容 ```json 包裹）
    m = re.search(r"\[.*\]", raw, re.DOTALL)
    if not m:
        raise RuntimeError(f"卡片拆分未返回有效 JSON:\n{raw[:500]}")
    return json.loads(m.group())


def _render_card_html(card: dict, index: int, total: int, image_b64: str) -> str:
    """渲染单张卡片 HTML"""
    layout = card.get("layout", "C").upper()
    css_class = f"layout-{layout.lower()}"

    if layout == "C":
        return f"""<div class="card {css_class}">
    <button class="card-download" onclick="downloadSingle({index})">下载</button>
    <span class="card-index">{index + 1}/{total}</span>
    <img class="card-img" src="data:image/png;base64,{image_b64}" alt="">
    <div class="card-overlay">
        <div class="card-title">{card.get('title', '')}</div>
        <div class="card-subtitle">{card.get('subtitle', '') or card.get('content', '')}</div>
    </div>
</div>"""
    elif layout == "A":
        return f"""<div class="card {css_class}">
    <button class="card-download" onclick="downloadSingle({index})">下载</button>
    <span class="card-index">{index + 1}/{total}</span>
    <div class="card-text">
        <div class="card-title">{card.get('title', '')}</div>
        <div class="card-content">{card.get('content', '')}</div>
    </div>
    <img class="card-img" src="data:image/png;base64,{image_b64}" alt="">
</div>"""
    else:  # B
        return f"""<div class="card {css_class}">
    <button class="card-download" onclick="downloadSingle({index})">下载</button>
    <span class="card-index">{index + 1}/{total}</span>
    <img class="card-img" src="data:image/png;base64,{image_b64}" alt="">
    <div class="card-text">
        <div class="card-title">{card.get('title', '')}</div>
        <div class="card-content">{card.get('content', '')}</div>
    </div>
</div>"""


def generate_cards(article: str, slug: str, output_dir: Path) -> Path:
    """生成视觉卡片 HTML，返回输出路径"""
    output_dir.mkdir(parents=True, exist_ok=True)

    print("  拆分文章为卡片...")
    cards = _split_to_cards(article)

    print(f"  生成 {len(cards)} 张卡片插图...")
    images = []
    for i, card in enumerate(cards):
        desc = card.get("image_prompt", card.get("title", "科技插图"))
        print(f"    [{i + 1}/{len(cards)}] {desc[:30]}...")
        try:
            b64 = create_illustration(desc)
        except Exception as e:
            print(f"    ⚠ 生图失败，使用占位: {e}")
            b64 = ""
        images.append(b64)
        if i < len(cards) - 1:
            time.sleep(_RATE_CFG["image_interval"])

    # 渲染各卡片 HTML 片段
    total = len(cards)
    cards_html_parts = []
    for i, (card, img_b64) in enumerate(zip(cards, images)):
        cards_html_parts.append(_render_card_html(card, i, total, img_b64))
    cards_html = "\n".join(cards_html_parts)

    # 填充模板
    page_template = _load_template("cards_template.html")
    title = cards[0].get("title", "视觉卡片") if cards else "视觉卡片"
    html = page_template.replace("{{title}}", title)
    html = html.replace("{{cards_html}}", cards_html)
    html = html.replace("{{slug}}", slug)

    output_path = output_dir / f"{slug}-cards.html"
    output_path.write_text(html, encoding="utf-8")
    return output_path
