"""微信公众号发布适配器 — 从 src/wechat_publisher/ 迁移"""

import os
import re
import time

import requests
import markdown

from publisher.base import BasePublisher
from publisher.models import Article, PublishResult, PublishStatus
from publisher.registry import register

HTTP_TIMEOUT = 20


@register("wechat")
class WeChatPublisher(BasePublisher):
    """微信公众号 — 推送到草稿箱"""

    def __init__(self):
        self._access_token = None
        self._token_expires_at = 0

    def publish(self, article: Article, config: dict) -> PublishResult:
        app_id = (
            config.get("app_id")
            or os.getenv("WECHAT_APP_ID")
            or os.getenv("WECHAT_APPID")
        )
        app_secret = (
            config.get("app_secret")
            or os.getenv("WECHAT_APP_SECRET")
            or os.getenv("WECHAT_SECRET")
        )

        if not app_id or not app_secret:
            return PublishResult(
                platform="wechat",
                status=PublishStatus.FAILED,
                message="缺少 WECHAT_APP_ID 或 WECHAT_APP_SECRET",
            )

        try:
            token = self._get_token(app_id, app_secret)
            html = self._process_content(article, token)
            thumb_id = ""
            if article.cover_image:
                thumb_id = self._upload_cover(article.cover_image, token)

            draft_id = self._post_draft(token, {
                "title": article.title,
                "author": article.author,
                "digest": article.digest,
                "content": html,
                "content_source_url": "",
                "thumb_media_id": thumb_id,
                "need_open_comment": 0,
                "only_fans_can_comment": 0,
            })
            return PublishResult(
                platform="wechat",
                status=PublishStatus.SUCCESS,
                platform_id=draft_id,
                message=f"草稿已创建: {draft_id}",
            )
        except Exception as e:
            return PublishResult(
                platform="wechat",
                status=PublishStatus.FAILED,
                message=str(e),
            )

    # -- token 管理 --

    def _get_token(self, app_id: str, app_secret: str) -> str:
        if self._access_token and time.time() < self._token_expires_at:
            return self._access_token

        url = (
            "https://api.weixin.qq.com/cgi-bin/token"
            f"?grant_type=client_credential&appid={app_id}&secret={app_secret}"
        )
        resp = requests.get(url, timeout=HTTP_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        if "access_token" not in data:
            raise RuntimeError(f"获取 access_token 失败: {data}")

        self._access_token = data["access_token"]
        self._token_expires_at = time.time() + data["expires_in"] - 200
        return self._access_token

    # -- 内容处理 --

    def _process_content(self, article: Article, token: str) -> str:
        """Markdown → HTML，处理内容中的本地图片"""
        content = article.content
        base_dir = os.path.dirname(article.source_path) if article.source_path else "."

        def replace_image(match):
            alt_text = match.group(1)
            img_path = match.group(2)
            if not img_path.startswith(("http://", "https://")):
                abs_path = os.path.join(base_dir, img_path)
                if os.path.exists(abs_path):
                    try:
                        wechat_url = self._upload_image(abs_path, token)
                        return f"![{alt_text}]({wechat_url})"
                    except Exception as e:
                        print(f"[wechat] 图片上传失败 {abs_path}: {e}")
            return match.group(0)

        content = re.sub(r"!\[(.*?)\]\((.*?)\)", replace_image, content)
        return markdown.markdown(content)

    # -- 图片上传 --

    def _upload_image(self, file_path: str, token: str) -> str:
        """上传内容图片，返回 URL"""
        url = f"https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token={token}"
        with open(file_path, "rb") as f:
            resp = requests.post(url, files={"media": f}, timeout=HTTP_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
        if "url" not in data:
            raise RuntimeError(f"上传内容图片失败: {data}")
        return data["url"]

    def _upload_cover(self, file_path: str, token: str) -> str:
        """上传封面图片，返回 media_id"""
        url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={token}&type=image"
        with open(file_path, "rb") as f:
            resp = requests.post(url, files={"media": f}, timeout=HTTP_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
        if "media_id" not in data:
            raise RuntimeError(f"上传封面图片失败: {data}")
        return data["media_id"]

    # -- 草稿发布 --

    def _post_draft(self, token: str, article_dict: dict) -> str:
        """发布到草稿箱，返回 media_id"""
        url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}"
        payload = {"articles": [article_dict]}
        resp = requests.post(
            url,
            json=payload,
            timeout=HTTP_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        if "media_id" not in data:
            raise RuntimeError(f"发布草稿失败: {data}")
        return data["media_id"]
