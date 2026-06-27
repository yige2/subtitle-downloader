"""字幕下载服务模块。

SubtitleService 是项目的核心调度器，负责：
    - 读取 movies.txt 中的电影列表
    - 调用 Provider 搜索字幕
    - 调用 matcher 选择最佳匹配
    - 下载匹配的字幕文件
    - 记录成功/失败日志
    - 输出统计信息和进度条

不包含任何 Playwright 代码，仅通过抽象接口操作。
"""

import logging
import sys
import time

from src.config import Config
from src.downloader import SubtitleDownloader
from src.providers.base import BaseProvider
from src.utils.matcher import choose_best
from src.utils.parser import parse_movie_title

logger = logging.getLogger(__name__)

# 进度条宽度（字符数）
_BAR_WIDTH = 30


def _render_progress(
    current: int,
    total: int,
    title: str,
    success: int,
    failed: int,
) -> str:
    """渲染进度条字符串。

    Args:
        current: 当前处理序号 (1-based)。
        total: 总电影数。
        title: 当前电影名称。
        success: 已成功数量。
        failed: 已失败数量。

    Returns:
        格式化的进度条字符串（含 \\r 前缀用于原地刷新）。
    """
    pct = current / total if total > 0 else 0
    filled = int(_BAR_WIDTH * pct)
    bar = "█" * filled + "░" * (_BAR_WIDTH - filled)
    return (
        f"\r  [{bar}] {current}/{total} ({pct:.0%})"
        f"  ✓{success} ✗{failed}"
        f"  {title[:20]:<20}"
    )


class SubtitleService:
    """字幕下载核心服务类。

    协调 Provider、Matcher 和 Downloader 完成批量字幕下载任务。

    Attributes:
        provider: 字幕网站 Provider 实例。
        downloader: 字幕文件下载器实例。
    """

    def __init__(
        self,
        provider: BaseProvider,
        downloader: SubtitleDownloader,
    ) -> None:
        """初始化字幕服务。

        Args:
            provider: 已初始化的字幕网站 Provider 实例。
            downloader: 字幕文件下载器实例。
        """
        self._provider: BaseProvider = provider
        self._downloader: SubtitleDownloader = downloader
        logger.info("SubtitleService 初始化完成，Provider: %s", self._provider.name)

    @property
    def provider(self) -> BaseProvider:
        """返回当前的 Provider 实例。"""
        return self._provider

    # ------------------------------------------------------------------
    # 文件 I/O
    # ------------------------------------------------------------------

    def read_movies(self) -> list[str]:
        """从 movies.txt 读取电影名称行列表。

        跳过以 '#' 开头的注释行和空行。

        Returns:
            有效的原始行列表（每行可能包含年份信息）。
        """
        logger.info("正在读取电影列表: %s", Config.MOVIES_FILE)
        movies: list[str] = []

        try:
            with open(Config.MOVIES_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        movies.append(line)
        except FileNotFoundError:
            logger.error("电影列表文件不存在: %s", Config.MOVIES_FILE)
            raise
        except IOError:
            logger.exception("读取电影列表文件失败")
            raise

        logger.info("读取到 %d 部电影", len(movies))
        return movies

    def record_success(self, movie_title: str) -> None:
        """累加一条成功记录到 success.txt。

        Args:
            movie_title: 电影名称。
        """
        try:
            with open(Config.SUCCESS_FILE, "a", encoding="utf-8") as f:
                f.write(f"{movie_title}\n")
        except IOError:
            logger.exception("写入成功记录文件失败")

    def record_failed(self, movie_title: str) -> None:
        """累加一条失败记录到 failed.txt。

        Args:
            movie_title: 电影名称。
        """
        try:
            with open(Config.FAILED_FILE, "a", encoding="utf-8") as f:
                f.write(f"{movie_title}\n")
        except IOError:
            logger.exception("写入失败记录文件失败")

    # ------------------------------------------------------------------
    # 主循环
    # ------------------------------------------------------------------

    def run(self) -> None:
        """运行字幕下载服务的主循环。

        流程：
            1. 读取 movies.txt
            2. 逐部电影：解析标题 → 搜索 → 匹配最佳 → 获取下载链接 → 下载
            3. 单部失败不中断整体流程
            4. 最后输出统计（Movies / Success / Failed / Elapsed）
        """
        start_time = time.time()

        try:
            raw_movies = self.read_movies()
        except (FileNotFoundError, IOError):
            logger.error("无法读取电影列表，服务终止。")
            return

        if not raw_movies:
            logger.warning("电影列表为空，没有需要处理的任务。")
            return

        total = len(raw_movies)
        success_count: int = 0
        failed_count: int = 0
        index: int = 0

        for line in raw_movies:
            title, year = parse_movie_title(line)
            if not title:
                continue

            index += 1
            sys.stderr.write(
                _render_progress(index, total, title, success_count, failed_count)
            )
            sys.stderr.flush()

            logger.info("=" * 36)
            logger.info("Searching : %s", title)

            # ---- 搜索 ----
            try:
                results = self._provider.search(title, year)
            except Exception:
                logger.warning("搜索异常，跳过: %s", title)
                self.record_failed(title)
                failed_count += 1
                continue

            logger.info("Found : %d", len(results))

            if not results:
                logger.info("Best Match :")
                logger.info("(none)")
                self.record_failed(title)
                failed_count += 1
                continue

            # ---- 匹配 ----
            best = choose_best(results, title, year)
            logger.info("Best Match :")
            if not best:
                logger.info("(none)")
                self.record_failed(title)
                failed_count += 1
                continue

            logger.info(best["title"])

            # ---- 获取下载链接 ----
            logger.info("Subtitle :")
            try:
                download_url = self._provider.get_download_url(best["href"])
            except Exception:
                logger.warning("获取下载链接异常")
                self.record_failed(title)
                failed_count += 1
                continue

            if not download_url:
                logger.info("No Chinese Subtitle")
                self.record_failed(title)
                failed_count += 1
                continue

            logger.info("Found %s", Config.TARGET_LANGUAGE)

            # ---- 下载 ----
            logger.info("Downloading...")
            filename = f"{title}.srt"
            filepath = self._downloader.download(download_url, filename)

            if filepath:
                logger.info("Completed")
                self.record_success(title)
                success_count += 1
            else:
                logger.info("Failed")
                self.record_failed(title)
                failed_count += 1

        # 进度条结束，换行
        sys.stderr.write("\n")
        sys.stderr.flush()

        # ---- 统计 ----
        elapsed = time.time() - start_time
        logger.info("=" * 36)
        logger.info("Statistics")
        logger.info("Movies : %d", len(raw_movies))
        logger.info("Success : %d", success_count)
        logger.info("Failed : %d", failed_count)
        logger.info("Elapsed : %.1f s", elapsed)
