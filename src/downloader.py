"""字幕下载器模块。

负责执行字幕文件的实际下载操作，将文件保存到本地输出目录。
使用 requests（非 Playwright）下载文件。
"""

import logging
import os
from typing import Optional

import requests

from src.config import Config

logger = logging.getLogger(__name__)


class SubtitleDownloader:
    """字幕文件下载器。

    负责从 URL 下载字幕文件并保存到本地目录。

    如果目标文件已存在，自动跳过下载。

    Attributes:
        output_dir: 字幕文件输出目录。
        session: requests.Session 实例，复用连接。
    """

    def __init__(self, output_dir: Optional[str] = None) -> None:
        """初始化下载器。

        Args:
            output_dir: 输出目录路径，默认使用 Config.OUTPUT_DIR。
        """
        self.output_dir: str = output_dir or Config.OUTPUT_DIR
        self.session: requests.Session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        })
        os.makedirs(self.output_dir, exist_ok=True)
        logger.info("下载器初始化完成，输出目录: %s", self.output_dir)

    def download(
        self,
        url: str,
        filename: str,
    ) -> Optional[str]:
        """从指定 URL 下载字幕文件。

        如果文件已存在，直接跳过并返回现有文件路径。
        下载失败时不抛异常，返回 None。

        Args:
            url: 字幕文件的直接下载链接。
            filename: 保存到本地的文件名（如 "Titanic.srt"）。

        Returns:
            下载成功或文件已存在时返回绝对路径，失败返回 None。
        """
        filepath = os.path.join(self.output_dir, filename)

        # 文件已存在，跳过下载
        if os.path.exists(filepath):
            logger.info("文件已存在，跳过: %s", filepath)
            return filepath

        logger.info("开始下载: %s -> %s", url, filepath)

        try:
            response = self.session.get(
                url,
                timeout=Config.REQUEST_TIMEOUT,
                stream=True,
            )
            response.raise_for_status()

            with open(filepath, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            file_size = os.path.getsize(filepath)
            logger.info("下载完成: %s (%d bytes)", filepath, file_size)
            return filepath

        except Exception:
            logger.warning("下载失败: %s", url, exc_info=True)
            # 清理不完整的文件
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except OSError:
                    pass
            return None

    def close(self) -> None:
        """关闭下载器，释放 HTTP 会话资源。"""
        self.session.close()
        logger.debug("下载器会话已关闭。")

