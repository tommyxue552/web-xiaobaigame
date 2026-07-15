# -*- coding: utf-8 -*-
"""
下载资源管理 API
--------------
下载资源 CRUD 接口。支持通过 provider_id 关联 DownloadProvider。
兼容旧的 provider 字符串字段。
"""
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import joinedload
from pydantic import BaseModel, Field
from typing import Optional

from ..core.database import get_db
from ..core.auth import get_current_admin
from ..models.download_resource import DownloadResource
from ..models.download_provider import DownloadProvider
from ..models.game import Game
from ..models.admin_user import AdminUser

router = APIRouter(prefix="/api/admin", tags=["Download Resources"])

VALID_STATUSES = {"pending", "active", "disabled", "invalid"}


# ==================== Pydantic models ====================


class DownloadResourceCreate(BaseModel):
    game_id: int = Field(..., ge=1, description="关联游戏ID")
    provider_id: Optional[int] = Field(None, description="下载渠道ID（优先使用）")
    provider: Optional[str] = Field("baidu", max_length=20, description="网盘代码（兼容旧数据，baidu/quark/alipan/115）")
    title: Optional[str] = Field("", max_length=255, description="资源标题")
    origin_url: Optional[str] = Field("", max_length=1000, description="原始来源URL")
    my_share_url: Optional[str] = Field("", max_length=1000, description="我的分享链接")
    extract_code: Optional[str] = Field("", max_length=20, description="提取码")
    remark: Optional[str] = Field("", max_length=2000, description="备注")
    display_order: Optional[int] = Field(0, description="显示排序")
    status: Optional[str] = Field("active", max_length=20, description="状态")


class DownloadResourceUpdate(BaseModel):
    game_id: Optional[int] = Field(None, ge=1, description="关联游戏ID")
    provider_id: Optional[int] = Field(None, description="下载渠道ID（优先使用）")
    provider: Optional[str] = Field(None, max_length=20, description="网盘代码（兼容旧数据）")
    title: Optional[str] = Field(None, max_length=255, description="资源标题")
    origin_url: Optional[str] = Field(None, max_length=1000, description="原始来源URL")
    my_share_url: Optional[str] = Field(None, max_length=1000, description="我的分享链接")
    extract_code: Optional[str] = Field(None, max_length=20, description="提取码")
    remark: Optional[str] = Field(None, max_length=2000, description="备注")
    display_order: Optional[int] = Field(None, description="显示排序")
    status: Optional[str] = Field(None, max_length=20, description="状态")


class DownloadPriorityUpdate(BaseModel):
    priority: int = Field(..., ge=0, le=10000, description='优先级（越大越优先）')


class DownloadPrimaryUpdate(BaseModel):
    is_primary: bool = Field(..., description='是否设为默认资源')


# ==================== Helpers ====================


async def _resolve_provider_id(db: AsyncSession, provider_id: Optional[int], provider_code: Optional[str]) -> int:
    """Resolve provider_id from provider_id or provider code string."""
    if provider_id:
        # Verify it exists
        result = await db.execute(select(DownloadProvider).where(DownloadProvider.id == provider_id))
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail=f"渠道ID {provider_id} 不存在")
        return provider_id

    if provider_code:
        result = await db.execute(select(DownloadProvider).where(DownloadProvider.code == provider_code))
        p = result.scalar_one_or_none()
        if p:
            return p.id
        # Fallback: try to find by name
        result = await db.execute(select(DownloadProvider).where(DownloadProvider.name == provider_code))
        p = result.scalar_one_or_none()
        if p:
            return p.id

    # Default: use provider code to find, or fallback to baidu
    if provider_code:
        result = await db.execute(select(DownloadProvider).where(DownloadProvider.code == "baidu"))
        p = result.scalar_one_or_none()
        if p:
            return p.id

    raise HTTPException(status_code=400, detail="无法确定下载渠道，请指定 provider_id")


def serialize_download_resource(dr: DownloadResource) -> dict:
    provider_code = ""
    provider_label = ""
    if dr.provider_rel:
        provider_code = dr.provider_rel.code
        provider_label = dr.provider_rel.name
    elif dr.provider:
        provider_code = dr.provider
        provider_label = dr.provider  # fallback

    return {
        "id": dr.id,
        "game_id": dr.game_id,
        "game_title": dr.game.title if dr.game else "",
        "provider_id": dr.provider_id,
        "provider": provider_code,
        "provider_label": provider_label,
        "title": dr.title,
        "origin_url": dr.origin_url,
        "my_share_url": dr.my_share_url,
        "extract_code": dr.extract_code,
        "remark": dr.remark,
        "display_order": dr.display_order,
        "priority": dr.priority if dr.priority is not None else 100,
        "is_primary": bool(dr.is_primary) if dr.is_primary is not None else False,
        "success_count": dr.success_count if dr.success_count is not None else 0,
        "fail_count": dr.fail_count if dr.fail_count is not None else 0,
        "last_check_at": str(dr.last_check_at) if dr.last_check_at else None,
        "status": dr.status,
        "created_at": str(dr.created_at) if dr.created_at else None,
        "updated_at": str(dr.updated_at) if dr.updated_at else None,
    }


# ==================== CRUD endpoints ====================


@router.get(
    "/download-resources",
    summary="[后台] 下载资源列表",
)
async def list_download_resources(
    game_id: Optional[int] = Query(None, ge=1, description="按游戏ID筛选"),
    keyword: Optional[str] = Query(None, description="按游戏名称搜索"),
    provider: Optional[str] = Query(None, description="按网盘代码筛选"),
    provider_id: Optional[int] = Query(None, description="按渠道ID筛选"),
    status_filter: Optional[str] = Query(None, alias="status", description="按状态筛选"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    query = select(DownloadResource).options(
        joinedload(DownloadResource.game),
        joinedload(DownloadResource.provider_rel),
    )
    count_query = select(func.count()).select_from(DownloadResource)

    if game_id:
        query = query.where(DownloadResource.game_id == game_id)
        count_query = count_query.where(DownloadResource.game_id == game_id)

    if provider_id:
        query = query.where(DownloadResource.provider_id == provider_id)
        count_query = count_query.where(DownloadResource.provider_id == provider_id)
    elif provider:
        query = query.where(DownloadResource.provider == provider)
        count_query = count_query.where(DownloadResource.provider == provider)

    if status_filter:
        query = query.where(DownloadResource.status == status_filter)
        count_query = count_query.where(DownloadResource.status == status_filter)

    if keyword:
        query = query.join(Game).where(Game.title.contains(keyword))
        count_query = count_query.join(Game).where(Game.title.contains(keyword))

    total = (await db.execute(count_query)).scalar() or 0
    offset = (page - 1) * page_size
    query = (
        query.order_by(DownloadResource.priority.desc())
        .order_by(DownloadResource.updated_at.desc())
        .offset(offset)
        .limit(page_size)
    )

    result = await db.execute(query)
    resources = result.unique().scalars().all()

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
    summary="[后台] 获取单个资源",
)
async def get_download_resource(
    resource_id: int,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(DownloadResource)
        .options(joinedload(DownloadResource.game), joinedload(DownloadResource.provider_rel))
        .where(DownloadResource.id == resource_id)
    )
    resource = result.unique().scalar_one_or_none()
    if not resource:
        raise HTTPException(status_code=404, detail="资源不存在")

    return {
        "code": 0,
        "message": "success",
        "data": serialize_download_resource(resource),
    }


@router.post(
    "/download-resources",
    summary="[后台] 新增下载资源",
    status_code=201,
)
async def create_download_resource(
    body: DownloadResourceCreate,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    if body.status and body.status not in VALID_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"无效的状态值，可选：{', '.join(sorted(VALID_STATUSES))}",
        )

    game_result = await db.execute(select(Game).where(Game.id == body.game_id))
    if not game_result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="游戏不存在")

    # Resolve provider
    pid = await _resolve_provider_id(db, body.provider_id, body.provider)

    # Build resource data
    data = body.model_dump()
    data["provider_id"] = pid
    # Keep provider string for backward compat
    if not data.get("provider"):
        data["provider"] = body.provider or "baidu"

    resource = DownloadResource(**data)
    db.add(resource)
    await db.flush()
    await db.refresh(resource)

    # Re-fetch with relationships
    result = await db.execute(
        select(DownloadResource)
        .options(joinedload(DownloadResource.game), joinedload(DownloadResource.provider_rel))
        .where(DownloadResource.id == resource.id)
    )
    resource = result.unique().scalar_one()

    return {
        "code": 0,
        "message": "创建成功",
        "data": serialize_download_resource(resource),
    }


@router.put(
    "/download-resources/{resource_id}",
    summary="[后台] 更新下载资源",
)
async def update_download_resource(
    resource_id: int,
    body: DownloadResourceUpdate,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(DownloadResource)
        .options(joinedload(DownloadResource.game), joinedload(DownloadResource.provider_rel))
        .where(DownloadResource.id == resource_id)
    )
    resource = result.unique().scalar_one_or_none()
    if not resource:
        raise HTTPException(status_code=404, detail="资源不存在")

    update_data = body.model_dump(exclude_unset=True)

    if "status" in update_data and update_data["status"] not in VALID_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"无效的状态值，可选：{', '.join(sorted(VALID_STATUSES))}",
        )
    if "game_id" in update_data:
        game_result = await db.execute(select(Game).where(Game.id == update_data["game_id"]))
        if not game_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="游戏不存在")

    # Resolve provider if provided
    if "provider_id" in update_data or "provider" in update_data:
        pid = await _resolve_provider_id(
            db,
            update_data.pop("provider_id", None),
            update_data.pop("provider", None),
        )
        update_data["provider_id"] = pid

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
    summary="[后台] 删除下载资源",
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
        raise HTTPException(status_code=404, detail="资源不存在")

    await db.delete(resource)
    await db.flush()

    return {"code": 0, "message": "删除成功"}



# ==================== 模块7.8: 优先级与默认资源管理 ====================

@router.put(
    "/download-resource/{resource_id}/priority",
    summary="[后台] 修改下载资源优先级（模块7.8）",
)
async def update_resource_priority(
    resource_id: int,
    body: DownloadPriorityUpdate,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(DownloadResource)
        .options(joinedload(DownloadResource.game), joinedload(DownloadResource.provider_rel))
        .where(DownloadResource.id == resource_id)
    )
    resource = result.unique().scalar_one_or_none()
    if not resource:
        raise HTTPException(status_code=404, detail="资源不存在")

    resource.priority = body.priority
    await db.flush()
    await db.refresh(resource)

    return {
        "code": 0,
        "message": "优先级已更新",
        "data": serialize_download_resource(resource),
    }


@router.put(
    "/download-resource/{resource_id}/primary",
    summary="[后台] 设置/取消默认资源（模块7.8）",
)
async def update_resource_primary(
    resource_id: int,
    body: DownloadPrimaryUpdate,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(DownloadResource)
        .options(joinedload(DownloadResource.game), joinedload(DownloadResource.provider_rel))
        .where(DownloadResource.id == resource_id)
    )
    resource = result.unique().scalar_one_or_none()
    if not resource:
        raise HTTPException(status_code=404, detail="资源不存在")

    if body.is_primary:
        # 自动取消同游戏其它资源的 primary 标记
        await db.execute(
            DownloadResource.__table__.update()
            .where(
                DownloadResource.game_id == resource.game_id,
                DownloadResource.id != resource.id,
            )
            .values(is_primary=False)
        )

    resource.is_primary = body.is_primary
    await db.flush()
    await db.refresh(resource)

    return {
        "code": 0,
        "message": "默认资源已更新",
        "data": serialize_download_resource(resource),
    }

# ==================== Games list helper ====================


@router.get(
    "/download-resources-games",
    summary="[后台] 获取游戏列表（用于下拉选择）",
)
async def list_games_for_select(
    keyword: Optional[str] = Query(None, description="游戏名称搜索"),
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    query = select(Game.id, Game.title).order_by(Game.title)
    if keyword:
        query = query.where(Game.title.contains(keyword))
    query = query.limit(200)
    result = await db.execute(query)
    rows = result.all()
    return {
        "code": 0,
        "message": "success",
        "data": [{"id": r.id, "title": r.title} for r in rows],
    }
