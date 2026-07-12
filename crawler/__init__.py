# crawler/__init__.py
# ===================
# 独立采集服务包。

from .base import Crawler, CrawlResult, FetchEngine, RequestsEngine, PlaywrightEngine

__all__ = [
    "Crawler",
    "CrawlResult",
    "FetchEngine",
    "RequestsEngine",
    "PlaywrightEngine",
]
