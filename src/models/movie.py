"""电影数据模型模块。

定义 Movie 数据类，用于表示一部待下载字幕的电影。
"""

from dataclasses import dataclass
from dataclasses import field
from typing import Optional


@dataclass
class Movie:
    """表示一部电影及其下载状态。

    Attributes:
        title: 电影名称（如 "Inception"）。
        year: 发行年份，可选。
        subtitle_url: 匹配到的字幕页面 URL，可选。
        download_url: 字幕直接下载链接，可选。
        status: 下载状态：
            - "pending": 等待处理
            - "searching": 正在搜索
            - "found": 已找到字幕
            - "downloading": 正在下载
            - "completed": 下载完成
            - "failed": 下载失败
    """

    title: str
    year: Optional[int] = None
    subtitle_url: Optional[str] = None
    download_url: Optional[str] = None
    status: str = "pending"

    def mark_searching(self) -> None:
        """将状态标记为 'searching'。"""
        self.status = "searching"

    def mark_found(self, subtitle_url: str) -> None:
        """将状态标记为 'found' 并记录字幕 URL。

        Args:
            subtitle_url: 匹配到的字幕页面 URL。
        """
        self.status = "found"
        self.subtitle_url = subtitle_url

    def mark_downloading(self, download_url: str) -> None:
        """将状态标记为 'downloading' 并记录下载链接。

        Args:
            download_url: 字幕直接下载链接。
        """
        self.status = "downloading"
        self.download_url = download_url

    def mark_completed(self) -> None:
        """将状态标记为 'completed'。"""
        self.status = "completed"

    def mark_failed(self) -> None:
        """将状态标记为 'failed'。"""
        self.status = "failed"

    @property
    def is_completed(self) -> bool:
        """返回电影是否已成功下载字幕。"""
        return self.status == "completed"

    @property
    def is_failed(self) -> bool:
        """返回电影是否下载失败。"""
        return self.status == "failed"
