"""知乎专栏发布适配器"""

from publisher.models import Article, PublishResult, PublishStatus
from publisher.platforms.browser_base import BrowserPublisher
from publisher.registry import register


@register("zhihu")
class ZhihuPublisher(BrowserPublisher):
    """知乎专栏 — Playwright 自动化"""

    login_url = "https://www.zhihu.com/signin"
    editor_url = "https://zhuanlan.zhihu.com/write"

    def _do_publish(self, page, article: Article, config: dict) -> PublishResult:
        # TODO: 实现知乎专栏发布的 DOM 操作
        return PublishResult(
            platform="zhihu",
            status=PublishStatus.SKIPPED,
            message="知乎适配器待实现",
        )
