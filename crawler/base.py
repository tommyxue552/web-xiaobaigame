# crawler/base.py
# ===============
# 采集器基类，提供请求网页、获取HTML、日志记录、异常处理等基础能力。
# 设计上预留了 Playwright 引擎的扩展点。

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

import requests
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# 日志配置
# ---------------------------------------------------------------------------

logger = logging.getLogger("crawler")

# ---------------------------------------------------------------------------
# 数据结构
# ---------------------------------------------------------------------------


@dataclass
class CrawlResult:
    """单次采集的结果封装。"""

    url: str
    status_code: int
    html: str = ""
    soup: Optional[BeautifulSoup] = None
    elapsed: float = 0.0
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.error is None and 200 <= self.status_code < 400


# ---------------------------------------------------------------------------
# 引擎抽象  ——  方便后续切换 requests / Playwright
# ---------------------------------------------------------------------------


class FetchEngine(ABC):
    """网页抓取引擎的抽象接口。

    当前实现：RequestsEngine
    未来实现：PlaywrightEngine（继承此类并实现 fetch 方法）
    """

    @abstractmethod
    def fetch(self, url: str, headers: Optional[Dict[str, str]] = None,
              timeout: int = 30) -> CrawlResult:
        ...


class RequestsEngine(FetchEngine):
    """基于 requests 库的同步抓取引擎。"""

    def fetch(self, url: str, headers: Optional[Dict[str, str]] = None,
              timeout: int = 30) -> CrawlResult:
        result = CrawlResult(url=url, status_code=0)

        if headers is None:
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/125.0.0.0 Safari/537.36"
                ),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            }

        start = time.perf_counter()
        try:
            resp = requests.get(url, headers=headers, timeout=timeout)
            resp.encoding = resp.apparent_encoding
            result.status_code = resp.status_code
            result.html = resp.text
            result.soup = BeautifulSoup(result.html, "html.parser")
        except requests.Timeout:
            result.error = f"请求超时（{timeout}s）：{url}"
        except requests.ConnectionError:
            result.error = f"连接失败：{url}"
        except requests.RequestException as exc:
            result.error = f"请求异常：{exc}"
        except Exception as exc:
            result.error = f"未知错误：{exc}"
        finally:
            result.elapsed = time.perf_counter() - start

        return result


# ---------------------------------------------------------------------------
# Crawler 基类
# ---------------------------------------------------------------------------


class Crawler(ABC):
    """采集器基类。

    子类需要实现：
        - parse(html: str) -> Any     解析逻辑
        - source_name: str           采集源名称（类属性）

    可选覆盖：
        - start_urls: List[str]      起始 URL 列表
        - process(item) -> None      单条结果持久化钩子
    """

    # --- 子类必须定义 ---

    source_name: str = ""

    # --- 子类可选覆盖 ---

    start_urls: list[str] = []
    request_delay: float = 1.0          # 请求间隔（秒）
    request_timeout: int = 30           # 单次请求超时（秒）

    # --- 引擎 ---

    engine: FetchEngine

    def __init__(self, engine: Optional[FetchEngine] = None,
                 extra_headers: Optional[Dict[str, str]] = None):
        self.engine = engine or RequestsEngine()
        self.extra_headers = extra_headers or {}

    # ------------------------------------------------------------------
    # 公开 API
    # ------------------------------------------------------------------

    def run(self, urls: Optional[list[str]] = None) -> list[CrawlResult]:
        """执行采集主流程。

        遍历 urls（或 self.start_urls），逐页抓取并调用 parse。
        """
        urls = urls or self.start_urls
        results: list[CrawlResult] = []

        logger.info("[%s] 开始采集，共 %d 个 URL", self.source_name, len(urls))

        for i, url in enumerate(urls, 1):
            logger.info("[%s] (%d/%d) 抓取 %s", self.source_name, i, len(urls), url)

            result = self.fetch(url)

            if result.success:
                logger.info("[%s] 成功 %d，耗时 %.2fs",
                            self.source_name, result.status_code, result.elapsed)
                try:
                    parsed = self.parse(result.html)
                    self.process(parsed)
                except Exception as exc:
                    logger.error("[%s] 解析异常：%s", self.source_name, exc)
                    result.error = f"解析异常：{exc}"
            else:
                logger.warning("[%s] 失败：%s", self.source_name, result.error)

            results.append(result)

            if i < len(urls):
                time.sleep(self.request_delay)

        ok = sum(1 for r in results if r.success)
        logger.info("[%s] 采集完成：%d/%d 成功", self.source_name, ok, len(results))
        return results

    def fetch(self, url: str) -> CrawlResult:
        """抓取单个 URL，自动合并额外请求头。"""
        return self.engine.fetch(
            url,
            headers=self.extra_headers or None,
            timeout=self.request_timeout,
        )

    # ------------------------------------------------------------------
    # 子类必须实现的钩子
    # ------------------------------------------------------------------

    @abstractmethod
    def parse(self, html: str) -> Any:
        """解析 HTML，返回结构化数据。"""
        ...

    # ------------------------------------------------------------------
    # 子类可选覆盖的钩子
    # ------------------------------------------------------------------

    def process(self, item: Any) -> None:
        """处理单条解析结果（默认仅打印日志）。"""
        if item is not None:
            logger.debug("[%s] 解析结果：%s", self.source_name, item)


# ---------------------------------------------------------------------------
# Playwright 引擎占位（后续实现）
# ---------------------------------------------------------------------------


class PlaywrightEngine(FetchEngine):
    """基于 Playwright 的抓取引擎（预留）。

    使用方式：
        engine = PlaywrightEngine(headless=True)
        crawler = MyCrawler(engine=engine)
        crawler.run()
    """

    def __init__(self, headless: bool = True):
        self.headless = headless
        self._browser = None
        self._context = None

    def fetch(self, url: str, headers: Optional[Dict[str, str]] = None,
              timeout: int = 30) -> CrawlResult:
        raise NotImplementedError("Playwright 引擎尚未实现，请先安装 playwright 并完成集成")
