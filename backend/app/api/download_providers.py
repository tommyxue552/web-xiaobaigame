# -*- coding: utf-8 -*-
"""
下载渠道管理 API
--------------
下载渠道 CRUD 接口。
"""
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel, Field
from typing import Optional

from ..core.database import get_db
from ..core.auth import get_current_admin
from ..models.download_provider import DownloadProvider
from ..models.download_resource import DownloadResource
from ..models.admin_user import AdminUser

router = APIRouter(prefix="/api/admin", tags=["Download Providers"])


# ==================== Pydantic models ====================

class DownloadProviderCreate(BaseModel):
    code: str = Field(..., max_length=20, description="渠道代码")
    name: str = Field(..., max_length=50, description="渠道名称")
    icon: Optional[str] = Field("", max_length=255, description="图标")
    status: Optional[str] = Field("active", max_length=20, description="状态")
    display_order: Optional[int] = Field(0, description="排序")
    remark: Optional[str] = Field("", max_length=2000, description="备注")


class DownloadProviderUpdate(BaseModel):
    code: Optional[str] = Field(None, max_length=20, description="渠道代码")
    name: Optional[str] = Field(None, max_length=50, description="渠道名称")
    icon: Optional[str] = Field(None, max_length=255, description="图标")
    status: Optional[str] = Field(None, max_length=20, description="状态")
    display_order: Optional[int] = Field(None, description="排序")
    remark: Optional[str] = Field(None, max_length=2000, description="备注")


# ==================== Serialization ====================

def serialize_provider(p: DownloadProvider) -> dict:
    return {
        "id": p.id,
        "code": p.code,
        "name": p.name,
        "icon": p.icon,
        "status": p.status,
        "display_order": p.display_order,
        "remark": p.remark,
        "created_at": str(p.created_at) if p.created_at else None,
        "updated_at": str(p.updated_at) if p.updated_at else None,
    }


# ==================== Helper ====================

async def _count_usage(db: AsyncSession, provider_id: int) -> int:
    """Count how many download_resources use this provider."""
    result = await db.execute(
        select(func.count()).select_from(DownloadResource).where(
            DownloadResource.provider_id == provider_id
        )
    )
    return result.scalar() or 0


# ==================== CRUD endpoints ====================

@router.get(
    "/download-providers",
    summary="[后台] 下载渠道列表",
)
async def list_providers(
    keyword: Optional[str] = Query(None, description="搜索名称或代码"),
    status_filter: Optional[str] = Query(None, alias="status", description="按状态筛选"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    query = select(DownloadProvider)
    count_query = select(func.count()).select_from(DownloadProvider)

    if status_filter:
        query = query.where(DownloadProvider.status == status_filter)
        count_query = count_query.where(DownloadProvider.status == status_filter)

    if keyword:
        like = f"%{keyword}%"
        query = query.where(
            (DownloadProvider.name.contains(keyword))
            | (DownloadProvider.code.contains(keyword))
        )
        count_query = count_query.where(
            (DownloadProvider.name.contains(keyword))
            | (DownloadProvider.code.contains(keyword))
        )

    total = (await db.execute(count_query)).scalar() or 0
    offset = (page - 1) * page_size

    query = (
        query.order_by(DownloadProvider.display_order.asc())
        .order_by(DownloadProvider.id.asc())
        .offset(offset)
        .limit(page_size)
    )

    result = await db.execute(query)
    providers = result.scalars().all()

    # Attach usage count
    items = []
    for p in providers:
        item = serialize_provider(p)
        item["usage_count"] = await _count_usage(db, p.id)
        items.append(item)

    return {
        "code": 0,
        "message": "success",
        "data": {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
        },
    }


@router.get(
    "/download-providers/active",
    summary="[后台] 获取启用的渠道列表（用于下拉选择）",
)
async def list_active_providers(
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(DownloadProvider)
        .where(DownloadProvider.status == "active")
        .order_by(DownloadProvider.display_order.asc())
    )
    providers = result.scalars().all()
    return {
        "code": 0,
        "message": "success",
        "data": [serialize_provider(p) for p in providers],
    }


@router.get(
    "/download-providers/{provider_id}",
    summary="[后台] 获取单个渠道",
)
async def get_provider(
    provider_id: int,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(DownloadProvider).where(DownloadProvider.id == provider_id)
    )
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="渠道不存在")

    item = serialize_provider(p)
    item["usage_count"] = await _count_usage(db, p.id)
    return {"code": 0, "message": "success", "data": item}


@router.post(
    "/download-providers",
    summary="[后台] 新增下载渠道",
    status_code=201,
)
async def create_provider(
    body: DownloadProviderCreate,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    # Check code uniqueness
    existing = await db.execute(
        select(DownloadProvider).where(DownloadProvider.code == body.code)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"渠道代码 '{body.code}' 已存在")

    provider = DownloadProvider(**body.model_dump())
    db.add(provider)
    await db.flush()
    await db.refresh(provider)

    return {
        "code": 0,
        "message": "创建成功",
        "data": serialize_provider(provider),
    }


@router.put(
    "/download-providers/{provider_id}",
    summary="[后台] 更新下载渠道",
)
async def update_provider(
    provider_id: int,
    body: DownloadProviderUpdate,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(DownloadProvider).where(DownloadProvider.id == provider_id)
    )
    provider = result.scalar_one_or_none()
    if not provider:
        raise HTTPException(status_code=404, detail="渠道不存在")

    update_data = body.model_dump(exclude_unset=True)

    # Check code uniqueness if changing
    if "code" in update_data and update_data["code"] != provider.code:
        existing = await db.execute(
            select(DownloadProvider).where(DownloadProvider.code == update_data["code"])
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail=f"渠道代码 '{update_data['code']}' 已存在")

    for key, value in update_data.items():
        setattr(provider, key, value)

    await db.flush()
    await db.refresh(provider)

    return {
        "code": 0,
        "message": "更新成功",
        "data": serialize_provider(provider),
    }


@router.delete(
    "/download-providers/{provider_id}",
    summary="[后台] 删除下载渠道",
)
async def delete_provider(
    provider_id: int,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(DownloadProvider).where(DownloadProvider.id == provider_id)
    )
    provider = result.scalar_one_or_none()
    if not provider:
        raise HTTPException(status_code=404, detail="渠道不存在")

    usage = await _count_usage(db, provider_id)
    if usage > 0:
        raise HTTPException(
            status_code=400,
            detail=f"该渠道正在被 {usage} 个下载资源使用，无法删除。请先解除关联。",
        )

    await db.delete(provider)
    await db.flush()

    return {"code": 0, "message": "删除成功"}
