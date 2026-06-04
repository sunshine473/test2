"""懂车帝发布适配器 — 懂车号（mp.dcdapp.com）后台。"""

from publisher.models import Article, PublishResult, PublishStatus
from publisher.platforms.browser_base import BrowserPublisher
from publisher.registry import register


@register("dongchedi")
class DongchediPublisher(BrowserPublisher):
    """懂车帝懂车号 — 自动填写标题正文 → 存草稿"""

    login_url = "https://mp.dcdapp.com"
    editor_url = "https://mp.dcdapp.com/profile_v2/publish/article"
    cookie_origins = ["https://mp.dcdapp.com", "https://www.dongchedi.com", "https://www.dcdapp.com"]

    def _is_login_page(self, page) -> bool:
        """懂车号：检查登录页或登录控件是否存在。"""
        url = page.url.lower()
        if "login" in url or "sso" in url or "passport" in url:
            return True
        try:
            return page.locator(
                'input[placeholder*="手机号"], input[placeholder*="验证码"], '
                'button:has-text("登录"), text=扫码登录'
            ).first.is_visible(timeout=2000)
        except Exception:
            return False

    def _is_logged_in(self, page) -> bool:
        """懂车号文章编辑器可用时才认为已登录。"""
        try:
            title_visible = self._title_locator(page).is_visible(timeout=3000)
            editor_visible = self._editor_locator(page).is_visible(timeout=3000)
            return title_visible and editor_visible
        except Exception:
            return False

    def _do_publish(self, page, article: Article, config: dict) -> PublishResult:
        # 1. 确保在编辑器页面
        if "/publish/article" not in page.url:
            try:
                page.goto(self.editor_url, wait_until="domcontentloaded", timeout=30000)
            except Exception:
                pass
            self._random_delay(3, 5)

        if self._is_login_page(page) and not self._is_logged_in(page):
            return PublishResult(
                platform="dongchedi",
                status=PublishStatus.FAILED,
                message="未登录懂车号后台，无法保存懂车帝草稿",
            )

        if not self._is_logged_in(page):
            message = "未检测到懂车号文章编辑器，请确认账号已登录并有发文权限"
            if config.get("_headless"):
                message = "未检测到懂车号文章编辑器，DONGCHEDI_COOKIE 需来自 mp.dcdapp.com 且账号需有发文权限"
            return PublishResult(
                platform="dongchedi",
                status=PublishStatus.FAILED,
                message=message,
            )

        # 关闭可能遮挡编辑器的抽屉/弹窗
        page.evaluate('''() => {
            const mask = document.querySelector(".byte-drawer-mask");
            if (mask) mask.click();
            const close = document.querySelector(".byte-drawer-close, .byte-drawer-wrapper button[aria-label='Close'], .arco-modal-close-icon");
            if (close) close.click();
        }''')
        self._random_delay(1, 2)

        # 2. 填写标题（懂车号限制 2~30 个汉字）
        title = article.title[:30]
        print(f"[dongchedi] 填写标题: {title}")
        title_input = self._title_locator(page)
        title_input.click()
        title_input.fill(title)
        self._random_delay(0.5, 1)

        # 3. 填写正文（懂车号 SylEditor）
        print(f"[dongchedi] 填写正文...")
        editor = self._editor_locator(page)
        editor.click()
        self._random_delay(0.3, 0.5)
        body = article.content.strip()[:5000]
        page.keyboard.type(body, delay=5)
        self._random_delay(2, 3)

        # 4. 等待草稿自动保存（懂车号编辑器有自动保存）
        print(f"[dongchedi] 等待草稿自动保存...")
        page.wait_for_timeout(5000)

        if not self._draft_content_visible(page, title, body):
            return PublishResult(
                platform="dongchedi",
                status=PublishStatus.FAILED,
                message="草稿保存校验失败：标题或正文未保留在编辑器中",
            )

        return PublishResult(
            platform="dongchedi",
            status=PublishStatus.SUCCESS,
            message="文章已自动保存到懂车号草稿箱",
        )

    def _draft_content_visible(self, page, title: str, body: str) -> bool:
        """轻量确认编辑器仍保留刚填入的标题和正文。"""
        try:
            current_title = self._title_locator(page).input_value(timeout=2000)
            editor_text = self._editor_locator(page).inner_text(timeout=2000)
        except Exception:
            return False

        body_probe = body.strip()[:30]
        return current_title.strip() == title.strip() and (not body_probe or body_probe in editor_text)

    @staticmethod
    def _title_locator(page):
        return page.locator(
            'textarea[placeholder*="文章标题"], textarea[placeholder*="标题"], '
            'input[placeholder*="文章标题"], input[placeholder*="标题"]'
        ).first

    @staticmethod
    def _editor_locator(page):
        return page.locator(
            '.syl-editor [contenteditable="true"], .syl-editor .ProseMirror, '
            '.publish-editor [contenteditable="true"], [contenteditable="true"]'
        ).first
