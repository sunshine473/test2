"""知乎专栏发布适配器 — Playwright 自动化"""

import re

from publisher.models import Article, PublishResult, PublishStatus
from publisher.platforms.browser_base import BrowserPublisher
from publisher.registry import register


def _md_to_html(md: str) -> str:
    """简易 Markdown → HTML 转换（覆盖知乎常用格式）"""
    lines = md.strip().split("\n")
    html_parts = []
    in_code_block = False
    in_list = False

    for line in lines:
        # 代码块
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

        # 关闭列表
        if in_list and not line.strip().startswith(("* ", "- ", "1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.")):
            html_parts.append("</ul>")
            in_list = False

        stripped = line.strip()
        if not stripped:
            html_parts.append("<p><br></p>")
            continue

        # 标题
        m = re.match(r"^(#{1,4})\s+(.+)$", stripped)
        if m:
            level = len(m.group(1))
            html_parts.append(f"<h{level}>{_inline(m.group(2))}</h{level}>")
            continue

        # 无序列表
        m = re.match(r"^[*\-]\s+(.+)$", stripped)
        if m:
            if not in_list:
                html_parts.append("<ul>")
                in_list = True
            html_parts.append(f"<li>{_inline(m.group(1))}</li>")
            continue

        # 普通段落
        html_parts.append(f"<p>{_inline(stripped)}</p>")

    if in_list:
        html_parts.append("</ul>")
    if in_code_block:
        html_parts.append("</code></pre>")

    return "\n".join(html_parts)


def _inline(text: str) -> str:
    """处理行内格式：加粗、行内代码、链接"""
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"`(.+?)`", r"<code>\1</code>", text)
    text = re.sub(r"\[(.+?)\]\((.+?)\)", r'<a href="\2">\1</a>', text)
    return text


@register("zhihu")
class ZhihuPublisher(BrowserPublisher):
    """知乎专栏 — 自动填写标题正文 → 存草稿"""

    login_url = "https://www.zhihu.com/signin"
    editor_url = "https://zhuanlan.zhihu.com/write"

    def _is_login_page(self, page) -> bool:
        url = page.url.lower()
        if "signin" in url or "login" in url:
            return True
        try:
            return page.locator('input[placeholder="手机号"]').is_visible(timeout=2000)
        except Exception:
            return False

    def _do_publish(self, page, article: Article, config: dict) -> PublishResult:
        # 1. 确保在编辑器页面
        if "write" not in page.url:
            try:
                page.goto(self.editor_url, wait_until="domcontentloaded", timeout=30000)
            except Exception:
                pass
            self._random_delay(3, 5)

        # 2. 填写标题（textarea，限 100 字）
        title = article.title[:100]
        print(f"[zhihu] 填写标题: {title}")
        title_input = page.locator('textarea[placeholder*="标题"]').first
        title_input.click()
        title_input.fill(title)
        self._random_delay(0.5, 1)

        # 3. 将 Markdown 转为 HTML，通过 paste 事件注入富文本编辑器
        print(f"[zhihu] 填写正文...")
        editor = page.locator('.public-DraftEditor-content, [contenteditable="true"]').first
        editor.click()
        self._random_delay(0.3, 0.5)

        body_html = _md_to_html(article.content.strip()[:10000])
        # 构造 paste 事件，让 Draft.js 编辑器解析 HTML 富文本
        page.evaluate("""(html) => {
            const editor = document.querySelector('.public-DraftEditor-content, [contenteditable="true"]');
            const dt = new DataTransfer();
            dt.setData('text/html', html);
            dt.setData('text/plain', html.replace(/<[^>]+>/g, ''));
            const event = new ClipboardEvent('paste', {
                clipboardData: dt,
                bubbles: true,
                cancelable: true
            });
            editor.dispatchEvent(event);
        }""", body_html)
        self._random_delay(2, 3)

        # 4. 等待草稿自动保存（知乎编辑器有自动保存）
        print(f"[zhihu] 等待草稿保存...")
        page.wait_for_timeout(5000)

        return PublishResult(
            platform="zhihu",
            status=PublishStatus.SUCCESS,
            message="文章已保存到知乎草稿箱",
        )
