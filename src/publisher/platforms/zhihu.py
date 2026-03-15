"""知乎专栏发布适配器 — Playwright 自动化"""

from publisher.models import Article, PublishResult, PublishStatus
from publisher.platforms.browser_base import BrowserPublisher
from publisher.registry import register
from packager.common import markdown_to_zhihu_html


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

        if article.metadata.get("content_format") == "html":
            body_html = article.content.strip()[:10000]
        else:
            body_html = markdown_to_zhihu_html(article.content.strip()[:10000])
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
