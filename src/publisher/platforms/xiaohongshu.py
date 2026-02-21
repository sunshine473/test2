"""小红书发布适配器 — Playwright 自动化"""

from publisher.models import Article, PublishResult, PublishStatus
from publisher.platforms.browser_base import BrowserPublisher
from publisher.registry import register


@register("xiaohongshu")
class XiaohongshuPublisher(BrowserPublisher):
    """小红书图文笔记 — 自动上传卡片图 + 填写标题正文 → 存草稿"""

    login_url = "https://creator.xiaohongshu.com/login"
    editor_url = "https://creator.xiaohongshu.com/publish/publish"

    def _is_login_page(self, page) -> bool:
        """小红书登录页 URL 不变（仍是 /publish/publish），只能通过页面内容判断"""
        try:
            return page.locator('text=短信登录').is_visible(timeout=2000)
        except Exception:
            return False

    def _do_publish(self, page, article: Article, config: dict) -> PublishResult:
        if not article.images:
            return PublishResult(
                platform="xiaohongshu",
                status=PublishStatus.FAILED,
                message="小红书需要至少 1 张图片，请先生成卡片",
            )

        # 1. 确保在发布页
        if "publish" not in page.url:
            try:
                page.goto(self.editor_url, wait_until="domcontentloaded", timeout=30000)
            except Exception:
                pass
            self._random_delay(2, 3)

        # 2. 点击"上传图文"标签（用 JS 点击避免 viewport 问题）
        print(f"[xiaohongshu] 切换到图文发布...")
        page.evaluate('''() => {
            const spans = document.querySelectorAll("span.title");
            for (const s of spans) {
                if (s.textContent.trim() === "上传图文" && s.offsetParent !== null) {
                    s.click();
                    break;
                }
            }
        }''')
        self._random_delay(3, 5)

        # 3. 上传图片 — 图文模式下 file input accept=".jpg,.jpeg,.png,.webp"
        print(f"[xiaohongshu] 上传 {len(article.images)} 张图片...")
        img_input = page.locator('input[type="file"][accept*=".jpg"], input.upload-input[accept*=".png"]').first
        img_input.wait_for(state="attached", timeout=10000)
        img_input.set_input_files(article.images)
        self._random_delay(3, 5)

        # 等待图片上传完成
        page.wait_for_timeout(8000)

        # 4. 填写标题（限 20 字）
        title = article.title[:20]
        print(f"[xiaohongshu] 填写标题: {title}")
        title_input = page.locator('input[placeholder*="标题"], input[placeholder*="赞"]').first
        title_input.click()
        title_input.fill(title)
        self._random_delay(0.5, 1)

        # 5. 填写正文（截取前 1000 字）
        body = article.content.strip()[:1000]
        print(f"[xiaohongshu] 填写正文 ({len(body)} 字)...")
        editor = page.locator('[placeholder*="正文"], [placeholder*="描述"], #composerDescInput, .ql-editor, [contenteditable="true"]').first
        editor.click()
        self._random_delay(0.3, 0.5)
        page.keyboard.type(body, delay=10)
        self._random_delay(1, 2)

        # 6. 存草稿（按钮文字是"暂存离开"）
        print(f"[xiaohongshu] 保存草稿...")
        page.locator('button:has-text("暂存离开")').click()
        self._random_delay(2, 3)

        return PublishResult(
            platform="xiaohongshu",
            status=PublishStatus.SUCCESS,
            message="笔记已保存到草稿箱",
        )
