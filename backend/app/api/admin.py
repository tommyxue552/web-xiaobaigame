"""
后台管理 API
-----------
提供游戏资源的增删改查管理接口。
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel, Field
from typing import Optional
from datetime import date

from ..core.database import get_db
from ..models.game import Game

router = APIRouter(prefix="/api/admin", tags=["Admin"])


# ==================== 请求/响应模型 ====================

class GameCreate(BaseModel):
    """创建游戏请求体"""
    title: str = Field(..., min_length=1, max_length=255, description="游戏标题")
    slug: str = Field(..., min_length=1, max_length=255, description="URL 标识")
    cover: str = Field("", max_length=500, description="封面图 URL")
    images: list[str] = Field(default_factory=list, description="截图列表")
    description: str = Field("", max_length=10000, description="游戏描述")
    system: str = Field("", max_length=100, description="运行平台")
    language: str = Field("", max_length=50, description="语言")
    size: str = Field("", max_length=50, description="文件大小")
    version: str = Field("", max_length=50, description="版本号")
    publisher: str = Field("", max_length=100, description="发行商")
    developer: str = Field("", max_length=100, description="开发商")
    release_date: Optional[date] = Field(None, description="发布日期")
    category: str = Field("", max_length=100, description="分类")
    tags: list[str] = Field(default_factory=list, description="标签")
    download_url: str = Field("", max_length=500, description="下载链接")
    original_url: str = Field("", max_length=500, description="原始来源")
    crawler_source: str = Field("", max_length=100, description="采集来源")
    crawler_url: str = Field("", max_length=500, description="采集页面")
    transfer_status: str = Field("pending", max_length=50, description="中转状态")
    publish_status: str = Field("draft", max_length=20, description="发布状态")


class GameUpdate(BaseModel):
    """更新游戏请求体（所有字段可选）"""
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
    category: Optional[str] = Field(None, max_length=100)
    tags: Optional[list[str]] = None
    download_url: Optional[str] = Field(None, max_length=500)
    original_url: Optional[str] = Field(None, max_length=500)
    crawler_source: Optional[str] = Field(None, max_length=100)
    crawler_url: Optional[str] = Field(None, max_length=500)
    transfer_status: Optional[str] = Field(None, max_length=50)
    publish_status: Optional[str] = Field(None, max_length=20)


# ==================== API 端点 ====================

@router.get("/games", summary="[管理] 获取游戏列表")
async def admin_list_games(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    publish_status: str = Query("", description="按状态筛选：draft/published/hidden"),
    db: AsyncSession = Depends(get_db),
):
    """管理端游戏列表，可查看所有状态的游戏"""
    query = select(Game)

    if publish_status:
        query = query.where(Game.publish_status == publish_status)

    # 总数
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()

    # 分页
    offset = (page - 1) * page_size
    query = query.order_by(Game.created_at.desc()).offset(offset).limit(page_size)
    result = await db.execute(query)
    games = result.scalars().all()

    return {
        "code": 0,
        "message": "success",
        "data": {
            "items": [serialize_game(g) for g in games],
            "total": total,
            "page": page,
            "page_size": page_size,
        },
    }


@router.get("/game/{game_id}", summary="[管理] 获取游戏详情")
async def admin_get_game(game_id: int, db: AsyncSession = Depends(get_db)):
    """管理端获取任意状态的游戏详情"""
    result = await db.execute(select(Game).where(Game.id == game_id))
    game = result.scalar_one_or_none()
    if not game:
        raise HTTPException(status_code=404, detail="游戏不存在")
    return {"code": 0, "message": "success", "data": serialize_game(game)}


@router.post("/game", summary="[管理] 创建游戏", status_code=201)
async def admin_create_game(body: GameCreate, db: AsyncSession = Depends(get_db)):
    """创建新游戏记录"""
    # 检查 slug 唯一性
    existing = await db.execute(select(Game).where(Game.slug == body.slug))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="slug 已存在")

    game = Game(**body.model_dump())
    db.add(game)
    await db.flush()
    await db.refresh(game)

    return {"code": 0, "message": "创建成功", "data": serialize_game(game)}


@router.put("/game/{game_id}", summary="[管理] 更新游戏")
async def admin_update_game(
    game_id: int, body: GameUpdate, db: AsyncSession = Depends(get_db)
):
    """更新游戏信息"""
    result = await db.execute(select(Game).where(Game.id == game_id))
    game = result.scalar_one_or_none()
    if not game:
        raise HTTPException(status_code=404, detail="游戏不存在")

    # 仅更新传入的非 None 字段
    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(game, key, value)

    await db.flush()
    await db.refresh(game)

    return {"code": 0, "message": "更新成功", "data": serialize_game(game)}


@router.delete("/game/{game_id}", summary="[管理] 删除游戏")
async def admin_delete_game(game_id: int, db: AsyncSession = Depends(get_db)):
    """删除游戏记录"""
    result = await db.execute(select(Game).where(Game.id == game_id))
    game = result.scalar_one_or_none()
    if not game:
        raise HTTPException(status_code=404, detail="游戏不存在")

    await db.delete(game)
    await db.flush()

    return {"code": 0, "message": "删除成功"}


# ==================== 辅助函数 ====================

def serialize_game(g: Game) -> dict:
    """将 Game ORM 对象序列化为字典"""
    return {
        "id": g.id,
        "title": g.title,
        "slug": g.slug,
        "cover": g.cover,
        "images": g.images,
        "description": g.description,
        "system": g.system,
        "language": g.language,
        "size": g.size,
        "version": g.version,
        "publisher": g.publisher,
        "developer": g.developer,
        "release_date": str(g.release_date) if g.release_date else None,
        "category": g.category,
        "tags": g.tags,
        "download_url": g.download_url,
        "original_url": g.original_url,
        "crawler_source": g.crawler_source,
        "crawler_url": g.crawler_url,
        "transfer_status": g.transfer_status,
        "transfer_time": str(g.transfer_time) if g.transfer_time else None,
        "publish_status": g.publish_status,
        "created_at": str(g.created_at),
        "updated_at": str(g.updated_at),
    }
