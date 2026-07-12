# -*- coding: utf-8 -*-
"""
main.py —— 采集器入口
=====================
命令行入口，串联 Spider 采集 → uploader 上传的完整链路。

用法：
    # 手动模式 —— 仅采集
    python main.py --site gameshare

    # 手动模式 —— 采集并上传
    python main.py --site gameshare --upload

    # 手动模式 —— 指定上传目标与数量限制
    python main.py --site gameshare --upload --url http://localhost:8000 --limit 10

    # 自动模式 —— 启动定时调度器
    python main.py --scheduler

    # 自动模式 —— 立即执行一次（测试用）
    python main.py --scheduler --run-now
"""

from __future__ import annotations

import argparse
import logging
import sys
import os
from pathlib import Path

# 确保项目根目录在 sys.path 中
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from crawler.spiders import GameshareSpider
from uploader import Uploader, UploadStats


# ---------------------------------------------------------------------------
# 日志配置
# ---------------------------------------------------------------------------

def setup_logging(log_dir: str = "logs") -> None:
    """配置日志：控制台 + 文件双输出。"""
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 根日志器
    root = logging.getLogger()
    root.setLevel(logging.INFO)

    # 控制台
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(fmt)
    root.addHandler(console)

    # 文件
    file_handler = logging.FileHandler(
        log_path / "crawler_main.log", encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(fmt)
    root.addHandler(file_handler)


# ---------------------------------------------------------------------------
# Spider 注册表
# ---------------------------------------------------------------------------

SPIDERS = {
    "gameshare": GameshareSpider,
}


# ---------------------------------------------------------------------------
# 手动采集主流程
# ---------------------------------------------------------------------------

def run_pipeline(
    site: str,
    upload: bool = False,
    limit: int = 0,
    base_url: str = "http://localhost:8000",
    log_dir: str = "logs",
) -> dict:
    """执行采集 → 上传完整链路。

    Args:
        site: 采集源标识（如 "gameshare"）。
        upload: 是否上传到 API。
        limit: 限制采集条数（0 表示不限制）。
        base_url: API 服务地址。
        log_dir: 日志目录。

    Returns:
        汇总统计 dict。
    """
    log = logging.getLogger("main")

    # ---- 1. 获取 Spider 类 ----
    spider_cls = SPIDERS.get(site)
    if spider_cls is None:
        log.error("未知的采集源：%s（可用：%s）", site, ", ".join(SPIDERS))
        sys.exit(1)

    # ---- 2. 运行采集 ----
    log.info("=" * 50)
    log.info("启动采集器：%s", site)
    log.info("=" * 50)

    spider = spider_cls()
    results = spider.run()
    items = spider.collected_items

    # 应用数量限制
    if limit > 0 and len(items) > limit:
        log.info("应用数量限制：%d → %d 条", len(items), limit)
        items = items[:limit]

    crawled_count = len(results)
    parsed_count = len(items)

    log.info("采集完成：请求 %d 次，解析 %d 条", crawled_count, parsed_count)

    # ---- 3. 显示样例 ----
    for i, item in enumerate(items[:3], 1):
        log.info("  样例 %d: %s", i, item.get("title", "N/A"))

    # ---- 4. 上传 ----
    if not upload:
        log.info("跳过上传（未指定 --upload）")
        return {
            "crawled": crawled_count,
            "parsed": parsed_count,
            "uploaded": 0,
            "failed": 0,
            "duplicated": 0,
            "items": items,
        }

    log.info("-" * 50)
    log.info("开始上传到 %s", base_url)

    uploader = Uploader(base_url=base_url)
    stats = uploader.upload(items, source=site, crawled_count=crawled_count)

    # ---- 5. 保存失败数据 ----
    uploader.save_failures(stats, log_dir=log_dir)

    return {
        "crawled": stats.crawled,
        "parsed": stats.parsed,
        "uploaded": stats.uploaded,
        "failed": stats.failed,
        "duplicated": stats.duplicated,
        "items": items,
    }


def print_summary(result: dict) -> None:
    """打印最终统计摘要。"""
    print()
    print("=" * 50)
    print("  采集链路测试 — 最终统计")
    print("=" * 50)
    print(f"  采集数量：    {result['crawled']:>5}")
    print(f"  解析成功数量：{result['parsed']:>5}")
    print(f"  上传成功数量：{result['uploaded']:>5}")
    print(f"  上传失败数量：{result['failed']:>5}")
    print(f"  重复数量：    {result['duplicated']:>5}")
    print("=" * 50)


# ---------------------------------------------------------------------------
# 调度器模式
# ---------------------------------------------------------------------------

def run_scheduler_mode(run_now: bool = False, log_dir: str = "logs") -> None:
    """启动调度器模式。

    Args:
        run_now: 启动后立即执行一次采集。
        log_dir: 日志目录。
    """
    from crawler.scheduler import run_scheduler_blocking, run_once

    log = logging.getLogger("main")

    log.info("=" * 50)
    log.info("启动自动定时采集模式")
    log.info("=" * 50)

    if run_now:
        log.info("--run-now：立即执行一次采集...")
        result = run_once()
        for site_name, stats in result.items():
            log.info(
                "[%s] 采集 %d → 上传 %d（成功）/ %d（失败）/ %d（重复）",
                site_name,
                stats.get("parsed_count", 0),
                stats.get("uploaded_count", 0),
                stats.get("failed_count", 0),
                stats.get("duplicated_count", 0),
            )

    # 启动调度器（阻塞）
    run_scheduler_blocking()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="小白游戏资源站 — 采集器命令行工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  # 手动模式
  python main.py --site gameshare
  python main.py --site gameshare --upload --limit 10

  # 自动定时模式
  python main.py --scheduler
  python main.py --scheduler --run-now
        """,
    )

    # ---- 手动模式参数 ----
    parser.add_argument(
        "--site", "-s",
        choices=list(SPIDERS.keys()),
        help="采集源标识（手动模式必填）",
    )
    parser.add_argument(
        "--upload", "-u",
        action="store_true",
        help="是否上传到站点 API",
    )
    parser.add_argument(
        "--limit", "-l",
        type=int,
        default=10,
        help="限制采集条数（默认 10）",
    )
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="API 服务地址（默认 http://localhost:8000）",
    )
    parser.add_argument(
        "--log-dir",
        default="logs",
        help="日志目录（默认 logs）",
    )
    parser.add_argument(
        "--no-limit",
        action="store_true",
        help="不限制采集数量",
    )

    # ---- 调度器模式参数 ----
    parser.add_argument(
        "--scheduler",
        action="store_true",
        help="启动自动定时采集模式（后台常驻运行）",
    )
    parser.add_argument(
        "--run-now",
        action="store_true",
        help="启动调度器后立即执行一次采集（需配合 --scheduler）",
    )

    args = parser.parse_args()

    # 日志
    setup_logging(args.log_dir)

    # ---- 调度器模式 ----
    if args.scheduler:
        run_scheduler_mode(
            run_now=args.run_now,
            log_dir=args.log_dir,
        )
        return

    # ---- 手动模式 ----
    if not args.site:
        parser.error("手动模式需要指定 --site，或使用 --scheduler 进入自动模式")

    # 限制
    limit = 0 if args.no_limit else args.limit

    # 运行
    result = run_pipeline(
        site=args.site,
        upload=args.upload,
        limit=limit,
        base_url=args.url,
        log_dir=args.log_dir,
    )

    # 统计
    print_summary(result)


if __name__ == "__main__":
    main()
