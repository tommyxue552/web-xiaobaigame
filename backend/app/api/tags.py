# -*- coding: utf-8 -*-
"""
标签管理 API
-----------
后台标签 CRUD，支持 SEO 字段编辑、排序、启用/禁用。
"""

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel, Field
from typing import Optional

from ..core.database import get_db
from ..core.auth import get_current_admin
from ..models.admin_user import AdminUser
from ..models.tag import Tag
from ..models.game_tag import GameTag

router = APIRouter(prefix="/api/admin", tags=["Admin - Tags"])


# ==================== Schemas ====================

class TagCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    slug: str = Field(..., min_length=1, max_length=100)
    description: str = Field("", max_length=5000)
    seo_title: str = Field("", max_length=255)
    seo_description: str = Field("", max_length=500)
    seo_keywords: str = Field("", max_length=500)
    sort_order: int = Field(0)
    is_active: bool = Field(True)


class TagUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    slug: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=5000)
    seo_title: Optional[str] = Field(None, max_length=255)
    seo_description: Optional[str] = Field(None, max_length=500)
    seo_keywords: Optional[str] = Field(None, max_length=500)
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


# ==================== Helpers ====================

async def _get_tag_game_count(db: AsyncSession, tag_id: int) -> int:
    result = await db.execute(
        select(func.count()).select_from(GameTag).where(GameTag.tag_id == tag_id)
    )
    return result.scalar() or 0


def _serialize_tag(tag: Tag, game_count: int = 0) -> dict:
    return {
        "id": tag.id,
        "name": tag.name,
        "slug": tag.slug,
        "description": tag.description or "",
        "seo_title": tag.seo_title or "",
        "seo_description": tag.seo_description or "",
        "seo_keywords": tag.seo_keywords or "",
        "sort_order": tag.sort_order,
        "is_active": tag.is_active,
        "game_count": game_count,
        "created_at": str(tag.created_at) if tag.created_at else "",
        "updated_at": str(tag.updated_at) if tag.updated_at else "",
    }


# ==================== CRUD ====================

@router.get("/tags", summary="[后台] 标签列表")
async def admin_list_tags(
    keyword: str = Query("", description="名称搜索"),
    is_active: Optional[bool] = Query(None, description="启用状态筛选"),
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    query = select(Tag)
    if keyword:
        query = query.where(Tag.name.contains(keyword))
    if is_active is not None:
        query = query.where(Tag.is_active == is_active)
    query = query.order_by(Tag.sort_order.asc(), Tag.id.asc())
    result = await db.execute(query)
    tags = result.scalars().all()

    items = []
    for tag in tags:
        gc = await _get_tag_game_count(db, tag.id)
        items.append(_serialize_tag(tag, gc))

    return {"code": 0, "message": "success", "data": items}


@router.get("/tags/active", summary="[后台] 启用标签列表（下拉选择用）")
async def admin_list_active_tags(
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Tag).where(Tag.is_active == True).order_by(Tag.sort_order.asc(), Tag.id.asc())
    )
    tags = result.scalars().all()
    return {
        "code": 0,
        "message": "success",
        "data": [{"id": t.id, "name": t.name, "slug": t.slug} for t in tags],
    }


@router.get("/tags/{tag_id}", summary="[后台] 标签详情")
async def admin_get_tag(
    tag_id: int,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Tag).where(Tag.id == tag_id))
    tag = result.scalar_one_or_none()
    if not tag:
        raise HTTPException(status_code=404, detail="标签不存在")
    gc = await _get_tag_game_count(db, tag.id)
    return {"code": 0, "message": "success", "data": _serialize_tag(tag, gc)}


@router.post("/tags", summary="[后台] 新增标签", status_code=201)
async def admin_create_tag(
    body: TagCreate,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(
        select(Tag).where((Tag.slug == body.slug) | (Tag.name == body.name))
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="标签名称或slug已存在")
    tag = Tag(**body.model_dump())
    db.add(tag)
    await db.flush()
    await db.refresh(tag)
    return {"code": 0, "message": "创建成功", "data": _serialize_tag(tag, 0)}


@router.put("/tags/{tag_id}", summary="[后台] 更新标签")
async def admin_update_tag(
    tag_id: int,
    body: TagUpdate,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Tag).where(Tag.id == tag_id))
    tag = result.scalar_one_or_none()
    if not tag:
        raise HTTPException(status_code=404, detail="标签不存在")
    update_data = body.model_dump(exclude_unset=True)
    # Check slug uniqueness if changed
    if "slug" in update_data and update_data["slug"] != tag.slug:
        dup = await db.execute(select(Tag).where(Tag.slug == update_data["slug"]))
        if dup.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="slug已被占用")
    for key, value in update_data.items():
        setattr(tag, key, value)
    await db.flush()
    await db.refresh(tag)
    gc = await _get_tag_game_count(db, tag.id)
    return {"code": 0, "message": "更新成功", "data": _serialize_tag(tag, gc)}


@router.delete("/tags/{tag_id}", summary="[后台] 删除标签")
async def admin_delete_tag(
    tag_id: int,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Tag).where(Tag.id == tag_id))
    tag = result.scalar_one_or_none()
    if not tag:
        raise HTTPException(status_code=404, detail="标签不存在")
    await db.delete(tag)
    await db.flush()
    return {"code": 0, "message": "删除成功"}


# ==================== Game-Tag Association ====================

@router.get("/game/{game_id}/tags", summary="[后台] 获取游戏的标签ID列表")
async def admin_get_game_tags(
    game_id: int,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(GameTag).where(GameTag.game_id == game_id)
    )
    game_tags = result.scalars().all()
    return {
        "code": 0,
        "message": "success",
        "data": [gt.tag_id for gt in game_tags],
    }


@router.put("/game/{game_id}/tags", summary="[后台] 更新游戏的标签关联")
async def admin_update_game_tags(
    game_id: int,
    tag_ids: list[int],
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    # Remove old associations
    await db.execute(select(GameTag).where(GameTag.game_id == game_id))
    existing = (await db.execute(select(GameTag).where(GameTag.game_id == game_id))).scalars().all()
    for gt in existing:
        await db.delete(gt)

    # Add new associations
    for tid in tag_ids:
        # Verify tag exists
        tag_result = await db.execute(select(Tag).where(Tag.id == tid))
        if tag_result.scalar_one_or_none():
            db.add(GameTag(game_id=game_id, tag_id=tid))

    await db.flush()
    return {"code": 0, "message": "更新成功", "data": tag_ids}
