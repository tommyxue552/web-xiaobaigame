# -*- coding: utf-8 -*-
"""
下载统计 API（模块7.6）
---------------------
提供下载行为统计数据查询接口，需要管理员权限。
包含：总览、热门游戏排行、网盘渠道统计、时间趋势。
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text, and_, case
from datetime import date, timedelta

from ..core.database import get_db
from ..core.auth import get_current_admin
from ..models.admin_user import AdminUser
from ..models.download_log import DownloadLog
from ..models.game import Game
from ..models.download_provider import DownloadProvider

router = APIRouter(prefix="/api/admin/download-stats", tags=["DownloadStats"])


def _today_range():
    """返回今天的日期范围（SQLite 日期字符串）。"""
    today = date.today().isoformat()
    return today, today


def _yesterday_range():
    """返回昨天的日期范围。"""
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    return yesterday, yesterday


@router.get("/overview", summary="下载统计总览")
async def download_overview(
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """返回今日/昨日/总下载次数（view + redirect）。"""
    today, _ = _today_range()
    yesterday, _ = _yesterday_range()

    # 今日下载
    today_result = await db.execute(
        select(func.count()).select_from(DownloadLog).where(
            func.date(DownloadLog.created_at) == today
        )
    )
    today_count = today_result.scalar() or 0

    # 昨日下载
    yesterday_result = await db.execute(
        select(func.count()).select_from(DownloadLog).where(
            func.date(DownloadLog.created_at) == yesterday
        )
    )
    yesterday_count = yesterday_result.scalar() or 0

    # 总下载
    total_result = await db.execute(
        select(func.count()).select_from(DownloadLog)
    )
    total_count = total_result.scalar() or 0

    # 今日分类统计
    today_view = await db.execute(
        select(func.count()).select_from(DownloadLog).where(
            func.date(DownloadLog.created_at) == today,
            DownloadLog.action == "view",
        )
    )
    today_view_count = today_view.scalar() or 0

    today_redirect = await db.execute(
        select(func.count()).select_from(DownloadLog).where(
            func.date(DownloadLog.created_at) == today,
            DownloadLog.action == "redirect",
        )
    )
    today_redirect_count = today_redirect.scalar() or 0

    return {
        "code": 0,
        "message": "success",
        "data": {
            "today": today_count,
            "today_view": today_view_count,
            "today_redirect": today_redirect_count,
            "yesterday": yesterday_count,
            "total": total_count,
        },
    }


@router.get("/top-games", summary="热门游戏下载排行")
async def top_games(
    limit: int = Query(10, ge=1, le=100, description="返回数量"),
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """按下载次数排行，返回游戏名称和下载次数。"""
    result = await db.execute(
        select(
            DownloadLog.game_id,
            Game.title,
            func.count(DownloadLog.id).label("download_count"),
        )
        .join(Game, DownloadLog.game_id == Game.id, isouter=True)
        .where(DownloadLog.game_id.isnot(None))
        .group_by(DownloadLog.game_id)
        .order_by(func.count(DownloadLog.id).desc())
        .limit(limit)
    )
    rows = result.all()

    ranking = [
        {
            "game_id": row.game_id,
            "game_title": row.title or "(已删除游戏)",
            "download_count": row.download_count,
        }
        for row in rows
    ]

    return {
        "code": 0,
        "message": "success",
        "data": {"ranking": ranking, "total_items": len(ranking)},
    }


@router.get("/providers", summary="网盘渠道统计")
async def provider_stats(
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """按下载渠道统计访问次数和跳转次数。"""
    # 按 provider_id 分组统计
    result = await db.execute(
        select(
            DownloadLog.provider_id,
            DownloadProvider.name,
            DownloadProvider.code,
            func.count(DownloadLog.id).label("total_count"),
            func.sum(
                case(
                    (DownloadLog.action == "view", 1),
                    else_=0,
                )
            ).label("view_count"),
            func.sum(
                case(
                    (DownloadLog.action == "redirect", 1),
                    else_=0,
                )
            ).label("redirect_count"),
        )
        .join(
            DownloadProvider,
            DownloadLog.provider_id == DownloadProvider.id,
            isouter=True,
        )
        .where(DownloadLog.provider_id.isnot(None))
        .group_by(DownloadLog.provider_id)
        .order_by(func.count(DownloadLog.id).desc())
    )
    rows = result.all()

    providers = []
    for row in rows:
        providers.append({
            "provider_id": row.provider_id,
            "provider_name": row.name or "(未知渠道)",
            "provider_code": row.code or "",
            "total_count": row.total_count or 0,
            "view_count": row.view_count or 0,
            "redirect_count": row.redirect_count or 0,
        })

    return {
        "code": 0,
        "message": "success",
        "data": {"providers": providers},
    }


@router.get("/trend", summary="下载量时间趋势")
async def download_trend(
    days: int = Query(7, ge=1, le=90, description="统计天数"),
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """返回最近 N 天的每日下载量趋势。"""
    start_date = (date.today() - timedelta(days=days - 1)).isoformat()

    result = await db.execute(
        select(
            func.date(DownloadLog.created_at).label("stat_date"),
            func.count(DownloadLog.id).label("count"),
        )
        .where(func.date(DownloadLog.created_at) >= start_date)
        .group_by(func.date(DownloadLog.created_at))
        .order_by(func.date(DownloadLog.created_at))
    )
    rows = result.all()

    # 构造完整的日期序列（填充无数据的日期为 0）
    existing = {row.stat_date: row.count for row in rows}
    trend = []
    for i in range(days):
        d = (date.today() - timedelta(days=days - 1 - i)).isoformat()
        trend.append({"date": d, "count": existing.get(d, 0)})

    return {
        "code": 0,
        "message": "success",
        "data": {"trend": trend, "days": days},
    }
