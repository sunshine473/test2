"""test_bot_agent.py — agent.py 单元测试"""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from bot.agent import handle_message, MAX_TOOL_ROUNDS


class TestHandleMessage:
    def test_no_api_key(self, monkeypatch):
        """无 CLAUDE_API_KEY 返回错误提示。"""
        monkeypatch.setattr("bot.agent.CLAUDE_API_KEY", "")
        result = handle_message("你好")
        assert "CLAUDE_API_KEY" in result

    @patch("bot.agent._build_client")
    def test_text_reply(self, mock_build, monkeypatch):
        """mock Claude API 返回纯文本。"""
        monkeypatch.setattr("bot.agent.CLAUDE_API_KEY", "fake-key")

        text_block = SimpleNamespace(type="text", text="你好，有什么可以帮你的？")
        mock_response = SimpleNamespace(
            content=[text_block],
            stop_reason="end_turn",
        )
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_build.return_value = mock_client

        result = handle_message("你好")
        assert "你好" in result

    @patch("bot.agent.execute_tool")
    @patch("bot.agent._build_client")
    def test_tool_use(self, mock_build, mock_exec, monkeypatch):
        """mock Claude API 返回 tool_use → 执行 → 再返回文本。"""
        monkeypatch.setattr("bot.agent.CLAUDE_API_KEY", "fake-key")

        tool_block = SimpleNamespace(
            type="tool_use", name="check_pool", input={}, id="tool_1"
        )
        # 第一次调用：返回 tool_use
        resp1 = SimpleNamespace(
            content=[tool_block],
            stop_reason="tool_use",
        )
        # 第二次调用：返回纯文本
        text_block = SimpleNamespace(type="text", text="素材池有 30 条数据")
        resp2 = SimpleNamespace(
            content=[text_block],
            stop_reason="end_turn",
        )

        mock_client = MagicMock()
        mock_client.messages.create.side_effect = [resp1, resp2]
        mock_build.return_value = mock_client
        mock_exec.return_value = '{"status": "ok", "total": 30}'

        result = handle_message("查看素材池")
        assert "30" in result
        mock_exec.assert_called_once_with("check_pool", {})

    @patch("bot.agent._build_client")
    def test_max_rounds(self, mock_build, monkeypatch):
        """10 轮后返回上限提示。"""
        monkeypatch.setattr("bot.agent.CLAUDE_API_KEY", "fake-key")

        tool_block = SimpleNamespace(
            type="tool_use", name="check_pool", input={}, id="tool_1"
        )
        mock_response = SimpleNamespace(
            content=[tool_block],
            stop_reason="tool_use",
        )

        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_build.return_value = mock_client

        with patch("bot.agent.execute_tool", return_value='{"ok": true}'):
            result = handle_message("无限循环")

        assert "上限" in result
        assert mock_client.messages.create.call_count == MAX_TOOL_ROUNDS
