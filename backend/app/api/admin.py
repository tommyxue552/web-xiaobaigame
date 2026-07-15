# -*- coding: utf-8 -*-

"""

???? API

-----------

?????????????????????????

?????? login ???? JWT ???

"""



from fastapi import APIRouter, Depends, Query, HTTPException, status

from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import select, func

from pydantic import BaseModel, Field

from typing import Optional

from datetime import date



from ..core.database import get_db

from ..core.auth import verify_password, create_access_token, get_current_admin

from ..models.game import Game

from ..models.category import Category
from ..models.tag import Tag
from ..models.game_tag import GameTag

from ..models.admin_user import AdminUser
from ..models.download_resource import DownloadResource
from ..models.download_provider import DownloadProvider
from ..models.download_log import DownloadLog



router = APIRouter(prefix="/api/admin", tags=["Admin"])





# ==================== ??/???? ====================



class LoginRequest(BaseModel):

    username: str = Field(..., min_length=1, max_length=50)

    password: str = Field(..., min_length=1, max_length=100)





class GameCreate(BaseModel):

    title: str = Field(..., min_length=1, max_length=255)

    slug: str = Field(..., min_length=1, max_length=255)

    cover: str = Field("", max_length=500)

    images: list[str] = Field(default_factory=list)

    description: str = Field("", max_length=10000)

    system: str = Field("", max_length=100)

    language: str = Field("", max_length=50)

    size: str = Field("", max_length=50)

    version: str = Field("", max_length=50)

    publisher: str = Field("", max_length=100)

    developer: str = Field("", max_length=100)

    release_date: Optional[date] = Field(None)

    category_id: Optional[int] = Field(None)

    category: str = Field("", max_length=100)

    tags: list[str] = Field(default_factory=list)
    tag_ids: Optional[list[int]] = Field(default_factory=list)

    download_url: str = Field("", max_length=500)

    original_url: str = Field("", max_length=500)

    crawler_source: str = Field("", max_length=100)

    crawler_url: str = Field("", max_length=500)

    transfer_status: str = Field("pending", max_length=50)

    seo_title: str = Field("", max_length=255)
    seo_description: str = Field("", max_length=500)
    seo_keywords: str = Field("", max_length=500)
    publish_status: str = Field("draft", max_length=20)





class GameUpdate(BaseModel):

    title: Optional[str] = Field(None, max_length=255)

    slug: Optional[str] = Field(None, max_length=255)

    cover: Optional[str] = Field(None, max_length=500)

    images: Optional[list[str]] = None

    description: Optional[str] = Field(None, max_length=10000)

    system: Optional[str] = Field(None, max_length=100)

    language: Optional[str] = Field(None, max_length=50)

    size: Optional[str] = Field(None, max_length=50)

    version: Optional[str] = Field(None, max_length=50)

    publisher: Optional[str] = Field(None, max_length=100)

    developer: Optional[str] = Field(None, max_length=100)

    release_date: Optional[date] = None

    category_id: Optional[int] = Field(None)

    category: Optional[str] = Field(None, max_length=100)

    tags: Optional[list[str]] = None
    tag_ids: Optional[list[int]] = None

    download_url: Optional[str] = Field(None, max_length=500)

    original_url: Optional[str] = Field(None, max_length=500)

    crawler_source: Optional[str] = Field(None, max_length=100)

    crawler_url: Optional[str] = Field(None, max_length=500)

    transfer_status: Optional[str] = Field(None, max_length=50)

    seo_title: Optional[str] = Field(None, max_length=255)
    seo_description: Optional[str] = Field(None, max_length=500)
    seo_keywords: Optional[str] = Field(None, max_length=500)
    publish_status: Optional[str] = Field(None, max_length=20)





class CategoryCreate(BaseModel):

    name: str = Field(..., min_length=1, max_length=100)

    slug: str = Field(..., min_length=1, max_length=100)





class CategoryUpdate(BaseModel):

    name: Optional[str] = Field(None, min_length=1, max_length=100)

    slug: Optional[str] = Field(None, min_length=1, max_length=100)





# ==================== 同步游戏标签 ====================

async def _sync_game_tags(db: AsyncSession, game_id: int, tag_ids: list[int]):
    """同步游戏标签关联"""
    # Delete old associations
    existing = (await db.execute(select(GameTag).where(GameTag.game_id == game_id))).scalars().all()
    for gt in existing:
        await db.delete(gt)
    # Create new associations
    for tid in tag_ids:
        db.add(GameTag(game_id=game_id, tag_id=tid))


# ==================== 登录 ====================



@router.post("/login", summary="管理员登录")

async def admin_login(body: LoginRequest, db: AsyncSession = Depends(get_db)):

    """管理员登录，返回 JWT Token"""

    result = await db.execute(

        select(AdminUser).where(AdminUser.username == body.username)

    )

    admin = result.scalar_one_or_none()

    if not admin or not verify_password(body.password, admin.password_hash):

        raise HTTPException(

            status_code=status.HTTP_401_UNAUTHORIZED,

            detail="用户名或密码错误",

        )

    token = create_access_token(data={"sub": str(admin.id), "username": admin.username})

    return {

        "code": 0,

        "message": "登录成功",

        "data": {"token": token, "username": admin.username},

    }





@router.get("/me", summary="?????????")

async def admin_me(admin: AdminUser = Depends(get_current_admin)):

    """?? token ??????????????"""

    return {

        "code": 0,

        "message": "success",

        "data": {"id": admin.id, "username": admin.username},

    }





# ==================== ???????????====================



@router.get("/games", summary="[??] ??????")

async def admin_list_games(

    page: int = Query(1, ge=1),

    page_size: int = Query(20, ge=1, le=100),

    keyword: str = Query("", description="搜索关键词"),

    publish_status: str = Query("", description="发布状态"),

    category: str = Query("", description="分类筛选"),

    admin: AdminUser = Depends(get_current_admin),

    db: AsyncSession = Depends(get_db),

):

    query = select(Game)

    count_query_base = select(func.count()).select_from(Game)

    if publish_status:

        query = query.where(Game.publish_status == publish_status)

        count_query_base = count_query_base.where(Game.publish_status == publish_status)

    if keyword:

        query = query.where(Game.title.contains(keyword))

        count_query_base = count_query_base.where(Game.title.contains(keyword))

    if category:

        query = query.where(Game.category == category)

        count_query_base = count_query_base.where(Game.category == category)

    total = (await db.execute(count_query_base)).scalar() or 0

    offset = (page - 1) * page_size

    query = query.order_by(Game.updated_at.desc()).offset(offset).limit(page_size)

    result = await db.execute(query)

    games = result.scalars().all()

    return {

        "code": 0, "message": "success",

        "data": {"items": [await serialize_game(g, db) for g in games], "total": total, "page": page, "page_size": page_size},

    }





@router.get("/game/{game_id}", summary="[??] ??????")

async def admin_get_game(game_id: int, admin: AdminUser = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):

    result = await db.execute(select(Game).where(Game.id == game_id))

    game = result.scalar_one_or_none()

    if not game:

        raise HTTPException(status_code=404, detail="游戏不存在")

    return {"code": 0, "message": "success", "data": await serialize_game(game, db)}





@router.post("/game", summary="[??] ????", status_code=201)

async def admin_create_game(body: GameCreate, admin: AdminUser = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):

    existing = await db.execute(select(Game).where(Game.slug == body.slug))

    if existing.scalar_one_or_none():

        raise HTTPException(status_code=400, detail="slug ???")

    data = body.model_dump()
    tag_ids = data.pop("tag_ids", [])

    game = Game(**data)

    db.add(game)
    await db.flush()

    # Sync game-tag associations
    await _sync_game_tags(db, game.id, tag_ids)

    await db.refresh(game)

    return {"code": 0, "message": "创建成功", "data": await serialize_game(game, db)}





@router.put("/game/{game_id}", summary="[??] ????")

async def admin_update_game(game_id: int, body: GameUpdate, admin: AdminUser = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):

    result = await db.execute(select(Game).where(Game.id == game_id))

    game = result.scalar_one_or_none()

    if not game:

        raise HTTPException(status_code=404, detail="游戏不存在")

    update_data = body.model_dump(exclude_unset=True)
    tag_ids = update_data.pop("tag_ids", None)

    for key, value in update_data.items():

        setattr(game, key, value)

    await db.flush()

    # Sync game-tag associations if tag_ids provided
    if tag_ids is not None:
        await _sync_game_tags(db, game.id, tag_ids)

    await db.refresh(game)

    return {"code": 0, "message": "更新成功", "data": await serialize_game(game, db)}





@router.delete("/game/{game_id}", summary="[??] ????")

async def admin_delete_game(game_id: int, admin: AdminUser = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):

    result = await db.execute(select(Game).where(Game.id == game_id))

    game = result.scalar_one_or_none()

    if not game:

        raise HTTPException(status_code=404, detail="游戏不存在")

    await db.delete(game)

    await db.flush()

    return {"code": 0, "message": "删除成功"}





# ==================== ???????????====================



@router.get("/categories", summary="[??] ??????")

async def admin_list_categories(admin: AdminUser = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):

    result = await db.execute(select(Category).order_by(Category.id))

    categories = result.scalars().all()

    items = []

    for c in categories:

        count_result = await db.execute(select(func.count()).select_from(Game).where(Game.category_id == c.id))

        game_count = count_result.scalar() or 0

        items.append({"id": c.id, "name": c.name, "slug": c.slug, "game_count": game_count})

    return {"code": 0, "message": "success", "data": items}





@router.post("/category", summary="[??] ????", status_code=201)

async def admin_create_category(body: CategoryCreate, admin: AdminUser = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):

    existing = await db.execute(select(Category).where((Category.slug == body.slug) | (Category.name == body.name)))

    if existing.scalar_one_or_none():

        raise HTTPException(status_code=400, detail="分类名或 slug 已存在")

    cat = Category(name=body.name, slug=body.slug)

    db.add(cat)

    await db.flush()

    await db.refresh(cat)

    return {"code": 0, "message": "创建成功", "data": {"id": cat.id, "name": cat.name, "slug": cat.slug, "game_count": 0}}





@router.put("/category/{cat_id}", summary="[??] ????")

async def admin_update_category(cat_id: int, body: CategoryUpdate, admin: AdminUser = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):

    result = await db.execute(select(Category).where(Category.id == cat_id))

    cat = result.scalar_one_or_none()

    if not cat:

        raise HTTPException(status_code=404, detail="分类不存在")

    update_data = body.model_dump(exclude_unset=True)

    for key, value in update_data.items():

        setattr(cat, key, value)

    await db.flush()

    await db.refresh(cat)

    return {"code": 0, "message": "更新成功", "data": {"id": cat.id, "name": cat.name, "slug": cat.slug}}





@router.delete("/category/{cat_id}", summary="[??] ????")

async def admin_delete_category(cat_id: int, admin: AdminUser = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):

    result = await db.execute(select(Category).where(Category.id == cat_id))

    cat = result.scalar_one_or_none()

    if not cat:

        raise HTTPException(status_code=404, detail="分类不存在")

    await db.delete(cat)

    await db.flush()

    return {"code": 0, "message": "删除成功"}





# ==================== ????? ====================



@router.get("/stats", summary="[Admin] Dashboard Stats")
async def admin_stats(admin: AdminUser = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    total = (await db.execute(select(func.count()).select_from(Game))).scalar() or 0
    published = (await db.execute(select(func.count()).select_from(Game).where(Game.publish_status == "published"))).scalar() or 0
    draft = (await db.execute(select(func.count()).select_from(Game).where(Game.publish_status == "draft"))).scalar() or 0
    cat_count = (await db.execute(select(func.count()).select_from(Category))).scalar() or 0
    tag_count = (await db.execute(select(func.count()).select_from(Tag))).scalar() or 0
    resource_count = (await db.execute(select(func.count()).select_from(DownloadResource))).scalar() or 0
    provider_count = (await db.execute(select(func.count()).select_from(DownloadProvider))).scalar() or 0
    download_count = (await db.execute(select(func.count()).select_from(DownloadLog))).scalar() or 0
    total_views = (await db.execute(select(func.sum(Game.views)).select_from(Game))).scalar() or 0
    recent_result = await db.execute(select(Game).order_by(Game.created_at.desc()).limit(8))
    recent_games = recent_result.scalars().all()
    return {
        "code": 0, "message": "success",
        "data": {
            "total_games": total, "published_games": published, "draft_games": draft,
            "category_count": cat_count, "tag_count": tag_count,
            "resource_count": resource_count, "provider_count": provider_count,
            "download_count": download_count, "total_views": total_views,
            "recent_games": [{"id": g.id, "title": g.title, "cover": g.cover, "category": g.category,
                               "publish_status": g.publish_status, "created_at": str(g.created_at)} for g in recent_games],
        },
    }



# ==================== 登录 ====================



async def serialize_game(g: Game, db: AsyncSession = None) -> dict:
    tag_ids = []
    if db is not None:
        result = await db.execute(select(GameTag.tag_id).where(GameTag.game_id == g.id))
        tag_ids = [row[0] for row in result.all()]

    return {
        "id": g.id, "title": g.title, "slug": g.slug,
        "cover": g.cover, "images": g.images, "description": g.description,
        "system": g.system, "language": g.language, "size": g.size,
        "version": g.version, "publisher": g.publisher, "developer": g.developer,
        "release_date": str(g.release_date) if g.release_date else None,
        "category_id": g.category_id, "category": g.category, "tags": g.tags,
        "tag_ids": tag_ids,
        "download_url": g.download_url, "original_url": g.original_url,
        "crawler_source": g.crawler_source, "crawler_url": g.crawler_url,
        "transfer_status": g.transfer_status,
        "transfer_time": str(g.transfer_time) if g.transfer_time else None,
        "publish_status": g.publish_status,
        "created_at": str(g.created_at), "updated_at": str(g.updated_at),
    }

