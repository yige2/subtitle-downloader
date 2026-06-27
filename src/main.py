"""项目入口模块。

负责组装依赖（DI）、管理浏览器生命周期、启动服务。

依赖注入链：
    BrowserManager → SubtitleCatProvider → SubtitleService.run()
"""

import logging
import sys

from src.browser import BrowserManager
from src.config import Config
from src.downloader import SubtitleDownloader
from src.logger import setup_logger
from src.providers.subtitlecat import SubtitleCatProvider
from src.service import SubtitleService

logger = logging.getLogger(__name__)


def main() -> None:
    """应用程序主入口函数。

    流程：
        1. 初始化日志、确保目录
        2. 创建 BrowserManager（启动 Playwright）
        3. 创建 SubtitleCatProvider（注入 browser）
        4. 创建 SubtitleDownloader
        5. 创建 SubtitleService（注入 provider + downloader）
        6. browser.start() → service.run() → finally: browser.stop()
    """
    setup_logger()
    Config.ensure_directories()

    print("=" * 50)
    print("  Subtitle Downloader v1.0")
    print("  批量字幕下载工具")
    print("=" * 50)
    logger.info("Subtitle Downloader v1.0 启动")

    browser = BrowserManager(headless=Config.HEADLESS)
    provider = SubtitleCatProvider(
        browser=browser,
        language=Config.TARGET_LANGUAGE,
    )
    downloader = SubtitleDownloader()
    service = SubtitleService(provider=provider, downloader=downloader)

    browser.start()
    try:
        service.run()
    finally:
        browser.stop()

    logger.info("Subtitle Downloader v1.0 正常退出。")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("用户中断，程序退出。")
        sys.exit(0)
    except Exception:
        logger.exception("程序运行异常")
        sys.exit(1)

