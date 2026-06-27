"""SubtitleCat Provider 模块。

SubtitleCat (https://subtitlecat.com) 字幕网站的 Provider 实现。
负责搜索和下载中文字幕。

核心流程：
    1. search() —— 搜索 → 解析 → 评分 → 返回全部结果
    2. get_download_url() —— 打开字幕页 → 解析下载链接 → 返回 URL

所有依赖通过构造器注入（Constructor Injection），不使用 setter。
"""

import logging
from typing import Optional
from urllib.parse import quote_plus

from src.browser import BrowserManager
from src.providers.base import BaseProvider
from src.utils.matcher import choose_best
from src.utils.parser import parse_download_url
from src.utils.parser import parse_search_results

logger = logging.getLogger(__name__)


class SubtitleCatProvider(BaseProvider):
    """SubtitleCat 字幕网站 Provider。

    继承 BaseProvider，实现 SubtitleCat 网站的字幕搜索和下载逻辑。

    BrowserManager 通过构造器注入，Provider 不管理浏览器生命周期。

    Attributes:
        browser: BrowserManager 实例，用于打开页面。
    """

    BASE_URL: str = "https://subtitlecat.com"

    def __init__(
        self,
        browser: BrowserManager,
        language: str = "zh-CN",
    ) -> None:
        """初始化 SubtitleCat Provider。

        Args:
            browser: BrowserManager 实例（必须，用于页面导航）。
            language: 目标语言代码，默认为 "zh-CN"。
        """
        super().__init__(
            name="SubtitleCat",
            base_url=self.BASE_URL,
            language=language,
        )
        self.browser: BrowserManager = browser

    # ------------------------------------------------------------------
    # search
    # ------------------------------------------------------------------

    def search(self, movie_title: str, year: Optional[int] = None) -> list[dict]:
        """在 SubtitleCat 上搜索指定电影的字幕。

        流程：
            1. 构造搜索 URL → …/index.php?search={movie_title}
            2. 通过 BrowserManager 打开搜索页面
            3. 使用 parse_search_results() 解析 HTML
            4. 使用 choose_best() 评分并选出最佳匹配
            5. 返回包含评分的全部搜索结果

        Args:
            movie_title: 电影名称。
            year: 电影发行年份（可选，用于精确匹配评分）。

        Returns:
            包含评分的字幕资源字典列表。搜索失败时返回空列表。
        """
        logger.info("Searching: %s", movie_title)

        search_url = (
            f"{self.base_url}/index.php?search={quote_plus(movie_title)}"
        )

        page = self.browser.open(search_url)
        if page is None:
            return []

        try:
            html = page.content()
            results = parse_search_results(html)
            logger.info("Found: %d results", len(results))

            best = choose_best(results, movie_title, year)
            logger.info("Best Match:")
            if best:
                logger.info(best["title"])
            else:
                logger.info("(none)")

            return results
        except Exception:
            logger.warning("搜索解析异常", exc_info=True)
            return []
        finally:
            page.close()

    # ------------------------------------------------------------------
    # get_download_url
    # ------------------------------------------------------------------

    def get_download_url(self, subtitle_url: str) -> Optional[str]:
        """获取 SubtitleCat 字幕文件的直接下载链接。

        流程：
            1. 打开字幕详情页
            2. 查找 id="download_{language}" 的 <a> 标签
            3. 拼接为完整 URL 并返回，未找到则返回 None

        Args:
            subtitle_url: 字幕详情页面的 URL（相对或绝对路径）。

        Returns:
            完整下载 URL，目标语言字幕不存在时返回 None。
        """
        logger.info("Subtitle Download:")

        full_url = subtitle_url
        if not full_url.startswith("http"):
            full_url = f"{self.base_url}/{subtitle_url.lstrip('/')}"

        page = self.browser.open(full_url)
        if page is None:
            return None

        try:
            html = page.content()
            download_href = parse_download_url(html, language=self.language)

            if download_href:
                if not download_href.startswith("http"):
                    download_href = f"{self.base_url}{download_href}"
                logger.info("Found %s", self.language)
                return download_href
            else:
                logger.info("No %s subtitle", self.language)
                return None
        except Exception:
            logger.warning("下载链接解析异常", exc_info=True)
            return None
        finally:
            page.close()
