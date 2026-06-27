"""名称匹配与评分工具模块。

提供电影名称的模糊匹配、搜索结果评分和最佳选择功能，
用于在字幕网站搜索结果中找到与输入电影名称最匹配的条目。
"""

import logging
import re
from difflib import SequenceMatcher
from typing import Optional

logger = logging.getLogger(__name__)


def fuzzy_match(
    query: str,
    candidate: str,
    threshold: float = 0.6,
) -> bool:
    """使用模糊匹配算法比较两个字符串的相似度。

    综合使用 SequenceMatcher 和文本归一化来提升匹配精度。
    在比较前会：
        - 转为小写
        - 去除标点符号和多余空格
        - 移除常见冠词（a, an, the）

    Args:
        query: 搜索关键词（原始电影名称）。
        candidate: 候选字符串（网站返回的标题）。
        threshold: 相似度阈值，范围 [0, 1]，默认 0.6。

    Returns:
        如果相似度 >= 阈值，则返回 True，否则返回 False。

    Example:
        >>> fuzzy_match("The Matrix", "Matrix (1999)")
        True
        >>> fuzzy_match("Inception", "Interstellar")
        False
    """
    def normalize(text: str) -> str:
        """归一化文本——小写、去标点、去冠词、去多余空格。"""
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\b(a|an|the)\b', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    query_norm = normalize(query)
    candidate_norm = normalize(candidate)

    if not query_norm or not candidate_norm:
        logger.debug("模糊匹配：空字符串，返回 False")
        return False

    similarity = SequenceMatcher(None, query_norm, candidate_norm).ratio()
    logger.debug(
        "模糊匹配: query=%s, candidate=%s, similarity=%.3f, threshold=%.3f",
        query_norm, candidate_norm, similarity, threshold,
    )
    return similarity >= threshold


def score_movie(
    query_title: str,
    query_year: Optional[int],
    candidate_title: str,
) -> int:
    """对搜索结果中的候选字幕进行评分。

    基于一套启发式规则对候选标题打分。分数越高表示匹配度越高，
    负分则表示不应匹配（如电视剧、纪录片等）。

    评分规则：
        - 电影名称完全包含在候选标题中 ........... +100
        - 年份一致 .................................... +30
        - 包含 "BluRay" 或 "Blu-Ray" ................. +10
        - 包含 "WEB-DL" ................................ +8
        - 包含 "1080p" .................................. +5
        - 包含 "2160p" .................................. +5
        - 包含 "x264" ................................... +3
        - 匹配到 S01E01 等剧集编号 ................... -1000
        - 包含 "Season" ................................ -500
        - 包含 "Episode" ............................... -500
        - 包含 "Airbender" (Avatar) .................. -500
        - 包含独立单词 "TV" ........................... -300
        - 包含 "Documentary" .......................... -300

    Args:
        query_title: 用户输入的电影名称。
        query_year: 用户输入的电影年份（可选）。
        candidate_title: 网站返回的候选字幕标题。

    Returns:
        整型评分，越高表示匹配越好。

    Example:
        >>> score_movie("Titanic", 1997, "Titanic 1997 BluRay 1080p x264")
        148
        >>> score_movie("Titanic", 1997, "Titanic.S01E01.Pilot")
        -1000
    """
    score: int = 0
    q_lower = query_title.lower()
    c_lower = candidate_title.lower()

    # --- 正分规则 ---

    # 电影名称完全包含在候选标题中
    if q_lower in c_lower:
        score += 100
        logger.debug("评分 +100: 名称完全包含 (%s)", query_title)

    # 年份一致
    if query_year is not None:
        years_in_candidate = re.findall(r'\b(\d{4})\b', candidate_title)
        for y_str in years_in_candidate:
            if int(y_str) == query_year:
                score += 30
                logger.debug("评分 +30: 年份匹配 (%d)", query_year)
                break

    # BluRay / Blu-Ray
    if re.search(r'blu-?ray', c_lower):
        score += 10
        logger.debug("评分 +10: BluRay")

    # WEB-DL
    if 'web-dl' in c_lower:
        score += 8
        logger.debug("评分 +8: WEB-DL")

    # 1080p
    if '1080p' in c_lower:
        score += 5
        logger.debug("评分 +5: 1080p")

    # 2160p
    if '2160p' in c_lower:
        score += 5
        logger.debug("评分 +5: 2160p")

    # x264
    if 'x264' in c_lower:
        score += 3
        logger.debug("评分 +3: x264")

    # --- 负分规则 ---

    # S01E01 等剧集编号模式
    if re.search(r's\d{1,2}\s*e\d{1,2}', c_lower):
        score -= 1000
        logger.debug("评分 -1000: 检测到剧集编号 SxxExx")

    # Season
    if 'season' in c_lower:
        score -= 500
        logger.debug("评分 -500: Season")

    # Episode
    if 'episode' in c_lower:
        score -= 500
        logger.debug("评分 -500: Episode")

    # Avatar: The Last Airbender
    if 'airbender' in c_lower:
        score -= 500
        logger.debug("评分 -500: Airbender")

    # TV（独立单词）
    if re.search(r'\btv\b', c_lower):
        score -= 300
        logger.debug("评分 -300: TV")

    # Documentary
    if 'documentary' in c_lower:
        score -= 300
        logger.debug("评分 -300: Documentary")

    logger.debug("总评分: %d (query=%s, candidate=%s)", score, query_title, candidate_title)
    return score


def choose_best(
    results: list[dict],
    query_title: str,
    query_year: Optional[int] = None,
) -> Optional[dict]:
    """从搜索结果列表中选出评分最高的一项。

    对每条结果调用 score_movie() 计算评分，将评分写入
    result["score"]，并返回评分最高的那条。

    Args:
        results: 搜索结果字典列表（来自 parse_search_results）。
        query_title: 用户搜索的电影名称。
        query_year: 用户搜索的电影年份（可选）。

    Returns:
        评分最高的结果字典。如果列表为空，返回 None。

    Example:
        >>> results = [{"title": "Titanic 1997", "href": "...", "score": 0}]
        >>> choose_best(results, "Titanic", 1997)
        {"title": "Titanic 1997", "href": "...", "score": 148}
    """
    if not results:
        logger.debug("choose_best: 结果列表为空，返回 None")
        return None

    best: Optional[dict] = None
    best_score: int = -999999

    for result in results:
        candidate_score = score_movie(
            query_title=query_title,
            query_year=query_year,
            candidate_title=result["title"],
        )
        result["score"] = candidate_score

        if candidate_score > best_score:
            best_score = candidate_score
            best = result

    logger.debug("choose_best: 最佳匹配 score=%d, title=%s",
                 best_score, best["title"] if best else "N/A")
    return best
