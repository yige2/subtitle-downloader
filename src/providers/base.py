"""Provider 基类模块。

定义了所有字幕网站 Provider 必须实现的统一接口。
通过继承 BaseProvider 并实现抽象方法，即可添加对新字幕网站的支持。
"""

import logging
from abc import ABC
from abc import abstractmethod
from typing import Optional

logger = logging.getLogger(__name__)


class BaseProvider(ABC):
    """字幕网站 Provider 的抽象基类。

    所有字幕网站的具体实现都必须继承此类，
    并实现 search() 和 get_download_url() 方法。

    Attributes:
        name: Provider 的显示名称（如 "SubtitleCat"）。
        base_url: 字幕网站的基础 URL。
        language: 目标语言代码（如 "zh-CN"）。
    """

    def __init__(self, name: str, base_url: str, language: str = "zh-CN") -> None:
        """初始化 Provider。

        Args:
            name: Provider 的显示名称。
            base_url: 字幕网站的基础 URL。
            language: 目标语言代码，默认为 "zh-CN"。
        """
        self.name: str = name
        self.base_url: str = base_url
        self.language: str = language
        logger.info("初始化 Provider: %s (base_url=%s, language=%s)",
                     self.name, self.base_url, self.language)

    @abstractmethod
    def search(self, movie_title: str, year: Optional[int] = None) -> list[dict]:
        """在字幕网站上搜索指定电影的字幕资源。

        Args:
            movie_title: 电影名称。
            year: 电影发行年份（可选，用于精确匹配）。

        Returns:
            包含字幕资源信息的字典列表，每个字典至少包含：
                - title: 字幕标题
                - language: 语言代码
                - url: 字幕详情页 URL
                - downloads: 下载次数（如可获取）

        Raises:
            NotImplementedError: 子类必须实现此方法。
        """
        raise NotImplementedError

    @abstractmethod
    def get_download_url(self, subtitle_url: str) -> Optional[str]:
        """获取字幕文件的直接下载链接。

        Args:
            subtitle_url: 字幕详情页面的 URL。

        Returns:
            字幕文件的直接下载 URL，如获取失败则返回 None。

        Raises:
            NotImplementedError: 子类必须实现此方法。
        """
        raise NotImplementedError
