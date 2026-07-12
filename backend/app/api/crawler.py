"""
????????
--------------

??????? xiaobai-game-collector ????????

?????
- ??? Collector-Key?? settings.COLLECTOR_KEY ??

?????
- ? original_url ????????????

????
    xiaobai-game-collector
        |
        v
    POST /api/crawler/import
        |
        v
    API Key ?? -> ???? -> ?? -> ?? games ?
"""

import re
import hashlib
import time
from typing import List, Optional

from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..core.database import get_db, async_session_factory
from ..core.config import settings
from ..models.game import Game

router = APIRouter(prefix="/api/crawler", tags=["Crawler"])


# ==================== ???? ====================


class GameImportItem(BaseModel):
    """??????????????"""
    title: str = Field(default="", max_length=255, description="????")
    cover: str = Field(default="", max_length=500, description="???? URL")
    description: str = Field(default="", description="????/??")
    category: str = Field(default="", max_length=100, description="????")
    size: str = Field(default="", max_length=50, description="?????? 1.2GB?")
    download_url: str = Field(default="", max_length=500, description="????")
    original_url: str = Field(default="", max_length=500, description="?????? URL??????")
    source: str = Field(default="", max_length=100, description="??????")


class ImportRequest(BaseModel):
    """????????"""
    games: List[GameImportItem] = Field(..., min_length=1, description="??????")
    source: str = Field(default="xiaobai-game-collector", max_length=100, description="????")


class ImportResult(BaseModel):
    """?????"""
    success: bool
    message: str
    imported: int = 0
    skipped: int = 0


# ==================== ???? ====================


def _generate_slug(title: str) -> str:
    """
    ?????? URL ??? slug?

    ???
    1. ????????? + ??? hash ????
    2. ??????????????????

    Args:
        title: ????

    Returns:
        ?? slug ???
    """
    # ??????????
    cleaned = re.sub(r"[^\w一-鿿]+", "-", title).strip("-").lower()
    if not cleaned:
        cleaned = "game"

    # ??? hash ?????
    unique_suffix = hashlib.md5(
        f"{title}{time.time()}".encode()
    ).hexdigest()[:6]

    # ????
    if len(cleaned) > 100:
        cleaned = cleaned[:100]
    cleaned = cleaned.strip("-")

    return f"{cleaned}-{unique_suffix}"


def _validate_collector_key(collector_key: Optional[str]) -> bool:
    """
    ????? API Key?

    Args:
        collector_key: ????? Collector-Key ?

    Returns:
        True ??????
    """
    expected = settings.COLLECTOR_KEY
    if not expected:
        # ????? Key???????????
        return True
    return collector_key == expected


# ==================== API ?? ====================


@router.post(
    "/import",
    response_model=ImportResult,
    summary="????????",
    description="??????????????????????? original_url ???",
)
async def crawler_import(
    body: ImportRequest,
    collector_key: Optional[str] = Header(None, alias="Collector-Key"),
):
    """
    ?????????

    ???:
        Collector-Key: ????? Key????

    ???:
        {
            "games": [
                {
                    "title": "????",
                    "cover": "??URL",
                    "description": "??",
                    "category": "??",
                    "size": "1.2GB",
                    "download_url": "????",
                    "original_url": "??URL",
                    "source": "????"
                }
            ],
            "source": "xiaobai-game-collector"
        }

    ??:
        ??: {"success": true, "message": "import success", "imported": 5, "skipped": 2}
        ??: {"success": false, "message": "????", "imported": 0, "skipped": 0}
    """

    # ---- ????API Key ?? ----
    if not _validate_collector_key(collector_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Collector-Key ??????",
        )

    # ---- ???????? ----
    if not body.games:
        return ImportResult(
            success=True,
            message="no games to import",
            imported=0,
            skipped=0,
        )

    # ??? title ???????
    valid_games = [g for g in body.games if g.title and g.title.strip()]
    skipped_validation = len(body.games) - len(valid_games)

    if not valid_games:
        return ImportResult(
            success=True,
            message=f"all {len(body.games)} games have empty title, skipped",
            imported=0,
            skipped=len(body.games),
        )

    # ---- ????????? ----
    imported_count = 0
    skipped_count = skipped_validation

    async with async_session_factory() as session:
        for game_data in valid_games:
            # ---- ???? original_url ?? ----
            if game_data.original_url and game_data.original_url.strip():
                result = await session.execute(
                    select(Game).where(
                        Game.original_url == game_data.original_url.strip()
                    )
                )
                existing = result.scalar_one_or_none()
                if existing:
                    skipped_count += 1
                    continue

            # ---- ?? slug ----
            slug = _generate_slug(game_data.title)

            # ?? slug ?????????????
            retry = 0
            while retry < 3:
                check = await session.execute(
                    select(Game).where(Game.slug == slug)
                )
                if check.scalar_one_or_none() is None:
                    break
                slug = _generate_slug(game_data.title)
                retry += 1

            # ---- ?? Game ?? ----
            game = Game(
                title=game_data.title.strip(),
                slug=slug,
                cover=game_data.cover or "",
                description=game_data.description or "",
                category=game_data.category or "",
                size=game_data.size or "",
                download_url=game_data.download_url or "",
                original_url=game_data.original_url or "",
                crawler_source=game_data.source or body.source or "xiaobai-game-collector",
                crawler_url=game_data.original_url or "",
                publish_status="draft",  # ???????????
            )

            session.add(game)
            imported_count += 1

        await session.commit()

    # ---- ???????? ----
    return ImportResult(
        success=True,
        message=f"import success",
        imported=imported_count,
        skipped=skipped_count,
    )


@router.get(
    "/health",
    summary="????????",
    description="????????????",
)
async def crawler_health():
    """???????"""
    return {
        "success": True,
        "message": "crawler api is running",
        "version": settings.APP_VERSION,
    }
