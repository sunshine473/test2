from publisher.platforms.browser_base import BrowserPublisher


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
