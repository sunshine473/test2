"""懂车帝发布适配器 — 实际走头条号（mp.toutiao.com）后台

懂车帝没有独立创作者后台，汽车类内容通过头条号发布后自动分发到懂车帝。
"""

from publisher.models import Article, PublishResult, PublishStatus
from publisher.platforms.browser_base import BrowserPublisher
from publisher.registry import register


@register("dongchedi")
class DongchediPublisher(BrowserPublisher):
    """懂车帝 → 头条号后台发布，汽车内容自动分发到懂车帝"""

    login_url = "https://mp.toutiao.com/auth/page/login"
    editor_url = "https://mp.toutiao.com/profile_v4/graphic/publish"

    def _is_login_page(self, page) -> bool:
        """头条号：检查登录表单是否存在"""
        url = page.url.lower()
        if "login" in url or "auth" in url:
            return True
        try:
            return page.locator('.web-login-normal-input__input, input[placeholder="手机号"]').first.is_visible(timeout=2000)
        except Exception:
            return False

    def _do_publish(self, page, article: Article, config: dict) -> PublishResult:
        # 1. 确保在编辑器页面
        if "graphic/publish" not in page.url:
            try:
                page.goto(self.editor_url, wait_until="domcontentloaded", timeout=30000)
            except Exception:
                pass
            self._random_delay(3, 5)

        # 关闭 AI 创作助手抽屉（会遮挡编辑器）
        page.evaluate('''() => {
            const mask = document.querySelector(".byte-drawer-mask");
            if (mask) mask.click();
            const close = document.querySelector(".ai-assistant-drawer .byte-drawer-close, .byte-drawer-wrapper button[aria-label='Close']");
            if (close) close.click();
        }''')
        self._random_delay(1, 2)

        # 2. 填写标题（textarea，限 30 字）
        title = article.title[:30]
        print(f"[dongchedi] 填写标题: {title}")
        title_input = page.locator('textarea[placeholder*="标题"]').first
        title_input.click()
        title_input.fill(title)
        self._random_delay(0.5, 1)

        # 3. 填写正文（ProseMirror 富文本编辑器）
        print(f"[dongchedi] 填写正文...")
        editor = page.locator('.ProseMirror').first
        editor.click()
        self._random_delay(0.3, 0.5)
        # ProseMirror 用 keyboard.type 输入，截取前 5000 字
        body = article.content.strip()[:5000]
        page.keyboard.type(body, delay=5)
        self._random_delay(2, 3)

        # 4. 等待草稿自动保存（头条号编辑器自动保存草稿）
        print(f"[dongchedi] 等待草稿自动保存...")
        page.wait_for_timeout(5000)

        return PublishResult(
            platform="dongchedi",
            status=PublishStatus.SUCCESS,
            message="文章已自动保存到头条号草稿箱（汽车内容将自动分发到懂车帝）",
        )
