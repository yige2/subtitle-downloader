"""日志配置模块。

提供统一的日志记录器配置，支持控制台输出和文件输出。
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Optional

from src.config import Config


def setup_logger(
    name: str = "subtitle_downloader",
    log_file: Optional[str] = None,
) -> logging.Logger:
    """配置并返回一个日志记录器。

    该记录器同时输出到控制台和文件。文件输出使用轮转策略，
    防止日志文件无限增大。

    Args:
        name: 日志记录器的名称。
        log_file: 日志文件的绝对路径。如果未提供，默认使用应用日志路径。

    Returns:
        一枚配置完毕的 logging.Logger 实例。

    Example:
        >>> logger = setup_logger(__name__)
        >>> logger.info("应用启动")
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, Config.LOG_LEVEL.upper(), logging.INFO))

    # 避免重复添加处理器
    if logger.handlers:
        return logger

    # 格式化器
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 文件处理器
    if log_file is None:
        log_file = os.path.join(Config.LOGS_DIR, "app.log")
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
