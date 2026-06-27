"""应用配置模块。

集中管理所有配置项，包括路径、超时时间、目标语言等。
"""

import os
from typing import ClassVar
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    """应用程序的全局配置。

    使用 frozen=True 确保配置在初始化后不可变。

    Attributes:
        BASE_DIR: 项目根目录的绝对路径。
        MOVIES_FILE: 输入电影列表文件路径。
        SUCCESS_FILE: 下载成功记录文件路径。
        FAILED_FILE: 下载失败记录文件路径。
        OUTPUT_DIR: 字幕输出目录。
        LOGS_DIR: 日志文件输出目录。
        LOG_LEVEL: 日志记录级别。
        TARGET_LANGUAGE: 下载字幕的目标语言代码。
        BROWSER_TIMEOUT: Playwright 浏览器操作的超时时间（毫秒）。
        REQUEST_TIMEOUT: HTTP 请求超时时间（秒）。
        HEADLESS: 是否以无头模式运行浏览器。
    """

    BASE_DIR: ClassVar[str] = os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )
    MOVIES_FILE: ClassVar[str] = os.path.join(BASE_DIR, "movies.txt")
    SUCCESS_FILE: ClassVar[str] = os.path.join(BASE_DIR, "success.txt")
    FAILED_FILE: ClassVar[str] = os.path.join(BASE_DIR, "failed.txt")
    OUTPUT_DIR: ClassVar[str] = os.path.join(BASE_DIR, "output")
    LOGS_DIR: ClassVar[str] = os.path.join(BASE_DIR, "logs")
    LOG_LEVEL: ClassVar[str] = "INFO"
    TARGET_LANGUAGE: ClassVar[str] = "zh-CN"
    BROWSER_TIMEOUT: ClassVar[int] = 30_000
    REQUEST_TIMEOUT: ClassVar[int] = 30
    HEADLESS: ClassVar[bool] = False

    @classmethod
    def ensure_directories(cls) -> None:
        """确保所有必要的目录存在。"""
        for dir_path in (cls.OUTPUT_DIR, cls.LOGS_DIR):
            os.makedirs(dir_path, exist_ok=True)

