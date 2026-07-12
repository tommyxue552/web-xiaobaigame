# -*- coding: utf-8 -*-
"""
下载资源管理 API
--------------
提供下载资源的 CRUD 操作，为后续网盘中转系统做准备。
所有接口需要管理员认证。
"""

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel, Field
from typing import Optional

from ..core.database import get_db
from ..core.auth import get_current_admin
from ..models.download_resource import DownloadResource
from ..models.game import Game
from ..models.admin_user import AdminUser

router = APIRouter(prefix="/api/admin", tags=["Download Resources"])


# ==================== 请求/响应模型 ====================


class DownloadResourceCreate(BaseModel):
    game_id: int = Field(..., ge=1, description="关联游戏ID")
    provider: Optional[str] = Field("baidu", max_length=20, description="网盘类型：baidu/quark/alipan/115")
    title: Optional[str] = Field("", max_length=255, description="资源标题")
    origin_url: Optional[str] = Field("", max_length=1000, description="原始来源URL")
    my_share_url: Optional[str] = Field("", max_length=1000, description="我的分享链接")
    extract_code: Optional[str] = Field("", max_length=20, description="提取码")
    status: Optional[str] = Field("active", max_length=20, description="状态")


class DownloadResourceUpdate(BaseModel):
    game_id: Optional[int] = Field(None, ge=1, description="关联游戏ID")
    provider: Optional[str] = Field(None, max_length=20, description="网盘类型")
    title: Optional[str] = Field(None, max_length=255, description="资源标题")
    origin_url: Optional[str] = Field(None, max_length=1000, description="原始来源URL")
    my_share_url: Optional[str] = Field(None, max_length=1000, description="我的分享链接")
    extract_code: Optional[str] = Field(None, max_length=20, description="提取码")
    status: Optional[str] = Field(None, max_length=20, description="状态")


VALID_PROVIDERS = {"baidu", "quark", "alipan", "115"}


# ==================== 序列化 ====================


def serialize_download_resource(dr: DownloadResource) -> dict:
    return {
        "id": dr.id,
        "game_id": dr.game_id,
        "provider": dr.provider,
        "title": dr.title,
        "origin_url": dr.origin_url,
        "my_share_url": dr.my_share_url,
        "extract_code": dr.extract_code,
        "status": dr.status,
        "created_at": str(dr.created_at) if dr.created_at else None,
        "updated_at": str(dr.updated_at) if dr.updated_at else None,
    }


# ==================== CRUD 接口 ====================


@router.get(
    "/download-resources",
    summary="[管理] 下载资源列表",
)
async def list_download_resources(
    game_id: Optional[int] = Query(None, ge=1, description="按游戏ID筛选"),
    provider: Optional[str] = Query(None, description="按网盘类型筛选"),
    status_filter: Optional[str] = Query(None, alias="status", description="按状态筛选"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    query = select(DownloadResource)
    count_base = select(func.count()).select_from(DownloadResource)

    if game_id:
        query = query.where(DownloadResource.game_id == game_id)
        count_base = count_base.where(DownloadResource.game_id == game_id)
    if provider:
        query = query.where(DownloadResource.provider == provider)
        count_base = count_base.where(DownloadResource.provider == provider)
    if status_filter:
        query = query.where(DownloadResource.status == status_filter)
        count_base = count_base.where(DownloadResource.status == status_filter)

    total = (await db.execute(count_base)).scalar() or 0
    offset = (page - 1) * page_size
    query = query.order_by(DownloadResource.updated_at.desc()).offset(offset).limit(page_size)

    result = await db.execute(query)
    resources = result.scalars().all()

    return {
        "code": 0,
        "message": "success",
        "data": {
            "items": [serialize_download_resource(r) for r in resources],
            "total": total,
            "page": page,
            "page_size": page_size,
        },
    }


@router.get(
    "/download-resources/{resource_id}",
    summary="[管理] 下载资源详情",
)
async def get_download_resource(
    resource_id: int,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(DownloadResource).where(DownloadResource.id == resource_id)
    )
    resource = result.scalar_one_or_none()
    if not resource:
        raise HTTPException(status_code=404, detail="下载资源不存在")

    return {
        "code": 0,
        "message": "success",
        "data": serialize_download_resource(resource),
    }


@router.post(
    "/download-resources",
    summary="[管理] 创建下载资源",
    status_code=201,
)
async def create_download_resource(
    body: DownloadResourceCreate,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    # 验证 provider
    if body.provider and body.provider not in VALID_PROVIDERS:
        raise HTTPException(
            status_code=400,
            detail=f"无效的网盘类型，支持：{', '.join(sorted(VALID_PROVIDERS))}",
        )

    # 验证游戏存在
    game_result = await db.execute(select(Game).where(Game.id == body.game_id))
    if not game_result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="游戏不存在")

    resource = DownloadResource(**body.model_dump())
    db.add(resource)
    await db.flush()
    await db.refresh(resource)

    return {
        "code": 0,
        "message": "创建成功",
        "data": serialize_download_resource(resource),
    }


@router.put(
    "/download-resources/{resource_id}",
    summary="[管理] 更新下载资源",
)
async def update_download_resource(
    resource_id: int,
    body: DownloadResourceUpdate,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(DownloadResource).where(DownloadResource.id == resource_id)
    )
    resource = result.scalar_one_or_none()
    if not resource:
        raise HTTPException(status_code=404, detail="下载资源不存在")

    update_data = body.model_dump(exclude_unset=True)

    # 验证 provider
    if "provider" in update_data and update_data["provider"] not in VALID_PROVIDERS:
        raise HTTPException(
            status_code=400,
            detail=f"无效的网盘类型，支持：{', '.join(sorted(VALID_PROVIDERS))}",
        )

    # 验证 game_id（如果传入）
    if "game_id" in update_data:
        game_result = await db.execute(select(Game).where(Game.id == update_data["game_id"]))
        if not game_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="游戏不存在")

    for key, value in update_data.items():
        setattr(resource, key, value)

    await db.flush()
    await db.refresh(resource)

    return {
        "code": 0,
        "message": "更新成功",
        "data": serialize_download_resource(resource),
    }


@router.delete(
    "/download-resources/{resource_id}",
    summary="[管理] 删除下载资源",
)
async def delete_download_resource(
    resource_id: int,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(DownloadResource).where(DownloadResource.id == resource_id)
    )
    resource = result.scalar_one_or_none()
    if not resource:
        raise HTTPException(status_code=404, detail="下载资源不存在")

    await db.delete(resource)
    await db.flush()

    return {"code": 0, "message": "删除成功"}
