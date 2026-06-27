"""Playwright 浏览器管理模块。

封装 Playwright 的生命周期管理，提供便捷的浏览器启动、页面创建和资源释放接口。
"""

import logging
from typing import Any
from typing import Optional

from playwright.sync_api import Browser
from playwright.sync_api import BrowserContext
from playwright.sync_api import Page
from playwright.sync_api import Playwright
from playwright.sync_api import sync_playwright

from src.config import Config

logger = logging.getLogger(__name__)


class BrowserManager:
    """Playwright 浏览器实例管理器。

    负责管理 Playwright 的完整生命周期，包括启动浏览器、
    创建页面、导航以及资源清理。

    Attributes:
        playwright: Playwright 入口实例。
        browser: Chromium 浏览器实例。
        context: 浏览器上下文。
        _headless: 是否以无头模式运行。
    """

    def __init__(self, headless: bool = True) -> None:
        """初始化 BrowserManager。

        Args:
            headless: 是否以无头模式启动浏览器。
        """
        self._headless: bool = headless
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None

    @property
    def playwright(self) -> Playwright:
        """返回 Playwright 实例。"""
        if self._playwright is None:
            raise RuntimeError("BrowserManager 尚未启动，请先调用 start()")
        return self._playwright

    @property
    def browser(self) -> Browser:
        """返回浏览器实例。"""
        if self._browser is None:
            raise RuntimeError("Browser 尚未启动，请先调用 start()")
        return self._browser

    @property
    def context(self) -> BrowserContext:
        """返回浏览器上下文。"""
        if self._context is None:
            raise RuntimeError("BrowserContext 尚未创建，请先调用 start()")
        return self._context

    def start(self) -> None:
        """启动 Playwright 并打开 Chromium 浏览器。

        创建浏览器上下文，设置默认超时和视口尺寸。
        使用同步 API 以简化调用方的代码。

        Raises:
            RuntimeError: 当 Playwright 无法启动或浏览器无法启动时抛出。
        """
        logger.info("正在启动 Playwright...")
        try:
            self._playwright = sync_playwright().start()
            logger.info("Playwright 启动成功。")

            self._browser = self._playwright.chromium.launch(
                headless=self._headless,
            )
            logger.info("Chromium 浏览器启动成功 (headless=%s)。", self._headless)

            self._context = self._browser.new_context(
                viewport={"width": 1280, "height": 720},
                locale="zh-CN",
            )
            self._context.set_default_timeout(Config.BROWSER_TIMEOUT)
            logger.info("浏览器上下文创建成功。")
        except Exception as exc:
            logger.exception("启动浏览器时发生异常")
            raise RuntimeError("无法启动浏览器") from exc

    def stop(self) -> None:
        """停止 Playwright 并释放所有资源。

        安全地关闭浏览器上下文、浏览器实例和 Playwright 入口。
        即使关闭过程中发生异常也会尝试继续释放剩余资源。
        """
        logger.info("正在关闭 Playwright...")
        resources: list[tuple[str, Optional[Any]]] = [
            ("BrowserContext", self._context),
            ("Browser", self._browser),
            ("Playwright", self._playwright),
        ]

        for name, resource in resources:
            if resource is not None:
                try:
                    # Playwright 用 .stop()，Browser/BrowserContext 用 .close()
                    if name == "Playwright":
                        resource.stop()
                    else:
                        resource.close()
                    logger.debug("%s 已关闭。", name)
                except Exception:
                    logger.exception("关闭 %s 时发生异常", name)
                finally:
                    if name == "BrowserContext":
                        self._context = None
                    elif name == "Browser":
                        self._browser = None
                    elif name == "Playwright":
                        self._playwright = None

        logger.info("Playwright 已完全关闭。")

    def new_page(self) -> Page:
        """在浏览器上下文中创建一个新的空白页面。

        Returns:
            一键 Playwright Page 对象。

        Raises:
            RuntimeError: 如果浏览器尚未启动。
        """
        logger.debug("创建新页面。")
        return self.context.new_page()

    def open(
        self,
        url: str,
        wait_until: str = "domcontentloaded",
    ) -> Optional[Page]:
        """创建一个新页面并导航到指定 URL。

        这是 new_page() + page.goto() 的便捷组合方法。

        Args:
            url: 需要导航到的目标 URL。
            wait_until: Playwright 页面就绪状态。
                默认值为 "domcontentloaded"，不使用 "networkidle"
                以避免在资源较多的页面上等待过长时间。

        Returns:
            已导航到目标 URL 的 Page 对象；导航失败返回 None（不抛异常）。
        """
        logger.info("正在打开页面: %s", url)
        page = self.new_page()
        try:
            page.goto(url, wait_until=wait_until)
            logger.info("页面加载完成: %s", url)
        except Exception:
            logger.warning("页面导航失败: %s", url)
            page.close()
            return None
        return page



