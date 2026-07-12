"""
游戏公开 API
-----------
提供游戏列表查询、详情获取、分类列表、二维码生成、下载跳转。
"""

import json
import io
from fastapi import APIRouter, Depends, Query, HTTPException, Request
from fastapi.responses import RedirectResponse, StreamingResponse, HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from ..core.database import get_db
from ..models.game import Game
from ..models.category import Category
import qrcode

router = APIRouter(tags=['Games'])

MOBILE_UA_REGEX = r'Android|iPhone|iPad|iPod|webOS|BlackBerry|Windows Phone'
MOBILE_UA_STR = 'Android|iPhone|iPad|iPod|webOS|BlackBerry|Windows Phone'


@router.get('/api/categories', summary='获取分类列表')
async def list_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Category).order_by(Category.id))
    categories = result.scalars().all()
    return {
        'code': 0,
        'message': 'success',
        'data': [
            {'id': c.id, 'name': c.name, 'slug': c.slug}
            for c in categories
        ],
    }


@router.get('/api/games', summary='获取游戏列表')
async def list_games(
    page: int = Query(1, ge=1, description='页码'),
    page_size: int = Query(20, ge=1, le=100, description='每页数量'),
    category: str = Query('', description='按分类筛选（分类名称）'),
    keyword: str = Query('', description='按关键词搜索标题'),
    sort: str = Query('latest', description='排序方式：latest/hot'),
    db: AsyncSession = Depends(get_db),
):
    query = select(Game).where(Game.publish_status == 'published')

    if category:
        query = query.where(Game.category == category)
    if keyword:
        query = query.where(Game.title.contains(keyword))

    if sort == 'hot':
        query = query.order_by(Game.id.desc())
    else:
        query = query.order_by(Game.created_at.desc())

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()

    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    result = await db.execute(query)
    games = result.scalars().all()

    return {
        'code': 0,
        'message': 'success',
        'data': {
            'games': [
                {
                    'id': g.id,
                    'title': g.title,
                    'slug': g.slug,
                    'cover': g.cover,
                    'category': g.category,
                    'category_name': g.category_rel.name if g.category_rel else g.category,
                    'tags': g.tags,
                    'system': g.system,
                    'language': g.language,
                    'size': g.size,
                    'version': g.version,
                    'publisher': g.publisher,
                    'developer': g.developer,
                    'release_date': str(g.release_date) if g.release_date else None,
                    'created_at': str(g.created_at),
                }
                for g in games
            ],
            'total': total,
            'page': page,
            'size': page_size,
        },
    }


@router.get('/api/game/{game_id}', summary='获取游戏详情')
async def get_game(
    game_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Game).where(
            Game.id == game_id,
            Game.publish_status == 'published',
        )
    )
    game = result.scalar_one_or_none()

    if not game:
        raise HTTPException(status_code=404, detail='游戏不存在或未发布')

    return {
        'code': 0,
        'message': 'success',
        'data': {
            'id': game.id,
            'title': game.title,
            'slug': game.slug,
            'cover': game.cover,
            'images': game.images,
            'description': game.description,
            'system': game.system,
            'language': game.language,
            'size': game.size,
            'version': game.version,
            'publisher': game.publisher,
            'developer': game.developer,
            'release_date': str(game.release_date) if game.release_date else None,
            'category': game.category,
            'category_name': game.category_rel.name if game.category_rel else game.category,
            'tags': game.tags,
            'download_url': game.download_url,
            'original_url': game.original_url,
            'crawler_source': game.crawler_source,
            'transfer_status': game.transfer_status,
            'created_at': str(game.created_at),
            'updated_at': str(game.updated_at),
        },
    }


# ==================== 二维码接口 ====================

@router.get('/api/qrcode/{game_id}', summary='生成游戏下载二维码')
async def get_qrcode(
    game_id: int,
    db: AsyncSession = Depends(get_db),
):
    """动态生成下载二维码图片（PNG），内容为游戏的 download_url"""
    result = await db.execute(
        select(Game).where(
            Game.id == game_id,
            Game.publish_status == 'published',
        )
    )
    game = result.scalar_one_or_none()

    if not game:
        raise HTTPException(status_code=404, detail='游戏不存在或未发布')

    download_url = game.download_url
    if not download_url:
        raise HTTPException(status_code=404, detail='该游戏暂无下载链接')

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(download_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color='black', back_color='white')
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)

    return StreamingResponse(buf, media_type='image/png')


# ==================== 页面路由 ====================

@router.get('/game/{game_id}', summary='游戏详情页')
async def game_page(game_id: int):
    """跳转到前端游戏详情页"""
    return RedirectResponse(f'/frontend/game.html?id={game_id}')


@router.get('/download/{game_id}', summary='游戏下载页')
async def download_page(
    game_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    下载页面：根据 User-Agent 判断设备类型。
    手机端 → 302 跳转到 download_url
    PC 端 → 展示二维码页面
    """
    import re
    user_agent = request.headers.get('user-agent', '')
    is_mobile = bool(re.search(MOBILE_UA_REGEX, user_agent, re.IGNORECASE))

    result = await db.execute(
        select(Game).where(
            Game.id == game_id,
            Game.publish_status == 'published',
        )
    )
    game = result.scalar_one_or_none()

    if not game:
        raise HTTPException(status_code=404, detail='游戏不存在或未发布')

    if not game.download_url:
        raise HTTPException(status_code=404, detail='该游戏暂无下载链接')

    if is_mobile:
        return RedirectResponse(game.download_url, status_code=302)

    # PC 端：返回二维码下载页面
    html = _render_download_page(game_id, game.title, game.download_url)
    return HTMLResponse(content=html)


def _render_download_page(game_id: int, title: str, download_url: str) -> str:
    """渲染 PC 端二维码下载页面 HTML"""
    safe_title = title.replace("'", "\\'").replace('"', '\\"')
    return '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>扫码下载 - 小白游戏资源站</title>
    <style>
        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC",
                         "Microsoft YaHei", sans-serif;
            background: #14141e;
            color: #fff;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-align: center;
            padding: 40px 20px;
        }
        .header {
            margin-bottom: 30px;
        }
        .header .logo {
            font-size: 1.4rem;
            font-weight: 700;
            color: #fff;
            text-decoration: none;
        }
        .header .logo span { color: #e94560; }
        .qr-container {
            background: #1e1e32;
            border: 1px solid #2a2a3e;
            border-radius: 12px;
            padding: 40px;
            max-width: 420px;
            width: 100%;
        }
        .qr-title {
            font-size: 1.2rem;
            font-weight: 700;
            margin-bottom: 4px;
        }
        .qr-game-name {
            color: #e94560;
            font-size: 0.95rem;
            margin-bottom: 24px;
        }
        .qr-code {
            display: flex;
            justify-content: center;
            margin-bottom: 20px;
        }
        .qr-code img {
            width: 220px;
            height: 220px;
            border-radius: 8px;
            background: #fff;
            padding: 8px;
        }
        .qr-tip {
            color: #999;
            font-size: 0.9rem;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }
        .qr-tip svg { flex-shrink: 0; }
        .qr-url {
            margin-top: 16px;
            color: #666;
            font-size: 0.75rem;
            word-break: break-all;
            max-width: 100%;
        }
        .back-link {
            margin-top: 24px;
            color: #777;
            font-size: 0.85rem;
            text-decoration: none;
            transition: color 0.2s;
        }
        .back-link:hover { color: #e94560; }
    </style>
</head>
<body>
    <div class="header">
        <a href="/" class="logo">小白<span>游戏</span></a>
    </div>
    <div class="qr-container">
        <h1 class="qr-title">扫码下载</h1>
        <p class="qr-game-name">''' + _html_esc(title) + '''</p>
        <div class="qr-code">
            <img src="/api/qrcode/''' + str(game_id) + '''" alt="下载二维码">
        </div>
        <p class="qr-tip">
            <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="5" y="2" width="14" height="20" rx="2" ry="2"/>
                <line x1="12" y1="18" x2="12.01" y2="18"/>
            </svg>
            请使用手机扫码下载
        </p>
        <p class="qr-url">''' + _html_esc(download_url) + '''</p>
    </div>
    <a href="/game/''' + str(game_id) + '''" class="back-link">&larr; 返回游戏详情</a>
</body>
</html>'''


def _html_esc(s: str) -> str:
    """HTML 实体转义"""
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')
