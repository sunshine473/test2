import requests
import json
import time


HTTP_TIMEOUT = 20

class WeChatClient:
    def __init__(self, app_id, app_secret):
        self.app_id = app_id
        self.app_secret = app_secret
        self.access_token = None
        self.token_expires_at = 0

    def get_access_token(self):
        if self.access_token and time.time() < self.token_expires_at:
            return self.access_token

        url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={self.app_id}&secret={self.app_secret}"
        try:
            response = requests.get(url, timeout=HTTP_TIMEOUT)
            response.raise_for_status()
            data = response.json()

            if "access_token" in data:
                self.access_token = data["access_token"]
                self.token_expires_at = time.time() + data["expires_in"] - 200 # Buffer
                return self.access_token
            else:
                raise Exception(f"Failed to get access token: {data}")
        except requests.RequestException as e:
            raise Exception(f"Network error getting access token: {str(e)}")
        except Exception as e:
            raise Exception(f"Network error getting access token: {str(e)}")

    def upload_image(self, file_path):
        """Uploads an image to be used within the article content (returns URL)"""
        token = self.get_access_token()
        url = f"https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token={token}"

        try:
            with open(file_path, 'rb') as f:
                files = {'media': f}
                response = requests.post(url, files=files, timeout=HTTP_TIMEOUT)
                response.raise_for_status()

            data = response.json()
            if "url" in data:
                return data["url"]
            else:
                raise Exception(f"Failed to upload content image: {data}")
        except FileNotFoundError:
            raise Exception(f"Image file not found: {file_path}")
        except requests.RequestException as e:
            raise Exception(f"Network error uploading image: {str(e)}")

    def upload_cover(self, file_path):
        """Uploads an image to be used as cover (returns media_id)"""
        # Using permanent material for cover
        token = self.get_access_token()
        url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={token}&type=image"

        try:
            with open(file_path, 'rb') as f:
                files = {'media': f}
                response = requests.post(url, files=files, timeout=HTTP_TIMEOUT)
                response.raise_for_status()

            data = response.json()
            if "media_id" in data:
                return data["media_id"]
            else:
                raise Exception(f"Failed to upload cover image: {data}")
        except FileNotFoundError:
            raise Exception(f"Cover image file not found: {file_path}")
        except requests.RequestException as e:
            raise Exception(f"Network error uploading cover: {str(e)}")

    def post_draft(self, articles):
        """
        articles: list of dicts with keys: title, author, digest, content, content_source_url, thumb_media_id, need_open_comment, only_fans_can_comment
        """
        token = self.get_access_token()
        url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}"

        payload = {
            "articles": articles
        }

        # Ensure UTF-8 encoding for Chinese characters
        try:
            response = requests.post(url, json=payload, timeout=HTTP_TIMEOUT)
            response.raise_for_status()
            data = response.json()

            if "media_id" in data:
                return data["media_id"]
            else:
                raise Exception(f"Failed to post draft: {data}")
        except requests.RequestException as e:
            raise Exception(f"Network error posting draft: {str(e)}")
        except Exception as e:
            raise Exception(f"Error posting draft: {str(e)}")
