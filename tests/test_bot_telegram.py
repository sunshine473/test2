"""test_bot_telegram.py — telegram.py 单元测试"""

import pytest
import responses

from bot.telegram import _split_text, get_updates, send_message, MAX_MESSAGE_LENGTH


# --- _split_text ---

class TestSplitText:
    def test_short_text(self):
        """短文本不分段，原样返回。"""
        text = "Hello, world!"
        assert _split_text(text) == [text]

    def test_long_text(self):
        """超 4096 字符按段落边界分段。"""
        # 构造 3 段，每段 2000 字符
        para = "A" * 2000
        text = f"{para}\n{para}\n{para}"
        chunks = _split_text(text)
        assert len(chunks) >= 2
        for chunk in chunks:
            assert len(chunk) <= MAX_MESSAGE_LENGTH

    def test_single_long_line(self):
        """单行超长强制截断。"""
        line = "X" * 10000
        chunks = _split_text(line)
        assert len(chunks) >= 3  # 10000 / 4096 ≈ 3
        for chunk in chunks:
            assert len(chunk) <= MAX_MESSAGE_LENGTH

    def test_exact_boundary(self):
        """恰好 4096 字符不分段。"""
        text = "A" * MAX_MESSAGE_LENGTH
        assert _split_text(text) == [text]


# --- get_updates ---

class TestGetUpdates:
    @responses.activate
    def test_success(self, monkeypatch):
        """mock requests.get，验证正常返回。"""
        monkeypatch.setattr("bot.telegram.BOT_TOKEN", "fake-token")
        monkeypatch.setattr("bot.telegram.BASE_URL", "https://api.telegram.org/botfake-token")

        responses.add(
            responses.GET,
            "https://api.telegram.org/botfake-token/getUpdates",
            json={"ok": True, "result": [{"update_id": 1, "message": {"text": "hi"}}]},
            status=200,
        )

        result = get_updates(offset=None, timeout=5)
        assert len(result) == 1
        assert result[0]["update_id"] == 1

    def test_no_token(self, monkeypatch):
        """token 为空抛 RuntimeError。"""
        monkeypatch.setattr("bot.telegram.BOT_TOKEN", "")
        with pytest.raises(RuntimeError, match="TELEGRAM_BOT_TOKEN"):
            get_updates()


# --- send_message ---

class TestSendMessage:
    @responses.activate
    def test_success(self, monkeypatch):
        """mock requests.post，验证发送成功。"""
        monkeypatch.setattr("bot.telegram.BOT_TOKEN", "fake-token")
        monkeypatch.setattr("bot.telegram.BASE_URL", "https://api.telegram.org/botfake-token")

        responses.add(
            responses.POST,
            "https://api.telegram.org/botfake-token/sendMessage",
            json={"ok": True},
            status=200,
        )

        assert send_message(12345, "Hello") is True

    def test_empty_text(self, monkeypatch):
        """空文本直接返回 True，不发请求。"""
        monkeypatch.setattr("bot.telegram.BOT_TOKEN", "fake-token")
        assert send_message(12345, "   ") is True
