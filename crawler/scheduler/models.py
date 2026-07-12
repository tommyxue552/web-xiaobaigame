# crawler/scheduler/models.py
# ===========================
# 调度运行记录的数据模型。

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class RunRecord:
    """单次调度执行记录。

    每次定时任务触发时生成一条记录，涵盖采集 → 上传的全链路结果。
    """

    site: str                          # 采集源标识
    start_time: datetime               # 任务开始时间
    end_time: datetime | None = None   # 任务结束时间
    crawled_count: int = 0             # 采集成功页数
    parsed_count: int = 0              # 解析出的条目数
    uploaded_count: int = 0            # 上传成功数
    failed_count: int = 0              # 上传失败数
    duplicated_count: int = 0          # 重复跳过数
    status: str = "running"            # running | success | failed
    error_message: str = ""            # 异常信息（如有）

    @property
    def total_failures(self) -> int:
        return self.failed_count

    @property
    def total_success(self) -> int:
        return self.uploaded_count

    @property
    def duration_seconds(self) -> float | None:
        if self.end_time is None:
            return None
        return (self.end_time - self.start_time).total_seconds()

    def to_dict(self) -> dict[str, Any]:
        return {
            "site": self.site,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "crawled_count": self.crawled_count,
            "parsed_count": self.parsed_count,
            "uploaded_count": self.uploaded_count,
            "failed_count": self.failed_count,
            "duplicated_count": self.duplicated_count,
            "status": self.status,
            "error_message": self.error_message,
            "duration_seconds": self.duration_seconds,
        }
