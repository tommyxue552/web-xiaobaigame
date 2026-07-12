# crawler/scheduler/engine.py
# ===========================
# 自动定时采集调度引擎。
#
# 职责：
#   1. 读取 sites.yaml 获取启用的站点列表
#   2. 按 COLLECT_SCHEDULE_TIME 配置创建每日定时任务
#   3. 执行 Spider → Upload 完整链路
#   4. 持久化运行记录
#
# 用法：
#   from crawler.scheduler.engine import SchedulerEngine
#   engine = SchedulerEngine()
#   engine.start()          # 启动后台定时器
#   engine.run_once()       # 立即执行一次（用于测试）

from __future__ import annotations

import json
import logging
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger("crawler.scheduler")

# ---------------------------------------------------------------------------
# 延迟导入 —— 避免循环依赖，同时保证引擎在模块加载后可用
# ---------------------------------------------------------------------------

def _import_pipeline():
    """延迟加载 main 模块的运行管道，避免导入时的副作用。"""
    # 确保项目根在 path 中
    project_root = Path(__file__).resolve().parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))


def _get_spiders():
    """返回 Spider 注册表。延迟导入避免循环。"""
    from crawler.spiders import GameshareSpider
    return {"gameshare": GameshareSpider}


def _get_uploader():
    """返回 Uploader 类。延迟导入。"""
    from uploader import Uploader
    return Uploader


# ---------------------------------------------------------------------------
# 引擎主体
# ---------------------------------------------------------------------------


class SchedulerEngine:
    """自动定时采集引擎。

    Attributes:
        sites: 站点配置列表（从 sites.yaml 读取）。
        scheduler: APScheduler BackgroundScheduler 实例。
        _running: 引擎是否已启动。
    """

    def __init__(
        self,
        sites_config_path: str | Path | None = None,
        schedule_time: str | None = None,
        timezone: str | None = None,
        upload_url: str | None = None,
        upload_limit: int | None = None,
        log_dir: str | None = None,
        run_records_dir: str | Path | None = None,
    ):
        """初始化调度引擎。

        Args:
            sites_config_path: sites.yaml 路径，默认从 settings 读取。
            schedule_time: 定时采集时间 HH:MM，默认从 settings 读取。
            timezone: 时区字符串，默认系统本地。
            upload_url: API 上传地址。
            upload_limit: 上传数量限制（0=不限制）。
            log_dir: 日志目录。
            run_records_dir: 运行记录保存目录。
        """
        # 延迟导入 settings，避免 config 包未就绪时报错
        from config.settings import (
            SITES_CONFIG_PATH,
            COLLECT_SCHEDULE_TIME,
            SCHEDULER_TIMEZONE,
            DEFAULT_UPLOAD_URL,
            DEFAULT_UPLOAD_LIMIT,
            LOG_DIR,
            RUN_RECORDS_DIR,
        )

        self.sites_config_path = Path(sites_config_path or SITES_CONFIG_PATH)
        self.schedule_time = schedule_time or COLLECT_SCHEDULE_TIME
        self.timezone = timezone if timezone is not None else SCHEDULER_TIMEZONE
        self.upload_url: str = upload_url or DEFAULT_UPLOAD_URL
        self.upload_limit: int = (
            upload_limit if upload_limit is not None else DEFAULT_UPLOAD_LIMIT
        )
        self.log_dir: str = log_dir or LOG_DIR
        self.run_records_dir: Path = Path(run_records_dir or RUN_RECORDS_DIR)

        self.sites: list[dict[str, Any]] = []
        self.scheduler: BackgroundScheduler | None = None

        # 确保记录目录存在
        self.run_records_dir.mkdir(parents=True, exist_ok=True)

        # 加载站点配置
        self._load_sites_config()

    # ------------------------------------------------------------------
    # 站点配置
    # ------------------------------------------------------------------

    def _load_sites_config(self) -> None:
        """从 sites.yaml 加载站点配置。"""
        if not self.sites_config_path.exists():
            logger.warning(
                "站点配置文件不存在：%s，将使用空列表",
                self.sites_config_path,
            )
            self.sites = []
            return

        with open(self.sites_config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        self.sites = data.get("sites", []) if data else []

        enabled = [s["name"] for s in self.sites if s.get("enabled", False)]
        logger.info(
            "站点配置加载完成：共 %d 个站点，启用 %d 个：%s",
            len(self.sites),
            len(enabled),
            ", ".join(enabled) if enabled else "(无)",
        )

    def get_enabled_sites(self) -> list[str]:
        """获取启用的站点名称列表。"""
        return [s["name"] for s in self.sites if s.get("enabled", False)]

    # ------------------------------------------------------------------
    # 启动 / 停止
    # ------------------------------------------------------------------

    def start(self) -> None:
        """启动后台定时调度器。

        根据 COLLECT_SCHEDULE_TIME 创建每日 cron 任务，
        调度器在后台线程运行，主线程保持阻塞。
        """
        enabled = self.get_enabled_sites()
        if not enabled:
            logger.warning("没有启用的站点，调度器启动但不会执行任何任务")

        hour, minute = self._parse_schedule_time()

        self.scheduler = BackgroundScheduler(
            timezone=self.timezone,
            daemon=False,
        )

        self.scheduler.add_job(
            func=self._execute_all,
            trigger=CronTrigger(hour=hour, minute=minute),
            id="daily_collect",
            name="每日自动采集",
            replace_existing=True,
        )

        self.scheduler.start()

        logger.info(
            "调度器已启动，每日 %02d:%02d 执行采集任务（时区：%s）",
            hour,
            minute,
            self.timezone or "系统本地",
        )
        logger.info("启用的站点：%s", ", ".join(enabled) if enabled else "(无)")

        # 打印下一次执行时间
        next_run = self.scheduler.get_job("daily_collect").next_run_time
        if next_run:
            logger.info("下一次执行时间：%s", next_run.isoformat())

    def stop(self) -> None:
        """停止调度器。"""
        if self.scheduler is not None:
            self.scheduler.shutdown(wait=False)
            logger.info("调度器已停止")

    # ------------------------------------------------------------------
    # 执行
    # ------------------------------------------------------------------

    def run_once(self, site: str | None = None) -> dict[str, Any]:
        """立即执行一次采集（不等待定时触发）。

        Args:
            site: 指定站点名，None 表示所有启用站点。

        Returns:
            汇总结果 dict。
        """
        if site:
            return self._execute_site(site)

        results: dict[str, Any] = {}
        for site_name in self.get_enabled_sites():
            results[site_name] = self._execute_site(site_name)
        return results

    def _execute_all(self) -> None:
        """定时任务回调：遍历所有启用站点并执行采集。"""
        logger.info("=" * 60)
        logger.info("定时采集任务触发 — %s", datetime.now().isoformat())
        logger.info("=" * 60)

        enabled = self.get_enabled_sites()
        if not enabled:
            logger.warning("没有启用的站点，跳过执行")
            return

        for site_name in enabled:
            self._execute_site(site_name)

        logger.info("本轮定时采集全部完成")

    def _execute_site(self, site_name: str) -> dict[str, Any]:
        """执行单个站点的采集 → 上传链路。

        Args:
            site_name: 站点标识。

        Returns:
            执行统计 dict。
        """
        from crawler.scheduler.models import RunRecord

        record = RunRecord(
            site=site_name,
            start_time=datetime.now(),
        )

        logger.info("-" * 50)
        logger.info("[%s] 开始执行采集任务", site_name)

        try:
            # ---- 1. 获取 Spider ----
            spiders = _get_spiders()
            spider_cls = spiders.get(site_name)
            if spider_cls is None:
                raise ValueError(f"未知的采集源：{site_name}")

            # ---- 2. 运行 Spider ----
            spider = spider_cls()
            crawl_results = spider.run()
            items = spider.collected_items

            # 应用数量限制
            if self.upload_limit > 0 and len(items) > self.upload_limit:
                logger.info(
                    "[%s] 应用数量限制：%d → %d 条",
                    site_name,
                    len(items),
                    self.upload_limit,
                )
                items = items[:self.upload_limit]

            record.crawled_count = len(crawl_results)
            record.parsed_count = len(items)

            logger.info(
                "[%s] 采集完成：请求 %d 次，解析 %d 条",
                site_name,
                record.crawled_count,
                record.parsed_count,
            )

            # ---- 3. 上传到 API ----
            Uploader = _get_uploader()
            uploader = Uploader(base_url=self.upload_url)
            stats = uploader.upload(
                items,
                source=site_name,
                crawled_count=record.crawled_count,
            )

            record.uploaded_count = stats.uploaded
            record.failed_count = stats.failed
            record.duplicated_count = stats.duplicated
            record.status = "success"

            # 保存失败数据
            uploader.save_failures(stats, log_dir=self.log_dir)

        except Exception as exc:
            record.status = "failed"
            record.error_message = str(exc)
            logger.error(
                "[%s] 采集任务异常：%s\n%s",
                site_name,
                exc,
                traceback.format_exc(),
            )

        finally:
            record.end_time = datetime.now()
            duration = record.duration_seconds or 0
            logger.info(
                "[%s] 任务结束 — 状态：%s，耗时 %.1fs",
                site_name,
                record.status,
                duration,
            )

            # 持久化运行记录
            self._save_run_record(record)

        return record.to_dict()

    # ------------------------------------------------------------------
    # 运行记录
    # ------------------------------------------------------------------

    def _save_run_record(self, record) -> None:
        """将运行记录保存为 JSON 文件。"""
        from crawler.scheduler.models import RunRecord

        timestamp = record.start_time.strftime("%Y%m%d_%H%M%S")
        filename = self.run_records_dir / f"{record.site}_{timestamp}.json"

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(record.to_dict(), f, ensure_ascii=False, indent=2)

        logger.info("[%s] 运行记录已保存：%s", record.site, filename)

    # ------------------------------------------------------------------
    # 工具方法
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_schedule_time() -> tuple[int, int]:
        """解析 HH:MM 格式的时间字符串。

        Returns:
            (hour, minute) 元组。
        """
        from config.settings import COLLECT_SCHEDULE_TIME

        time_str = COLLECT_SCHEDULE_TIME
        try:
            parts = time_str.strip().split(":")
            hour = int(parts[0])
            minute = int(parts[1])
            return hour, minute
        except (ValueError, IndexError):
            logger.warning(
                "时间格式错误：%s（期望 HH:MM），回退到 03:00",
                time_str,
            )
            return 3, 0


# ---------------------------------------------------------------------------
# 便捷函数
# ---------------------------------------------------------------------------


def run_scheduler_blocking() -> None:
    """启动调度器并保持主线程存活。

    适用于 `python main.py --scheduler` 入口。
    """
    _import_pipeline()

    engine = SchedulerEngine()
    engine.start()

    logger.info("调度器运行中，按 Ctrl+C 停止...")

    try:
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        logger.info("收到停止信号，正在关闭调度器...")
        engine.stop()


def run_once(site: str | None = None) -> dict[str, Any]:
    """立即执行一次完整的采集链路（用于测试）。

    Args:
        site: 指定站点名，None 表示所有启用站点。

    Returns:
        执行结果汇总。
    """
    _import_pipeline()

    engine = SchedulerEngine()
    return engine.run_once(site=site)
