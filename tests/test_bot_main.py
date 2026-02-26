"""test_bot_main.py — main.py 单元测试"""

from pathlib import Path

from bot.main import load_offset, save_offset, is_authorized


class TestLoadOffset:
    def test_file_not_exist(self, monkeypatch, tmp_path):
        """文件不存在返回 None。"""
        monkeypatch.setattr("bot.main.OFFSET_FILE", tmp_path / "nonexistent.txt")
        assert load_offset() is None

    def test_valid(self, monkeypatch, tmp_path):
        """正常读取数字 offset。"""
        f = tmp_path / "offset.txt"
        f.write_text("12345")
        monkeypatch.setattr("bot.main.OFFSET_FILE", f)
        assert load_offset() == 12345

    def test_invalid_content(self, monkeypatch, tmp_path):
        """非数字内容（如 'None'）返回 None。"""
        f = tmp_path / "offset.txt"
        f.write_text("None")
        monkeypatch.setattr("bot.main.OFFSET_FILE", f)
        assert load_offset() is None

    def test_empty_file(self, monkeypatch, tmp_path):
        """空文件返回 None。"""
        f = tmp_path / "offset.txt"
        f.write_text("")
        monkeypatch.setattr("bot.main.OFFSET_FILE", f)
        assert load_offset() is None


class TestSaveOffset:
    def test_save_and_read(self, monkeypatch, tmp_path):
        """写入并验证。"""
        f = tmp_path / "state" / "offset.txt"
        monkeypatch.setattr("bot.main.OFFSET_FILE", f)
        save_offset(99999)
        assert f.read_text() == "99999"

    def test_creates_parent_dir(self, monkeypatch, tmp_path):
        """自动创建父目录。"""
        f = tmp_path / "deep" / "nested" / "offset.txt"
        monkeypatch.setattr("bot.main.OFFSET_FILE", f)
        save_offset(42)
        assert f.exists()
        assert f.read_text() == "42"


class TestIsAuthorized:
    def test_match(self, monkeypatch):
        """chat_id 匹配返回 True。"""
        monkeypatch.setattr("bot.main.AUTHORIZED_CHAT_ID", "12345")
        assert is_authorized(12345) is True
        assert is_authorized("12345") is True

    def test_no_match(self, monkeypatch):
        """chat_id 不匹配返回 False。"""
        monkeypatch.setattr("bot.main.AUTHORIZED_CHAT_ID", "12345")
        assert is_authorized(99999) is False

    def test_empty_config(self, monkeypatch):
        """未配置 AUTHORIZED_CHAT_ID 返回 False。"""
        monkeypatch.setattr("bot.main.AUTHORIZED_CHAT_ID", "")
        assert is_authorized(12345) is False
