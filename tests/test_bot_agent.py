"""test_bot_agent.py — agent.py 双模型 fallback 单元测试"""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from bot.agent import handle_message, MAX_TOOL_ROUNDS


class TestHandleMessageClaude:
    """Claude 主力路径测试。"""

    @patch("bot.agent._build_claude_client")
    def test_claude_text_reply(self, mock_build, monkeypatch):
        """Claude 返回纯文本，不走 Gemini。"""
        monkeypatch.setattr("bot.agent.CLAUDE_API_KEY", "fake-claude-key")
        monkeypatch.setattr("bot.agent.GEMINI_API_KEY", "fake-gemini-key")

        text_block = SimpleNamespace(type="text", text="你好，有什么可以帮你的？")
        mock_response = SimpleNamespace(content=[text_block])
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_build.return_value = mock_client

        result = handle_message("你好")
        assert "你好" in result
        mock_client.messages.create.assert_called_once()

    @patch("bot.agent.execute_tool")
    @patch("bot.agent._build_claude_client")
    def test_claude_tool_use(self, mock_build, mock_exec, monkeypatch):
        """Claude 返回 tool_use → 执行 → 再返回文本。"""
        monkeypatch.setattr("bot.agent.CLAUDE_API_KEY", "fake-claude-key")
        monkeypatch.setattr("bot.agent.GEMINI_API_KEY", "fake-gemini-key")

        tool_block = SimpleNamespace(
            type="tool_use", id="tu_1", name="check_pool", input={}
        )
        resp1 = SimpleNamespace(content=[tool_block])
        text_block = SimpleNamespace(type="text", text="素材池有 30 条数据")
        resp2 = SimpleNamespace(content=[text_block])

        mock_client = MagicMock()
        mock_client.messages.create.side_effect = [resp1, resp2]
        mock_build.return_value = mock_client
        mock_exec.return_value = '{"status": "ok", "total": 30}'

        result = handle_message("查看素材池")
        assert "30" in result
        mock_exec.assert_called_once_with("check_pool", {})

    @patch("bot.agent._build_claude_client")
    def test_claude_max_rounds(self, mock_build, monkeypatch):
        """Claude tool loop 达到上限。"""
        monkeypatch.setattr("bot.agent.CLAUDE_API_KEY", "fake-claude-key")
        monkeypatch.setattr("bot.agent.GEMINI_API_KEY", "")

        tool_block = SimpleNamespace(
            type="tool_use", id="tu_1", name="check_pool", input={}
        )
        mock_response = SimpleNamespace(content=[tool_block])
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_build.return_value = mock_client

        with patch("bot.agent.execute_tool", return_value='{"ok": true}'):
            result = handle_message("无限循环")

        assert "上限" in result
        assert mock_client.messages.create.call_count == MAX_TOOL_ROUNDS


class TestHandleMessageFallback:
    """Claude 失败 → Gemini fallback 测试。"""

    @patch("bot.agent._build_gemini_client")
    @patch("bot.agent._build_claude_client")
    def test_claude_fail_fallback_gemini(self, mock_claude_build, mock_gemini_build, monkeypatch):
        """Claude 抛异常后 fallback 到 Gemini。"""
        monkeypatch.setattr("bot.agent.CLAUDE_API_KEY", "fake-claude-key")
        monkeypatch.setattr("bot.agent.GEMINI_API_KEY", "fake-gemini-key")

        # Claude 抛超时异常
        mock_claude_client = MagicMock()
        mock_claude_client.messages.create.side_effect = Exception("timeout")
        mock_claude_build.return_value = mock_claude_client

        # Gemini 正常返回
        text_block = SimpleNamespace(text="Gemini 回复你好", function_call=None)
        candidate = SimpleNamespace(content=SimpleNamespace(parts=[text_block]))
        mock_gemini_response = SimpleNamespace(candidates=[candidate])
        mock_gemini_client = MagicMock()
        mock_gemini_client.models.generate_content.return_value = mock_gemini_response
        mock_gemini_build.return_value = mock_gemini_client

        result = handle_message("你好")
        assert "Gemini" in result
        mock_claude_client.messages.create.assert_called_once()
        mock_gemini_client.models.generate_content.assert_called_once()

    def test_no_api_keys(self, monkeypatch):
        """两个 API Key 都没配置时返回错误。"""
        monkeypatch.setattr("bot.agent.CLAUDE_API_KEY", "")
        monkeypatch.setattr("bot.agent.GEMINI_API_KEY", "")
        result = handle_message("你好")
        assert "未配置" in result

    @patch("bot.agent._build_gemini_client")
    def test_gemini_only(self, mock_build, monkeypatch):
        """只有 Gemini Key 时直接走 Gemini。"""
        monkeypatch.setattr("bot.agent.CLAUDE_API_KEY", "")
        monkeypatch.setattr("bot.agent.GEMINI_API_KEY", "fake-gemini-key")

        text_block = SimpleNamespace(text="Gemini 回复", function_call=None)
        candidate = SimpleNamespace(content=SimpleNamespace(parts=[text_block]))
        mock_response = SimpleNamespace(candidates=[candidate])
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        mock_build.return_value = mock_client

        result = handle_message("你好")
        assert "Gemini" in result
