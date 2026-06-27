"""字幕下载 Provider 包。

该包包含所有字幕网站 Provider 的基类和具体实现。
通过 Provider 架构，可以轻松添加新的字幕网站支持。
"""

from src.providers.base import BaseProvider
from src.providers.subtitlecat import SubtitleCatProvider

__all__ = ["BaseProvider", "SubtitleCatProvider"]
