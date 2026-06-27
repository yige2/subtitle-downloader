"""解析工具模块。

提供电影标题解析、搜索页面 HTML 解析和字幕下载链接提取功能。
"""

import logging
import re
from typing import Optional
from typing import Tuple

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def parse_movie_title(line: str) -> Tuple[str, Optional[int]]:
    """从一行文本中解析电影名称和可选年份。

    支持以下格式：
        - "Inception"
        - "The Matrix (1999)"
        - "Titanic 1997"
        - "  Inception  "  → 自动去除空白

    Args:
        line: 来自 movies.txt 的一行原始文本。

    Returns:
        一个 (title, year) 元组，year 可能为 None。

    Example:
        >>> parse_movie_title("The Matrix (1999)")
        ("The Matrix", 1999)
        >>> parse_movie_title("Inception")
        ("Inception", None)
    """
    line = line.strip()

    if not line or line.startswith("#"):
        return ("", None)

    # 尝试匹配 "(Year)" 模式
    year_match = re.search(r'\((\d{4})\)$', line)
    if year_match:
        title = line[:year_match.start()].strip()
        year = int(year_match.group(1))
        logger.debug("解析电影: title=%s, year=%d", title, year)
        return (title, year)

    # 尝试匹配末尾四位数字
    year_match = re.search(r'\b(\d{4})\b\s*$', line)
    if year_match:
        title = line[:year_match.start()].strip()
        year = int(year_match.group(1))
        logger.debug("解析电影: title=%s, year=%d", title, year)
        return (title, year)

    logger.debug("解析电影: title=%s, year=None", line)
    return (line, None)


def parse_search_results(html: str) -> list[dict]:
    """从 SubtitleCat 搜索结果页面的 HTML 中解析字幕列表。

    找到所有 <table><tbody><tr> 行中的 <a> 标签，
    提取标题和 href 属性。

    Args:
        html: 搜索结果页面的完整 HTML 字符串。

    Returns:
        包含字幕资源的字典列表，每个字典包含：
            - title: 字幕标题（<a> 标签的可见文本）
            - href: 字幕详情页的相对路径
            - score: 初始评分（始终为 0，后续由 matcher 赋值）

    解析失败时返回空列表（不抛异常）。
    """
    results: list[dict] = []
    try:
        soup = BeautifulSoup(html, "lxml")
        rows = soup.select("table tbody tr")
        logger.debug("找到 %d 行搜索结果", len(rows))

        for row in rows:
            a_tag = row.find("a")
            if a_tag is None:
                continue
            title = a_tag.get_text(strip=True)
            href = a_tag.get("href", "")
            if title and href:
                results.append({
                    "title": title,
                    "href": href,
                    "score": 0,
                })
    except Exception:
        logger.warning("解析搜索结果 HTML 时发生异常", exc_info=True)
        return []

    logger.debug("解析得到 %d 条字幕结果", len(results))
    return results


def parse_download_url(
    html: str,
    language: str = "zh-CN",
) -> Optional[str]:
    """从字幕详情页 HTML 中提取指定语言的下载链接。

    查找 id="download_{language}" 的 <a> 标签，
    提取其 href 属性。

    Args:
        html: 字幕详情页面的完整 HTML 字符串。
        language: 目标语言代码，默认为 "zh-CN"。

    Returns:
        字幕下载链接的相对路径（如 "/subs/460/xxx-zh-CN.srt"）。
        未找到时返回 None。

    解析失败时返回 None（不抛异常）。
    """
    try:
        soup = BeautifulSoup(html, "lxml")
        download_id = f"download_{language}"
        a_tag = soup.find("a", id=download_id)
        if a_tag is None:
            logger.debug("未找到下载链接: id=%s", download_id)
            return None
        href = a_tag.get("href", "")
        if href:
            logger.debug("找到下载链接: %s", href)
            return href
        return None
    except Exception:
        logger.warning("解析字幕详情页 HTML 时发生异常", exc_info=True)
        return None
