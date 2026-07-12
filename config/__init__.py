# config/__init__.py
# =================
# 统一配置模块。

from .settings import (
    COLLECT_SCHEDULE_TIME,
    SCHEDULER_TIMEZONE,
    SITES_CONFIG_PATH,
    RUN_RECORDS_DIR,
    LOG_DIR,
    DEFAULT_UPLOAD_URL,
    DEFAULT_UPLOAD_LIMIT,
)

__all__ = [
    "COLLECT_SCHEDULE_TIME",
    "SCHEDULER_TIMEZONE",
    "SITES_CONFIG_PATH",
    "RUN_RECORDS_DIR",
    "LOG_DIR",
    "DEFAULT_UPLOAD_URL",
    "DEFAULT_UPLOAD_LIMIT",
]
