"""懂车帝发布适配器 — 懂车号新版图文动态直接发布。"""

import re
from pathlib import Path

from publisher.models import Article, PublishResult, PublishStatus
from publisher.platforms.browser_base import BrowserPublisher
from publisher.registry import register


@register("dongchedi")
class DongchediPublisher(BrowserPublisher):
    """懂车帝懂车号 — 填写新版图文动态并直接发布。"""

    campaign_tag = "#星河创造营"
    login_url = "https://mp.dcdapp.com"
    editor_url = "https://mp.dcdapp.com/profile_v2/publish/post"
    manage_url = "https://mp.dcdapp.com/profile_v2/manage/content/posts"
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
        """新版动态富文本编辑器可用时才认为已登录。"""
        try:
            return self._dynamic_editor(page).is_visible(timeout=3000)
        except Exception:
            return False

    def _do_publish(self, page, article: Article, config: dict) -> PublishResult:
        if "/profile_v2/publish/post" not in page.url:
            try:
                page.goto(self.editor_url, wait_until="domcontentloaded", timeout=30000)
            except Exception:
                pass
            self._random_delay(3, 5)

        if self._is_login_page(page) and not self._is_logged_in(page):
            return PublishResult(
                platform="dongchedi",
                status=PublishStatus.FAILED,
                message="未登录懂车号新版后台，无法检查懂车帝动态编辑器",
            )

        if not self._is_logged_in(page):
            message = "未检测到懂车号新版动态编辑器，请确认账号已登录并有发动态权限"
            if config.get("_headless"):
                message = "未检测到懂车号新版动态编辑器，DONGCHEDI_COOKIE 需来自 mp.dcdapp.com 且账号需有发动态权限"
            return PublishResult(
                platform="dongchedi",
                status=PublishStatus.FAILED,
                message=message,
            )

        dynamic_text = self._build_dynamic_text(article)
        editor = self._dynamic_editor(page)
        editor.fill(dynamic_text)
        self._random_delay(1, 2)
        if not self._dynamic_content_visible(page, dynamic_text):
            return PublishResult(
                platform="dongchedi",
                status=PublishStatus.FAILED,
                message="懂车帝动态正文填写校验失败，未执行发布",
            )

        image_count = self._upload_images(page, article.images)
        if article.images and image_count != min(len(article.images), 9):
            return PublishResult(
                platform="dongchedi",
                status=PublishStatus.FAILED,
                message=f"懂车帝动态图片上传失败：期望 {min(len(article.images), 9)} 张，实际 {image_count} 张",
            )

        publish_button = page.get_by_role("button", name="发布", exact=True)
        if publish_button.count() != 1 or not publish_button.is_enabled():
            return PublishResult(
                platform="dongchedi",
                status=PublishStatus.FAILED,
                message="懂车帝动态发布按钮不可用，未执行发布",
            )

        publish_button.click()
        try:
            page.wait_for_url("**/profile_v2/manage/content/posts", timeout=30000)
        except Exception:
            pass
        self._random_delay(2, 3)

        if "/profile_v2/manage/content/posts" not in page.url:
            return PublishResult(
                platform="dongchedi",
                status=PublishStatus.FAILED,
                message="懂车帝动态已提交，但未跳转到作品管理页，发布状态无法确认",
            )

        return PublishResult(
            platform="dongchedi",
            status=PublishStatus.SUCCESS,
            message=f"图文动态已提交懂车帝，上传 {image_count} 张图片，当前请在作品管理查看审核状态",
        )

    def _dynamic_content_visible(self, page, dynamic_text: str) -> bool:
        """轻量确认新版动态富文本编辑器仍保留刚填入的内容。"""
        try:
            current_text = self._dynamic_editor(page).inner_text(timeout=2000)
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

        content = content.replace(self.campaign_tag, "").strip()
        suffix = f"\n\n{self.campaign_tag}"
        return f"{content[:2000 - len(suffix)].rstrip()}{suffix}"

    def _upload_images(self, page, images: list[str]) -> int:
        """上传最多 9 张图片，保持列表顺序，首图作为封面。"""
        image_paths = [
            str(Path(path).expanduser().resolve())
            for path in images
            if path and Path(path).expanduser().exists()
        ][:9]
        if not image_paths:
            return 0

        page.get_by_role("button", name="图片", exact=True).click()
        page.get_by_text("上传图片", exact=True).click()
        upload_input = page.locator('input[type="file"]')
        if upload_input.count() != 1:
            return 0
        upload_input.set_input_files(image_paths)

        confirm_button = page.get_by_role("button", name="确定", exact=True)
        try:
            confirm_button.wait_for(state="visible", timeout=60000)
            page.wait_for_function(
                """() => {
                    const buttons = [...document.querySelectorAll("button")];
                    const confirm = buttons.find((button) => button.textContent.trim() === "确定");
                    return Boolean(confirm && !confirm.disabled);
                }""",
                timeout=60000,
            )
        except Exception:
            return 0

        confirm_button.click()
        try:
            page.get_by_text("上传完成，可以拖拽调整图片顺序", exact=False).wait_for(
                state="hidden",
                timeout=15000,
            )
        except Exception:
            pass
        return len(image_paths)

    @staticmethod
    def _dynamic_editor(page):
        return page.locator('.ProseMirror[contenteditable="true"]').first
