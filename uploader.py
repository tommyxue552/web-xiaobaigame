# -*- coding: utf-8 -*-
"""
uploader.py —— 采集数据上传模块
=============================
将采集器产出的游戏数据批量 POST 到 web-xiaobaigame 的 /api/crawler/import 接口。

用法：
    from uploader import Uploader

    uploader = Uploader(base_url="http://localhost:8000")
    stats = uploader.upload(games, source="gameshare")
    print(stats)
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import requests

logger = logging.getLogger("uploader")


# ---------------------------------------------------------------------------
# 数据结构
# ---------------------------------------------------------------------------


@dataclass
class UploadStats:
    """上传结果统计。"""

    crawled: int = 0          # 采集数量（传入总数）
    parsed: int = 0           # 解析成功数量（传入的有效条目）
    uploaded: int = 0         # 上传成功数量
    failed: int = 0           # 上传失败数量
    duplicated: int = 0       # 重复数量（服务端返回的 skipped）
    errors: list[dict[str, Any]] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        if self.parsed == 0:
            return 0.0
        return self.uploaded / self.parsed


# ---------------------------------------------------------------------------
# Uploader
# ---------------------------------------------------------------------------


class Uploader:
    """采集数据上传器。

    将游戏条目列表打包，逐批（或整体）POST 到 /api/crawler/import。
    """

    # 默认配置
    DEFAULT_BASE_URL: str = "http://localhost:8000"
    DEFAULT_COLLECTOR_KEY: str = "xiaobai-collector-default-key-change-in-production"
    DEFAULT_BATCH_SIZE: int = 10

    def __init__(
        self,
        base_url: Optional[str] = None,
        collector_key: Optional[str] = None,
        batch_size: int = DEFAULT_BATCH_SIZE,
    ):
        self.base_url = (base_url or self.DEFAULT_BASE_URL).rstrip("/")
        self.collector_key = collector_key or os.environ.get(
            "XIAOBAI_COLLECTOR_KEY", self.DEFAULT_COLLECTOR_KEY
        )
        self.batch_size = batch_size
        self._import_url = f"{self.base_url}/api/crawler/import"

    # ------------------------------------------------------------------
    # 公开 API
    # ------------------------------------------------------------------

    def upload(
        self,
        games: list[dict[str, str]],
        source: str = "gameshare",
        crawled_count: Optional[int] = None,
    ) -> UploadStats:
        """上传游戏数据到站点 API。

        Args:
            games: 游戏条目列表（dict 需包含 title 等字段）。
            source: 来源标识。
            crawled_count: 原始采集数量（用于统计，默认为 len(games)）。

        Returns:
            UploadStats 统计结果。
        """
        stats = UploadStats(
            crawled=crawled_count if crawled_count is not None else len(games),
            parsed=len(games),
        )

        if not games:
            logger.warning("没有可上传的游戏数据")
            return stats

        # 分批上传
        batches = self._batch(games)

        for i, batch in enumerate(batches, 1):
            logger.info("上传第 %d/%d 批，共 %d 条", i, len(batches), len(batch))
            result = self._post_batch(batch, source, stats)
            if result is not None:
                stats.uploaded += result.get("imported", 0)
                stats.duplicated += result.get("skipped", 0)

        logger.info(
            "上传完成：采集 %d → 解析 %d → 成功 %d / 失败 %d / 重复 %d",
            stats.crawled, stats.parsed, stats.uploaded, stats.failed, stats.duplicated,
        )

        return stats

    # ------------------------------------------------------------------
    # 内部方法
    # ------------------------------------------------------------------

    def _batch(self, games: list[dict[str, str]]) -> list[list[dict[str, str]]]:
        """将游戏列表按 batch_size 分片。"""
        return [
            games[i:i + self.batch_size]
            for i in range(0, len(games), self.batch_size)
        ]

    def _post_batch(
        self,
        batch: list[dict[str, str]],
        source: str,
        stats: UploadStats,
    ) -> Optional[dict]:
        """POST 一批游戏数据到 API，返回响应 JSON 或 None（失败时）。"""
        payload = self._build_payload(batch, source)

        try:
            resp = requests.post(
                self._import_url,
                headers={
                    "Content-Type": "application/json",
                    "Collector-Key": self.collector_key,
                },
                json=payload,
                timeout=30,
            )

            if resp.status_code == 200:
                data = resp.json()
                logger.info(
                    "  ↳ 成功：imported=%s, skipped=%s",
                    data.get("imported", 0),
                    data.get("skipped", 0),
                )
                return data
            elif resp.status_code == 401:
                msg = f"认证失败：Collector-Key 无效 (HTTP {resp.status_code})"
                logger.error("  ↳ %s", msg)
                for item in batch:
                    stats.failed += 1
                    stats.errors.append({"item": item, "reason": msg})
                return None
            else:
                msg = f"HTTP {resp.status_code}: {resp.text[:200]}"
                logger.error("  ↳ 上传失败：%s", msg)
                for item in batch:
                    stats.failed += 1
                    stats.errors.append({"item": item, "reason": msg})
                return None

        except requests.ConnectionError:
            msg = f"连接失败：无法访问 {self._import_url}（服务是否已启动？）"
            logger.error("  ↳ %s", msg)
            for item in batch:
                stats.failed += 1
                stats.errors.append({"item": item, "reason": msg})
            return None
        except requests.Timeout:
            msg = "请求超时"
            logger.error("  ↳ %s", msg)
            for item in batch:
                stats.failed += 1
                stats.errors.append({"item": item, "reason": msg})
            return None
        except Exception as exc:
            msg = f"未知错误：{exc}"
            logger.error("  ↳ %s", msg)
            for item in batch:
                stats.failed += 1
                stats.errors.append({"item": item, "reason": msg})
            return None

    @staticmethod
    def _build_payload(
        batch: list[dict[str, str]],
        source: str,
    ) -> dict:
        """构建符合 /api/crawler/import 接口格式的请求体。"""
        games_payload = []
        for item in batch:
            games_payload.append({
                "title": item.get("title", ""),
                "cover": item.get("cover", ""),
                "description": item.get("description", ""),
                "category": item.get("category", ""),
                "size": item.get("size", ""),
                "download_url": item.get("download_url", ""),
                "original_url": item.get("original_url", ""),
                "source": item.get("source", source),
            })
        return {"games": games_payload, "source": source}

    # ------------------------------------------------------------------
    # 失败数据持久化
    # ------------------------------------------------------------------

    def save_failures(
        self,
        stats: UploadStats,
        log_dir: str = "logs",
    ) -> Optional[Path]:
        """将上传失败的数据写入 logs/ 目录。

        Args:
            stats: 上传结果统计（含 errors 列表）。
            log_dir: 日志目录路径。

        Returns:
            写入的文件路径，无失败数据时返回 None。
        """
        if not stats.errors:
            return None

        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = log_path / f"upload_failures_{timestamp}.json"

        failures = []
        for err in stats.errors:
            failures.append({
                "item": err.get("item", {}),
                "reason": err.get("reason", "unknown"),
            })

        data = {
            "timestamp": datetime.now().isoformat(),
            "total_failures": len(failures),
            "failures": failures,
        }

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info("失败数据已写入 %s（%d 条）", filename, len(failures))
        return filename
