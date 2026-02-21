"""今日头条发布适配器"""

from publisher.models import Article, PublishResult, PublishStatus
from publisher.platforms.browser_base import BrowserPublisher
from publisher.registry import register


@register("toutiao")
class ToutiaoPublisher(BrowserPublisher):
    """今日头条/头条号 — Playwright 自动化"""

    login_url = "https://mp.toutiao.com/auth/page/login"
    editor_url = "https://mp.toutiao.com/profile_v4/graphic/publish"

    def _do_publish(self, page, article: Article, config: dict) -> PublishResult:
        # TODO: 实现头条号发布的 DOM 操作
        return PublishResult(
            platform="toutiao",
            status=PublishStatus.SKIPPED,
            message="头条适配器待实现",
        )
