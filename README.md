# Subtitle Downloader

> 批量从字幕网站下载电影中文字幕的 Python 工具。

## 功能

- 🔍 自动搜索指定电影的中文字幕（zh-CN）
- 📥 批量下载，支持多部电影
- 🧩 Provider 架构，轻松扩展支持新的字幕网站
- 📝 完整的日志记录，成功/失败自动归档
- 🖥️ Playwright 驱动，兼容动态渲染页面

## 环境要求

- Python 3.13+
- 支持 macOS / Linux / Windows

## 安装

### 1. 克隆项目

```bash
git clone <your-repo-url>
cd subtitle-downloader
```

### 2. 创建虚拟环境

```bash
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 安装 Playwright 浏览器

```bash
playwright install chromium
```

## 运行

### 准备电影列表

编辑 `movies.txt`，每行写入一部电影名称：

```
# 每行一部电影名称
Inception
The Matrix
Interstellar
The Dark Knight (2008)
```

### 启动下载

```bash
python -m src.main
```

或

```bash
cd src
python main.py
```

### 输出

- 成功下载的字幕文件保存在 `output/` 目录
- 运行日志保存在 `logs/app.log`
- 成功的电影记录在 `success.txt`
- 失败的电影记录在 `failed.txt`

## 项目目录

```
subtitle-downloader/
├── README.md                  # 项目说明文档
├── requirements.txt           # Python 依赖清单
├── .gitignore                 # Git 忽略规则
├── movies.txt                 # 待下载电影列表（输入）
├── failed.txt                 # 下载失败的记录（输出）
├── success.txt                # 下载成功的记录（输出）
├── logs/                      # 日志文件目录
│   └── app.log
├── output/                    # 字幕文件输出目录
└── src/
    ├── main.py                # 程序入口
    ├── config.py              # 全局配置
    ├── browser.py             # Playwright 浏览器封装
    ├── downloader.py          # 字幕文件下载器
    ├── service.py             # 核心调度服务
    ├── logger.py              # 日志配置
    ├── providers/
    │   ├── __init__.py
    │   ├── base.py            # Provider 抽象基类
    │   └── subtitlecat.py     # SubtitleCat Provider 实现
    ├── models/
    │   ├── __init__.py
    │   └── movie.py           # Movie 数据模型
    └── utils/
        ├── __init__.py
        ├── matcher.py         # 模糊匹配工具
        └── parser.py          # 标题解析工具
```

## Provider 架构

本项目采用 Provider 设计模式，方便扩展支持多个字幕网站。

### 添加新的 Provider

1. 在 `src/providers/` 下创建新文件（如 `opensubtitles.py`）
2. 继承 `BaseProvider` 并实现 `search()` 和 `get_download_url()` 方法
3. 在 `src/providers/__init__.py` 中导出新 Provider

```python
# src/providers/opensubtitles.py
from src.providers.base import BaseProvider

class OpenSubtitlesProvider(BaseProvider):
    def search(self, movie_title, year=None):
        # 实现搜索逻辑
        pass

    def get_download_url(self, subtitle_url):
        # 实现下载链接提取
        pass
```

## 开发说明

### 代码规范

- **类型注解**：所有函数和类方法均使用完整的 Type Hints
- **日志记录**：使用 `logging` 模块，日志同时输出到控制台和文件
- **PEP8**：严格遵循 PEP8 代码风格
- **Docstring**：所有公开接口均包含完整的 Google 风格文档字符串

### 配置说明

所有配置集中在 `src/config.py` 的 `Config` 类中：

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `TARGET_LANGUAGE` | `zh-CN` | 目标字幕语言 |
| `HEADLESS` | `True` | 浏览器无头模式 |
| `BROWSER_TIMEOUT` | `30000` | 浏览器操作超时（毫秒） |
| `REQUEST_TIMEOUT` | `30` | HTTP 请求超时（秒） |
| `LOG_LEVEL` | `INFO` | 日志级别 |

### 当前状态

项目处于架构搭建阶段，SubtitleCat 的具体搜索和下载逻辑尚未实现（标记为 TODO）。

## 许可证

MIT License
