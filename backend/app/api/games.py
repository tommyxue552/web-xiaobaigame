"""
游戏公开 API
-----------
提供游戏列表查询和详情获取。
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from ..core.database import get_db
from ..models.game import Game

router = APIRouter(tags=["Games"])


@router.get("/api/games", summary="获取游戏列表")
async def list_games(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    category: str = Query("", description="按分类筛选"),
    keyword: str = Query("", description="按关键词搜索标题"),
    db: AsyncSession = Depends(get_db),
):
    """
    分页查询已发布的游戏列表。

    支持按分类筛选和关键词搜索。
    仅返回 publish_status='published' 的记录。
    """
    # 构建基础查询
    query = select(Game).where(Game.publish_status == "published")

    if category:
        query = query.where(Game.category == category)
    if keyword:
        query = query.where(Game.title.contains(keyword))

    # 计算总数
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
            "items": [
                {
                    "id": g.id,
                    "title": g.title,
                    "slug": g.slug,
                    "cover": g.cover,
                    "category": g.category,
                    "tags": g.tags,
                    "system": g.system,
                    "language": g.language,
                    "size": g.size,
                    "version": g.version,
                    "publisher": g.publisher,
                    "developer": g.developer,
                    "release_date": str(g.release_date) if g.release_date else None,
                    "created_at": str(g.created_at),
                }
                for g in games
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
        },
    }


@router.get("/api/game/{game_id}", summary="获取游戏详情")
async def get_game(
    game_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    根据 ID 获取单个游戏的完整信息。
    仅返回已发布的记录。
    """
    result = await db.execute(
        select(Game).where(
            Game.id == game_id,
            Game.publish_status == "published",
        )
    )
    game = result.scalar_one_or_none()

    if not game:
        raise HTTPException(status_code=404, detail="游戏不存在或未发布")

    return {
        "code": 0,
        "message": "success",
        "data": {
            "id": game.id,
            "title": game.title,
            "slug": game.slug,
            "cover": game.cover,
            "images": game.images,
            "description": game.description,
            "system": game.system,
            "language": game.language,
            "size": game.size,
            "version": game.version,
            "publisher": game.publisher,
            "developer": game.developer,
            "release_date": str(game.release_date) if game.release_date else None,
            "category": game.category,
            "tags": game.tags,
            "download_url": game.download_url,
            "original_url": game.original_url,
            "crawler_source": game.crawler_source,
            "transfer_status": game.transfer_status,
            "created_at": str(game.created_at),
            "updated_at": str(game.updated_at),
        },
    }
