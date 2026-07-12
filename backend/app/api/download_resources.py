# -*- coding: utf-8 -*-
"""
?????? API
--------------
??????? CRUD ????????????????
????????????
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
from ..models.game import Game
from ..models.admin_user import AdminUser

router = APIRouter(prefix="/api/admin", tags=["Download Resources"])

VALID_PROVIDERS = {"baidu", "quark", "alipan", "115"}
VALID_STATUSES = {"pending", "active", "disabled", "invalid"}

PROVIDER_LABELS = {"baidu": "百度网盘", "quark": "夸克网盘", "alipan": "阿里云盘", "115": "115网盘"}


# ==================== Pydantic models ====================


class DownloadResourceCreate(BaseModel):
    game_id: int = Field(..., ge=1, description="????ID")
    provider: Optional[str] = Field("baidu", max_length=20, description="?????baidu/quark/alipan/115")
    title: Optional[str] = Field("", max_length=255, description="????")
    origin_url: Optional[str] = Field("", max_length=1000, description="????URL")
    my_share_url: Optional[str] = Field("", max_length=1000, description="??????")
    extract_code: Optional[str] = Field("", max_length=20, description="???")
    remark: Optional[str] = Field("", max_length=2000, description="??")
    display_order: Optional[int] = Field(0, description="????")
    status: Optional[str] = Field("active", max_length=20, description="???pending/active/disabled/invalid")


class DownloadResourceUpdate(BaseModel):
    game_id: Optional[int] = Field(None, ge=1, description="????ID")
    provider: Optional[str] = Field(None, max_length=20, description="????")
    title: Optional[str] = Field(None, max_length=255, description="????")
    origin_url: Optional[str] = Field(None, max_length=1000, description="????URL")
    my_share_url: Optional[str] = Field(None, max_length=1000, description="??????")
    extract_code: Optional[str] = Field(None, max_length=20, description="???")
    remark: Optional[str] = Field(None, max_length=2000, description="??")
    display_order: Optional[int] = Field(None, description="????")
    status: Optional[str] = Field(None, max_length=20, description="??")


# ==================== Serialization ====================


def serialize_download_resource(dr: DownloadResource) -> dict:
    return {
        "id": dr.id,
        "game_id": dr.game_id,
        "game_title": dr.game.title if dr.game else "",
        "provider": dr.provider,
        "provider_label": PROVIDER_LABELS.get(dr.provider, dr.provider),
        "title": dr.title,
        "origin_url": dr.origin_url,
        "my_share_url": dr.my_share_url,
        "extract_code": dr.extract_code,
        "remark": dr.remark,
        "display_order": dr.display_order,
        "status": dr.status,
        "created_at": str(dr.created_at) if dr.created_at else None,
        "updated_at": str(dr.updated_at) if dr.updated_at else None,
    }


# ==================== CRUD endpoints ====================


@router.get(
    "/download-resources",
    summary="[??] ??????",
)
async def list_download_resources(
    game_id: Optional[int] = Query(None, ge=1, description="???ID??"),
    keyword: Optional[str] = Query(None, description="???????"),
    provider: Optional[str] = Query(None, description="???????"),
    status_filter: Optional[str] = Query(None, alias="status", description="?????"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    # Base query with eager-load game
    query = select(DownloadResource).options(joinedload(DownloadResource.game))
    count_query = select(func.count()).select_from(DownloadResource)

    if game_id:
        query = query.where(DownloadResource.game_id == game_id)
        count_query = count_query.where(DownloadResource.game_id == game_id)

    if provider:
        query = query.where(DownloadResource.provider == provider)
        count_query = count_query.where(DownloadResource.provider == provider)

    if status_filter:
        query = query.where(DownloadResource.status == status_filter)
        count_query = count_query.where(DownloadResource.status == status_filter)

    # Game name search via JOIN
    if keyword:
        query = query.join(Game).where(Game.title.contains(keyword))
        count_query = count_query.join(Game).where(Game.title.contains(keyword))

    total = (await db.execute(count_query)).scalar() or 0
    offset = (page - 1) * page_size
    query = (
        query.order_by(DownloadResource.display_order.asc())
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
    summary="[??] ??????",
)
async def get_download_resource(
    resource_id: int,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(DownloadResource)
        .options(joinedload(DownloadResource.game))
        .where(DownloadResource.id == resource_id)
    )
    resource = result.unique().scalar_one_or_none()
    if not resource:
        raise HTTPException(status_code=404, detail="???????")

    return {
        "code": 0,
        "message": "success",
        "data": serialize_download_resource(resource),
    }


@router.post(
    "/download-resources",
    summary="[??] ??????",
    status_code=201,
)
async def create_download_resource(
    body: DownloadResourceCreate,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    if body.provider and body.provider not in VALID_PROVIDERS:
        raise HTTPException(
            status_code=400,
            detail=f"???????????{', '.join(sorted(VALID_PROVIDERS))}",
        )
    if body.status and body.status not in VALID_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"?????????{', '.join(sorted(VALID_STATUSES))}",
        )

    game_result = await db.execute(select(Game).where(Game.id == body.game_id))
    if not game_result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="?????")

    resource = DownloadResource(**body.model_dump())
    db.add(resource)
    await db.flush()
    await db.refresh(resource)

    # Re-fetch with game relationship
    result = await db.execute(
        select(DownloadResource)
        .options(joinedload(DownloadResource.game))
        .where(DownloadResource.id == resource.id)
    )
    resource = result.unique().scalar_one()

    return {
        "code": 0,
        "message": "????",
        "data": serialize_download_resource(resource),
    }


@router.put(
    "/download-resources/{resource_id}",
    summary="[??] ??????",
)
async def update_download_resource(
    resource_id: int,
    body: DownloadResourceUpdate,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(DownloadResource)
        .options(joinedload(DownloadResource.game))
        .where(DownloadResource.id == resource_id)
    )
    resource = result.unique().scalar_one_or_none()
    if not resource:
        raise HTTPException(status_code=404, detail="???????")

    update_data = body.model_dump(exclude_unset=True)

    if "provider" in update_data and update_data["provider"] not in VALID_PROVIDERS:
        raise HTTPException(
            status_code=400,
            detail=f"???????????{', '.join(sorted(VALID_PROVIDERS))}",
        )
    if "status" in update_data and update_data["status"] not in VALID_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"?????????{', '.join(sorted(VALID_STATUSES))}",
        )
    if "game_id" in update_data:
        game_result = await db.execute(select(Game).where(Game.id == update_data["game_id"]))
        if not game_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="?????")

    for key, value in update_data.items():
        setattr(resource, key, value)

    await db.flush()
    await db.refresh(resource)

    return {
        "code": 0,
        "message": "????",
        "data": serialize_download_resource(resource),
    }


@router.delete(
    "/download-resources/{resource_id}",
    summary="[??] ??????",
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
        raise HTTPException(status_code=404, detail="???????")

    await db.delete(resource)
    await db.flush()

    return {"code": 0, "message": "????"}


# ==================== Games list helper ====================


@router.get(
    "/download-resources-games",
    summary="[??] ?????????????????",
)
async def list_games_for_select(
    keyword: Optional[str] = Query(None, description="?????"),
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
