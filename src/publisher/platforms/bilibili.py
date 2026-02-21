"""B站专栏发布适配器"""

import os

from publisher.base import BasePublisher
from publisher.models import Article, PublishResult, PublishStatus
from publisher.registry import register


@register("bilibili")
class BilibiliPublisher(BasePublisher):
    """B站专栏 — 使用 bilibili-api-python 库"""

    def publish(self, article: Article, config: dict) -> PublishResult:
        try:
            from bilibili_api import article as bili_article
            from bilibili_api import Credential
        except ImportError:
            return PublishResult(
                platform="bilibili",
                status=PublishStatus.SKIPPED,
                message="需要安装: pip install bilibili-api-python",
            )

        sessdata = config.get("sessdata") or os.getenv("BILIBILI_SESSDATA")
        bili_jct = config.get("bili_jct") or os.getenv("BILIBILI_BILI_JCT")

        if not sessdata or not bili_jct:
            return PublishResult(
                platform="bilibili",
                status=PublishStatus.FAILED,
                message="缺少 BILIBILI_SESSDATA 或 BILIBILI_BILI_JCT",
            )

        try:
            credential = Credential(sessdata=sessdata, bili_jct=bili_jct)
            # 创建专栏草稿
            draft = bili_article.Article(credential=credential)
            draft.set_self_article(
                title=article.title,
                content=article.content,
                category_id=config.get("category", 17),
            )
            # TODO: 实际发布流程需要根据 bilibili-api-python 最新 API 调整
            return PublishResult(
                platform="bilibili",
                status=PublishStatus.SKIPPED,
                message="B站适配器待完善，请参考 bilibili-api-python 文档",
            )
        except Exception as e:
            return PublishResult(
                platform="bilibili",
                status=PublishStatus.FAILED,
                message=str(e),
            )
