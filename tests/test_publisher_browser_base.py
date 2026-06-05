from publisher.platforms.browser_base import BrowserPublisher
from publisher.platforms.dongchedi import DongchediPublisher


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
        self.text = value


class DongchediPage:
    url = "https://mp.dcdapp.com/profile_v2/publish/article"

    def __init__(self, title_visible=True, editor_visible=True, title="", body=""):
        self.title_locator = FakeLocator(visible=title_visible, value=title)
        self.editor_locator = FakeLocator(visible=editor_visible, text=body)
        self.login_locator = FakeLocator(visible=False)

    def locator(self, selector):
        if "标题" in selector:
            return self.title_locator
        if "contenteditable" in selector or "syl-editor" in selector:
            return self.editor_locator
        return self.login_locator


def test_dongchedi_uses_dcdapp_creator_backend():
    publisher = DongchediPublisher()

    assert publisher.editor_url == "https://mp.dcdapp.com/profile_v2/publish/article"
    assert "https://mp.dcdapp.com" in publisher.cookie_origins


def test_check_login_requires_editor_when_configured(monkeypatch):
    monkeypatch.setattr(DongchediPublisher, "_random_delay", lambda *args, **kwargs: None)
    page = DongchediPage(title_visible=False, editor_visible=False)

    assert DongchediPublisher()._check_login(page, {"_headless": True}) is False


def test_dongchedi_logged_in_requires_editor_controls():
    publisher = DongchediPublisher()

    assert publisher._is_logged_in(DongchediPage(title_visible=True, editor_visible=True)) is True
    assert publisher._is_logged_in(DongchediPage(title_visible=True, editor_visible=False)) is False


def test_dongchedi_draft_content_visible():
    publisher = DongchediPublisher()
    page = DongchediPage(title="测试标题", body="正文内容很长，足够用于校验")

    assert publisher._draft_content_visible(page, "测试标题", "正文内容很长，足够用于校验") is True
    assert publisher._draft_content_visible(page, "另一个标题", "正文内容很长，足够用于校验") is False


class KeyboardPage:
    class Keyboard:
        def __init__(self):
            self.inserted = None

        def insert_text(self, value):
            self.inserted = value

    def __init__(self):
        self.keyboard = self.Keyboard()


def test_dongchedi_fill_editor_body_uses_contenteditable_fill(monkeypatch):
    monkeypatch.setattr(DongchediPublisher, "_random_delay", lambda *args, **kwargs: None)
    publisher = DongchediPublisher()
    page = KeyboardPage()
    editor = FakeLocator()

    publisher._fill_editor_body(page, editor, "测试正文")

    assert editor.clicked is True
    assert editor.filled == "测试正文"
    assert page.keyboard.inserted is None
