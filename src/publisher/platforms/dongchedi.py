"""懂车帝发布适配器 — 懂车号图文动态（mp.dcdapp.com/ugc/publish）。"""

import re
from pathlib import Path

from publisher.models import Article, PublishResult, PublishStatus
from publisher.platforms.browser_base import BrowserPublisher
from publisher.registry import register


@register("dongchedi")
class DongchediPublisher(BrowserPublisher):
    """懂车帝懂车号 — 自动发布图文动态"""

    login_url = "https://mp.dcdapp.com"
    editor_url = "https://mp.dcdapp.com/ugc/publish#/picture"
    cookie_origins = ["https://mp.dcdapp.com", "https://www.dongchedi.com", "https://www.dcdapp.com"]
    require_logged_in_editor = True

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
        """懂车号图文动态输入框可用时才认为已登录。"""
        try:
            return self._dynamic_textarea(page).is_visible(timeout=3000)
        except Exception:
            return False

    def _do_publish(self, page, article: Article, config: dict) -> PublishResult:
        # 1. 确保在图文动态页面
        if "#/picture" not in page.url:
            try:
                page.goto(self.editor_url, wait_until="domcontentloaded", timeout=30000)
            except Exception:
                pass
            self._random_delay(3, 5)

        if self._is_login_page(page) and not self._is_logged_in(page):
            return PublishResult(
                platform="dongchedi",
                status=PublishStatus.FAILED,
                message="未登录懂车号后台，无法发布懂车帝动态",
            )

        if not self._is_logged_in(page):
            message = "未检测到懂车号图文动态输入框，请确认账号已登录并有发动态权限"
            if config.get("_headless"):
                message = "未检测到懂车号图文动态输入框，DONGCHEDI_COOKIE 需来自 mp.dcdapp.com 且账号需有发动态权限"
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

        # 2. 填写动态正文（懂车号图文动态限制 2000 字）
        dynamic_text = self._build_dynamic_text(article)
        print(f"[dongchedi] 填写图文动态: {dynamic_text[:40]}...")
        textarea = self._dynamic_textarea(page)
        textarea.click()
        textarea.fill(dynamic_text)
        self._random_delay(2, 3)

        if not self._dynamic_content_visible(page, dynamic_text):
            return PublishResult(
                platform="dongchedi",
                status=PublishStatus.FAILED,
                message="动态发布校验失败：正文未保留在输入框中",
            )

        image_count = self._upload_images(page, article.images)
        if article.images and image_count <= 0:
            return PublishResult(
                platform="dongchedi",
                status=PublishStatus.FAILED,
                message="动态图片上传失败：未检测到已上传图片",
            )

        self._disable_toutiao_sync(page)
        publish_button = self._publish_button(page)
        try:
            publish_button.wait_for(state="visible", timeout=5000)
        except Exception:
            pass
        if not self._publish_button_enabled(page):
            return PublishResult(
                platform="dongchedi",
                status=PublishStatus.FAILED,
                message="动态发布按钮不可用，请确认正文长度或账号权限",
            )

        print("[dongchedi] 立即发布动态...")
        publish_button.click()
        self._confirm_publish_if_needed(page)
        page.wait_for_timeout(5000)

        if not self._publish_succeeded(page, dynamic_text):
            return PublishResult(
                platform="dongchedi",
                status=PublishStatus.FAILED,
                message="动态已提交，但未检测到明确发布成功提示",
            )

        return PublishResult(
            platform="dongchedi",
            status=PublishStatus.SUCCESS,
            message="图文动态已发布到懂车帝",
        )

    def _dynamic_content_visible(self, page, dynamic_text: str) -> bool:
        """轻量确认动态输入框仍保留刚填入的内容。"""
        try:
            current_text = self._dynamic_textarea(page).input_value(timeout=2000)
        except Exception:
            return False

        probe = dynamic_text.strip()[:30]
        return bool(probe) and probe in current_text

    def _build_dynamic_text(self, article: Article) -> str:
        """将 Markdown 文章压缩为懂车帝图文动态文本。"""
        content = article.content.strip()
        content = re.sub(r"^---\s*.*?\s*---\s*", "", content, flags=re.DOTALL)
        content = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", content)
        content = re.sub(r"`{1,3}", "", content)
        content = re.sub(r"^#{1,6}\s+", "", content, flags=re.MULTILINE)
        content = re.sub(r"\n{3,}", "\n\n", content).strip()

        title = article.title.strip()
        if title and not content.startswith(title):
            content = f"{title}\n\n{content}" if content else title
        return content[:2000].strip()

    def _disable_toutiao_sync(self, page) -> None:
        """仅发布懂车帝动态，不同步到微头条。"""
        try:
            page.evaluate('''() => {
                const input = document.querySelector(".radio-wrap input[type='checkbox']");
                if (input && input.checked) {
                    input.click();
                }
            }''')
        except Exception:
            pass

    def _upload_images(self, page, images: list[str]) -> int:
        """上传图文动态图片，列表第一张会作为动态封面图。"""
        image_paths = [str(Path(path).expanduser().resolve()) for path in images if path and Path(path).exists()]
        if not image_paths:
            return 0

        image_paths = image_paths[:9]
        print(f"[dongchedi] 上传图片: {len(image_paths)} 张，封面图: {Path(image_paths[0]).name}")
        page.locator(".fun-button", has_text="选择图片").first.click(force=True)
        upload_input = page.locator("input.add-pic-input[type='file']").first
        upload_input.set_input_files(image_paths)

        expected = len(image_paths)
        try:
            page.wait_for_function(
                """(expected) => {
                    const text = document.body.innerText || "";
                    const match = text.match(/照片已(\\d+)张/);
                    return match && Number(match[1]) >= expected;
                }""",
                arg=expected,
                timeout=60000,
            )
        except Exception:
            pass
        return self._uploaded_image_count(page)

    def _uploaded_image_count(self, page) -> int:
        try:
            body_text = page.locator("body").inner_text(timeout=3000)
        except Exception:
            return 0
        match = re.search(r"照片已(\d+)张", body_text)
        return int(match.group(1)) if match else 0

    def _publish_button_enabled(self, page) -> bool:
        try:
            return page.evaluate('''() => {
                const button = Array.from(document.querySelectorAll("button"))
                    .find((el) => (el.innerText || "").includes("立即发布"));
                return Boolean(button && !button.disabled && !button.className.includes("btn-disable"));
            }''')
        except Exception:
            return False

    def _confirm_publish_if_needed(self, page) -> None:
        try:
            confirm = page.locator(
                'button:has-text("确定"), button:has-text("确认"), button:has-text("继续发布")'
            ).last
            if confirm.is_visible(timeout=2000):
                confirm.click()
        except Exception:
            pass

    def _publish_succeeded(self, page, dynamic_text: str) -> bool:
        try:
            body_text = page.locator("body").inner_text(timeout=3000)
        except Exception:
            body_text = ""
        success_markers = ("发布成功", "发布队列", "内容管理")
        if any(marker in body_text for marker in success_markers) and dynamic_text[:30] not in body_text:
            return True
        return "#/content" in page.url or "#/task" in page.url

    @staticmethod
    def _dynamic_textarea(page):
        return page.locator('textarea[placeholder*="分享汽车生活"], textarea').first

    @staticmethod
    def _publish_button(page):
        return page.locator('button:has-text("立即发布")').first
