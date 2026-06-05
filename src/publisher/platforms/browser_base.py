"""Playwright 浏览器自动化基类 — 知乎/头条/小红书/懂车帝共用"""

import os
import random
import time
from pathlib import Path
from urllib.parse import urlparse

from publisher.base import BasePublisher
from publisher.models import Article, PublishResult, PublishStatus

BROWSER_STATE_DIR = Path(__file__).resolve().parent.parent.parent.parent / ".browser_state"


class BrowserPublisher(BasePublisher):
    """基于 Playwright 的发布适配器基类

    子类只需覆盖 login_url、editor_url 和 _do_publish 方法。
    Cookie 自动持久化到 .browser_state/ 目录。
    首次运行会打开浏览器引导手动登录。
    """

    login_url: str = ""
    editor_url: str = ""
    cookie_origins: list = []  # 额外需要注入 cookie 的域名
    require_logged_in_editor: bool = False

    def publish(self, article: Article, config: dict) -> PublishResult:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            return PublishResult(
                platform=self.name,
                status=PublishStatus.SKIPPED,
                message="需要安装: pip install playwright && playwright install chromium",
            )

        headless = config.get("headless")
        if headless is None:
            headless = os.getenv("CI", "").lower() == "true"
        config = {**config, "_headless": headless}
        state_file = BROWSER_STATE_DIR / f"{self.name}_state.json"

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=headless)
            context = browser.new_context(
                storage_state=str(state_file) if state_file.exists() else None,
                viewport={"width": 1280, "height": 800},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            )
            self._load_cookies_from_env(context)
            # 注入 stealth 脚本
            try:
                from playwright_stealth import stealth_sync
                page = context.new_page()
                stealth_sync(page)
            except ImportError:
                page = context.new_page()

            try:
                # 检查登录状态
                if not self._check_login(page, config):
                    if config.get("_headless"):
                        message = f"{self.name.upper()}_COOKIE 无效或已过期，headless 模式无法手动登录"
                    else:
                        message = "未登录，请重新运行（浏览器会打开登录页面）"
                    return PublishResult(
                        platform=self.name,
                        status=PublishStatus.FAILED,
                        message=message,
                    )

                # 登录成功后立即保存 Cookie（防止后续步骤出错丢失登录态）
                BROWSER_STATE_DIR.mkdir(parents=True, exist_ok=True)
                context.storage_state(path=str(state_file))

                result = self._do_publish(page, article, config)
                # 发布完成后再次保存（可能有新的 Cookie）
                context.storage_state(path=str(state_file))
                return result
            except Exception as e:
                return PublishResult(
                    platform=self.name,
                    status=PublishStatus.FAILED,
                    message=str(e),
                )
            finally:
                browser.close()

    def _check_login(self, page, config: dict) -> bool:
        """检查登录状态，未登录则引导手动登录"""
        try:
            page.goto(self.editor_url, wait_until="domcontentloaded", timeout=30000)
        except Exception:
            pass  # 超时也继续，页面可能已部分加载
        self._random_delay(3, 5)

        if self._is_logged_in(page):
            return True

        # 如果被重定向到登录页，等待用户手动登录
        if self._is_login_page(page) and not self._is_logged_in(page):
            if config.get("_headless"):
                print(f"[{self.name}] headless 模式检测到登录页面，Cookie 可能已失效")
                return False

            print(f"[{self.name}] 检测到登录页面，请在浏览器中手动登录...")
            print(f"[{self.name}] 登录完成后会自动继续（最多等待 300 秒）")
            for _ in range(150):
                time.sleep(2)
                if self._is_logged_in(page):
                    print(f"[{self.name}] 登录成功！")
                    self._random_delay(3, 5)
                    # 登录后重新导航到编辑器
                    try:
                        page.goto(self.editor_url, wait_until="domcontentloaded", timeout=30000)
                    except Exception:
                        pass
                    self._random_delay(3, 5)
                    return self._is_logged_in(page) if self.require_logged_in_editor else True
                if not self.require_logged_in_editor and not self._is_login_page(page):
                    print(f"[{self.name}] 登录成功！")
                    self._random_delay(3, 5)
                    # 登录后重新导航到编辑器
                    try:
                        page.goto(self.editor_url, wait_until="domcontentloaded", timeout=30000)
                    except Exception:
                        pass
                    self._random_delay(3, 5)
                    return True
                if self.require_logged_in_editor and not self._is_login_page(page):
                    try:
                        page.goto(self.editor_url, wait_until="domcontentloaded", timeout=30000)
                    except Exception:
                        pass
                    self._random_delay(3, 5)
                    if self._is_logged_in(page):
                        print(f"[{self.name}] 登录成功！")
                        return True
            return False
        if self.require_logged_in_editor:
            if config.get("_headless"):
                print(f"[{self.name}] headless 模式未检测到编辑器，Cookie 可能已失效或账号无权限")
                return False
            print(f"[{self.name}] 未检测到编辑器，请在浏览器中完成登录或确认账号权限...")
            for _ in range(150):
                time.sleep(2)
                try:
                    page.goto(self.editor_url, wait_until="domcontentloaded", timeout=15000)
                except Exception:
                    pass
                if self._is_logged_in(page):
                    print(f"[{self.name}] 登录成功！")
                    self._random_delay(3, 5)
                    return True
            return False
        return True

    def _is_login_page(self, page) -> bool:
        """判断当前是否在登录页，子类可覆盖"""
        url = page.url.lower()
        return "login" in url or "signin" in url or "sign-in" in url

    def _is_logged_in(self, page) -> bool:
        """判断是否已经登录，子类可覆盖更精确的检测逻辑。"""
        return False

    def _do_publish(self, page, article: Article, config: dict) -> PublishResult:
        """子类实现具体的页面操作"""
        raise NotImplementedError

    @staticmethod
    def _random_delay(min_s: float = 0.5, max_s: float = 1.5):
        """随机延迟，模拟人类操作"""
        time.sleep(random.uniform(min_s, max_s))

    @staticmethod
    def _type_slowly(page, selector: str, text: str, delay: int = 50):
        """模拟人类打字速度"""
        page.click(selector)
        page.type(selector, text, delay=delay)

    def _load_cookies_from_env(self, context) -> None:
        cookie_env = f"{self.name.upper()}_COOKIE"
        raw_cookie = os.getenv(cookie_env, "").strip()
        if not raw_cookie:
            return

        target = self.editor_url or self.login_url
        if not target:
            return

        parsed = urlparse(target)
        primary_origin = f"{parsed.scheme}://{parsed.netloc}"
        # 注入到主域 + 所有额外域名
        origins = [primary_origin] + [o for o in (self.cookie_origins or []) if o != primary_origin]

        raw_pairs = []
        for part in raw_cookie.split(";"):
            item = part.strip()
            if not item or "=" not in item:
                continue
            name, value = item.split("=", 1)
            name = name.strip()
            if not name:
                continue
            raw_pairs.append((name, value.strip()))

        if not raw_pairs:
            return

        cookies = []
        for origin in origins:
            for name, value in raw_pairs:
                cookies.append({"name": name, "value": value, "url": origin})

        context.add_cookies(cookies)
