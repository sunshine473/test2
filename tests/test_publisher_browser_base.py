from publisher.platforms.browser_base import BrowserPublisher
from publisher.platforms.dongchedi import DongchediPublisher
from publisher.models import Article


class DummyPublisher(BrowserPublisher):
    name = "zhihu"
    editor_url = "https://zhuanlan.zhihu.com/write"


class DummyContext:
    def __init__(self):
        self.cookies = None

    def add_cookies(self, cookies):
        self.cookies = cookies


def test_load_cookies_from_env(monkeypatch):
    monkeypatch.setenv("ZHIHU_COOKIE", "a=1; b=2")
    context = DummyContext()

    DummyPublisher()._load_cookies_from_env(context)

    assert context.cookies == [
        {"name": "a", "value": "1", "url": "https://zhuanlan.zhihu.com"},
        {"name": "b", "value": "2", "url": "https://zhuanlan.zhihu.com"},
    ]


def test_load_cookies_from_env_ignores_missing(monkeypatch):
    monkeypatch.delenv("ZHIHU_COOKIE", raising=False)
    context = DummyContext()

    DummyPublisher()._load_cookies_from_env(context)

    assert context.cookies is None


class LoginPage:
    url = "https://example.com/login"

    def __init__(self):
        self.reload_count = 0

    def goto(self, *args, **kwargs):
        return None

    def reload(self, *args, **kwargs):
        self.reload_count += 1


def test_check_login_fails_fast_in_headless(monkeypatch):
    monkeypatch.setattr(DummyPublisher, "_random_delay", lambda *args, **kwargs: None)
    page = LoginPage()

    assert DummyPublisher()._check_login(page, {"_headless": True}) is False
    assert page.reload_count == 0


class FakeLocator:
    def __init__(self, visible=True, value="", text=""):
        self.visible = visible
        self.value = value
        self.text = text
        self.first = self
        self.clicked = False
        self.filled = None

    def is_visible(self, timeout=None):
        return self.visible

    def input_value(self, timeout=None):
        return self.value

    def inner_text(self, timeout=None):
        return self.text

    def click(self):
        self.clicked = True

    def fill(self, value, timeout=None):
        self.filled = value
        self.value = value
        self.text = value

    def wait_for(self, state=None, timeout=None):
        return None


class DongchediPage:
    url = "https://mp.dcdapp.com/profile_v2/publish/post"

    def __init__(self, editor_visible=True, dynamic_text=""):
        self.editor_locator = FakeLocator(visible=editor_visible, value=dynamic_text, text=dynamic_text)
        self.login_locator = FakeLocator(visible=False)

    def locator(self, selector):
        if "ProseMirror" in selector:
            return self.editor_locator
        return self.login_locator


def test_dongchedi_uses_dcdapp_dynamic_backend():
    publisher = DongchediPublisher()

    assert publisher.editor_url == "https://mp.dcdapp.com/profile_v2/publish/post"
    assert publisher.manage_url == "https://mp.dcdapp.com/profile_v2/manage/content/posts"
    assert "https://mp.dcdapp.com" in publisher.cookie_origins


def test_check_login_requires_editor_when_configured(monkeypatch):
    monkeypatch.setattr(DongchediPublisher, "_random_delay", lambda *args, **kwargs: None)
    page = DongchediPage(editor_visible=False)

    assert DongchediPublisher()._check_login(page, {"_headless": True}) is False


def test_dongchedi_logged_in_requires_dynamic_editor():
    publisher = DongchediPublisher()

    assert publisher._is_logged_in(DongchediPage(editor_visible=True)) is True
    assert publisher._is_logged_in(DongchediPage(editor_visible=False)) is False


def test_dongchedi_dynamic_content_visible():
    publisher = DongchediPublisher()
    page = DongchediPage(dynamic_text="测试动态正文很长，足够用于校验")

    assert publisher._dynamic_content_visible(page, "测试动态正文很长，足够用于校验") is True
    assert publisher._dynamic_content_visible(page, "另一个正文") is False


def test_dongchedi_build_dynamic_text_strips_markdown_and_limits_length():
    publisher = DongchediPublisher()
    article = Article(
        title="测试标题",
        content="---\ntitle: old\n---\n# 测试标题\n\n正文内容\n\n![图](x.png)\n\n" + "很长" * 1200,
    )

    dynamic_text = publisher._build_dynamic_text(article)

    assert dynamic_text.startswith("测试标题")
    assert "![图]" not in dynamic_text
    assert dynamic_text.endswith("#星河创造营")
    assert dynamic_text.count("#星河创造营") == 1
    assert len(dynamic_text) <= 2000


def test_dongchedi_stops_before_mutating_editor_without_draft_support():
    publisher = DongchediPublisher()
    page = DongchediPage()
    article = Article(title="测试标题", content="测试正文", images=["cover.jpg"])

    result = publisher._do_publish(page, article, {})

    assert result.status.value == "failed"
    assert "动态页没有草稿入口" in result.message
    assert page.editor_locator.filled is None
