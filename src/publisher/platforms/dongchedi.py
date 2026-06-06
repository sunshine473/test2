"""懂车帝发布适配器 — 懂车号新版动态发布页的草稿安全保护。"""

import re

from publisher.models import Article, PublishResult, PublishStatus
from publisher.platforms.browser_base import BrowserPublisher
from publisher.registry import register


@register("dongchedi")
class DongchediPublisher(BrowserPublisher):
    """懂车帝懂车号 — 动态没有草稿能力时禁止自动填写或发布。"""

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

        return PublishResult(
            platform="dongchedi",
            status=PublishStatus.FAILED,
            message=(
                "懂车号新版动态仅支持直接发布，作品管理的动态页没有草稿入口；"
                "已在填写、上传和发布前停止"
            ),
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

    @staticmethod
    def _dynamic_editor(page):
        return page.locator('.ProseMirror[contenteditable="true"]').first
