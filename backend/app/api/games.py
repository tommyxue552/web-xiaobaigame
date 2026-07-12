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
from sqlalchemy import select, func, update
from ..core.database import get_db
from ..models.game import Game
from ..models.category import Category
from ..models.download_resource import DownloadResource
from ..models.download_provider import DownloadProvider
import qrcode

router = APIRouter(tags=['Games'])

MOBILE_UA_REGEX = r'Android|iPhone|iPad|iPod|webOS|BlackBerry|Windows Phone'

SITE_NAME = '小白游戏资源站'
SITE_URL = 'http://localhost:8000'



# ==================== SEO 辅助函数 ====================

def _build_game_meta(game) -> dict:
    """构建游戏的 SEO 元数据（自定义字段优先，否则自动生成）"""
    title = game.seo_title or f"{game.title} - {SITE_NAME}"
    desc = game.seo_description or (game.description[:160] if game.description else f'{game.title} 是一款精彩的游戏，快来下载体验吧！')
    keywords = game.seo_keywords or f'{game.title},游戏下载,单机游戏,免费游戏'
    if game.category and not game.seo_keywords:
        keywords += f',{game.category}'
    return {
        'title': title,
        'description': desc,
        'keywords': keywords,
        'image': game.cover or '',
    }


def _html_esc(s: str) -> str:
    """HTML 实体转义"""
    if s is None:
        return ''
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')


def _render_game_detail_html(game, meta, game_dict):
    """Render full SEO-optimized game detail page HTML."""
    t = html_esc(meta["title"])
    d = html_esc(meta["description"])
    kw = html_esc(meta["keywords"])
    img = meta["image"]
    slug = game_dict.get("slug", "")
    cover = html_esc(game_dict.get("cover", "") or "")
    cat = html_esc(game_dict.get("category_name", "") or game_dict.get("category", "") or "")
    sys_v = html_esc(game_dict.get("system", "") or "")
    lang = html_esc(game_dict.get("language", "") or "")
    sz = html_esc(game_dict.get("size", "") or "")
    ver = html_esc(game_dict.get("version", "") or "")
    pub = html_esc(game_dict.get("publisher", "") or "")
    dev = html_esc(game_dict.get("developer", "") or "")
    rel_d = str(game_dict.get("release_date", "") or "")
    desc = html_esc(game_dict.get("description", "") or "")
    tags = game_dict.get("tags", []) or []
    imgs = game_dict.get("images", []) or []
    canon = SITE_URL + "/game/" + slug
    gjson = json.dumps(game_dict, ensure_ascii=False, default=str)
    gt = game_dict["title"]
    gte = html_esc(gt)

    jld = {
        "@context": "https://schema.org",
        "@type": "SoftwareApplication",
        "name": gt,
        "description": meta["description"],
        "applicationCategory": "GameApplication",
        "operatingSystem": sys_v or "Windows",
    }
    if img:
        jld["image"] = img
    jld_s = json.dumps(jld, ensure_ascii=False)

    th = ""
    if isinstance(tags, list) and tags:
        th = "".join("<span>" + html_esc(str(x)) + "</span>" for x in tags)

    mf = [
        ("游戏分类", cat),
        ("游戏大小", sz),
        ("版本", ver),
        ("语言", lang),
        ("运行平台", sys_v),
        ("开发商", dev),
        ("发行商", pub),
        ("发行日期", rel_d),
    ]
    mg = ""
    for lab, val in mf:
        v = val or "-"
        mg += '<div class="meta-item"><span class="meta-label">' + html_esc(lab) + '</span><span class="meta-value">' + html_esc(v) + '</span></div>'

    ss = ""
    if isinstance(imgs, list) and imgs:
        items = ""
        for idx, url in enumerate(imgs):
            items += '<div class="screenshot-thumb" data-idx="' + str(idx) + '"><img src="' + html_esc(url) + '" alt="' + gte + ' 截图 ' + str(idx + 1) + '" loading="lazy" onerror="this.parentElement.style.display=\'none\'"></div>'
        ss = '<section class="detail-section" id="detail-screenshots-section"><h2 class="detail-section-title">游戏截图</h2><div class="screenshots-gallery" id="screenshots-gallery">' + items + '</div><div class="screenshot-lightbox" id="screenshot-lightbox"><button class="lightbox-close">&times;</button><img id="lightbox-img" src="" alt=""><button class="lightbox-prev">&lsaquo;</button><button class="lightbox-next">&rsaquo;</button></div></section>'

    cov = ""
    if cover:
        cov = '<img id="detail-cover" class="detail-cover" src="' + cover + '" alt="' + gte + '" onerror="this.style.display=\'none\'">'

    og_img = '<meta property="og:image" content="' + html_esc(img) + '">' if img else ""
    tw_img = '<meta name="twitter:image" content="' + html_esc(img) + '">' if img else ""

    return """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>""" + t + """</title>
    <meta name="description" content="""" + d + """">
    <meta name="keywords" content="""" + kw + """">
    <meta property="og:title" content="""" + t + """">
    <meta property="og:description" content="""" + d + """">
    <meta property="og:type" content="website">
    <meta property="og:url" content="""" + canon + """">
    <meta property="og:site_name" content="""" + SITE_NAME + """">
    <meta property="og:locale" content="zh_CN">
    """ + og_img + """
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="""" + t + """">
    <meta name="twitter:description" content="""" + d + """">
    """ + tw_img + """
    <link rel="canonical" href="""" + canon + """">
    <script type="application/ld+json">""" + jld_s + """</script>
    <link rel="stylesheet" href="/frontend/css/style.css">
</head>
<body>
    <script>window.__GAME_DATA__ = """ + gjson + """;</script>

    <header class="site-header">
        <div class="header-inner">
            <a href="/" class="logo">小白<span>游戏</span></a>
            <nav class="main-nav">
                <a href="/">首页</a>
                <a href="/frontend/games.html">游戏列表</a>
                <a href="/admin/index.html">后台管理</a>
            </nav>
            <button class="mobile-menu-btn" aria-label="菜单">
                <span></span><span></span><span></span>
            </button>
        </div>
    </header>

    <nav class="breadcrumb">
        <div class="container">
            <a href="/">首页</a>
            <span class="breadcrumb-sep">/</span>
            <a href="/frontend/games.html">游戏列表</a>
            <span class="breadcrumb-sep">/</span>
            <span class="breadcrumb-current" id="breadcrumb-title">""" + gte + """</span>
        </div>
    </nav>

    <main class="container game-detail-main">
        <div class="detail-content" id="detail-content">
            <section class="detail-hero">
                <div class="detail-cover-wrap">
                    """ + cov + """
                </div>
                <div class="detail-hero-body">
                    <h1 class="detail-title" id="detail-title">""" + gte + """</h1>
                    <div class="detail-tags" id="detail-tags">""" + th + """</div>
                    <div class="detail-meta-grid" id="detail-meta-grid">""" + mg + """</div>
                </div>
            </section>

            """ + ss + """

            <section class="detail-section">
                <h2 class="detail-section-title">游戏简介</h2>
                <div class="detail-desc" id="detail-desc">""" + desc + """</div>
            </section>
        </div>
    </main>

    <div class="download-bar" id="download-bar" style="display:flex">
        <div class="container download-bar-inner">
            <div class="download-bar-info">
                <span class="download-bar-title" id="download-bar-title">""" + gte + """</span>
                <span class="download-bar-size" id="download-bar-size">""" + sz + """</span>
            </div>
            <button class="btn btn-primary download-bar-btn" id="download-bar-btn" onclick="handleDownload()">
                <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                    <polyline points="7 10 12 15 17 10"/>
                    <line x1="12" y1="15" x2="12" y2="3"/>
                </svg>
                下载游戏
            </button>
        </div>
    </div>

    <footer class="site-footer">
        <div class="container">
            <p>&copy; 2026 """ + SITE_NAME + """. All rights reserved.</p>
        </div>
    </footer>

    <script src="/frontend/js/game-detail.js"></script>
</body>
</html>"""


def html_esc(s):
    if s is None:
        return ""
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

# ==================== 分类列表 ====================

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
                    'views': g.views,
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

    # Extract data before update to avoid expired attributes
    data = {
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
        'download_resources': await _get_game_downloads(db, game.id),
        'views': game.views,
        'created_at': str(game.created_at),
        'updated_at': str(game.updated_at),
    }

    # Increase views count
    await db.execute(
        update(Game).where(Game.id == game_id).values(views=Game.views + 1)
    )
    await db.commit()

    return {
        'code': 0,
        'message': 'success',
        'data': data,
    }



# ==================== 游戏详情 (Slug) ====================

@router.get('/api/game/slug/{slug}', summary='通过 Slug 获取游戏详情')
async def get_game_by_slug(
    slug: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Game).where(
            Game.slug == slug,
            Game.publish_status == 'published',
        )
    )
    game = result.scalar_one_or_none()

    if not game:
        raise HTTPException(status_code=404, detail='游戏不存在或未发布')

    # Extract data before update to avoid expired attributes
    data = {
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
        'download_resources': await _get_game_downloads(db, game.id),
        'views': game.views,
        'created_at': str(game.created_at),
        'updated_at': str(game.updated_at),
    }

    # Increase views count
    await db.execute(
        update(Game).where(Game.id == game.id).values(views=Game.views + 1)
    )
    await db.commit()

    return {
        'code': 0,
        'message': 'success',
        'data': data,
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

@router.get('/game/{identifier}', summary='游戏详情页 (SEO)')
async def game_page(
    identifier: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """SEO ???????????slug ???? HTML??? ID 301 ??? slug URL?"""
    if identifier.isdigit():
        game_id = int(identifier)
        result = await db.execute(
            select(Game).where(
                Game.id == game_id,
                Game.publish_status == 'published',
            )
        )
        game = result.scalar_one_or_none()
        if not game:
            raise HTTPException(status_code=404, detail='游戏不存在或未发布')
        if game.slug:
            return RedirectResponse(f'/game/{game.slug}', status_code=301)
        slug = str(game.id)
    else:
        slug = identifier
        result = await db.execute(
            select(Game).where(
                Game.slug == slug,
                Game.publish_status == 'published',
            )
        )
        game = result.scalar_one_or_none()
        if not game:
            raise HTTPException(status_code=404, detail='游戏不存在或未发布')

    game_dict = {
        'id': game.id, 'title': game.title, 'slug': game.slug,
        'cover': game.cover or '', 'images': game.images or [],
        'description': game.description or '', 'system': game.system or '',
        'language': game.language or '', 'size': game.size or '',
        'version': game.version or '', 'publisher': game.publisher or '',
        'developer': game.developer or '',
        'release_date': str(game.release_date) if game.release_date else '',
        'category': game.category or '',
        'category_name': game.category_rel.name if game.category_rel else (game.category or ''),
        'tags': game.tags or [], 'download_url': game.download_url or '',
        'original_url': game.original_url or '', 'crawler_source': game.crawler_source or '',
        'transfer_status': game.transfer_status or '', 'views': game.views,
        'seo_title': game.seo_title or '', 'seo_description': game.seo_description or '',
        'seo_keywords': game.seo_keywords or '',
        'download_resources': await _get_game_downloads(db, game.id),
        'created_at': str(game.created_at) if game.created_at else '',
        'updated_at': str(game.updated_at) if game.updated_at else '',
    }

    meta = _build_game_meta(game)

    await db.execute(
        update(Game).where(Game.id == game.id).values(views=Game.views + 1)
    )
    await db.commit()

    html = _render_game_detail_html(game, meta, game_dict)
    return HTMLResponse(content=html)


# ==================== SEO 站点文件 ====================

@router.get('/sitemap.xml', summary='站点地图')
async def sitemap(db: AsyncSession = Depends(get_db)):
    """生成符合搜索引擎标准的 sitemap.xml"""
    result = await db.execute(
        select(Game).where(Game.publish_status == 'published').order_by(Game.updated_at.desc())
    )
    games = result.scalars().all()
    urls = []
    urls.append('  <url>\n    <loc>' + SITE_URL + '</loc>\n    <changefreq>daily</changefreq>\n    <priority>1.0</priority>\n  </url>')
    urls.append('  <url>\n    <loc>' + SITE_URL + '/frontend/games.html</loc>\n    <changefreq>daily</changefreq>\n    <priority>0.9</priority>\n  </url>')
    for g in games:
        loc = SITE_URL + '/game/' + (g.slug or str(g.id))
        lm = str(g.updated_at)[:10] if g.updated_at else (str(g.created_at)[:10] if g.created_at else '')
        lm_line = '\n    <lastmod>' + lm + '</lastmod>' if lm else ''
        urls.append('  <url>\n    <loc>' + loc + '</loc>' + lm_line + '\n    <changefreq>weekly</changefreq>\n    <priority>0.8</priority>\n  </url>')
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + '\n'.join(urls) + '\n</urlset>'
    return HTMLResponse(content=xml, media_type='application/xml')


@router.get('/robots.txt', summary='robots.txt')
async def robots():
    """返回 robots.txt"""
    txt = """User-agent: *
Allow: /
Disallow: /admin/
Disallow: /api/admin/
Disallow: /api/crawler/
Disallow: /api/transfer/
Disallow: /api/ai/

Sitemap: """ + SITE_URL + """/sitemap.xml
"""
    return HTMLResponse(content=txt, media_type='text/plain')


@router.get('/game/{game_id}/download-qr', summary='游戏下载页（旧版兼容）')
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

async def _get_game_downloads(db: AsyncSession, game_id: int) -> list:
    result = await db.execute(
        select(DownloadResource)
        .where(
            DownloadResource.game_id == game_id,
            DownloadResource.status.in_(["active", "pending"]),
        )
        .order_by(DownloadResource.display_order.asc(), DownloadResource.id.asc())
    )
    resources = result.scalars().all()
    items = []
    for r in resources:
        provider_name = ""
        provider_code = r.provider
        if r.provider_rel:
            provider_name = r.provider_rel.name
            provider_code = r.provider_rel.code
        items.append({
            "id": r.id,
            "provider_code": provider_code,
            "provider_name": provider_name or provider_code,
            "title": r.title or "",
            "extract_code": r.extract_code or "",
            "display_order": r.display_order,
        })
    return items


@router.get("/api/game/{game_id}/download-resources", summary="Get game download resources")
async def get_game_download_resources(
    game_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Game).where(Game.id == game_id, Game.publish_status == "published")
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Game not found")
    items = await _get_game_downloads(db, game_id)
    return {
        "code": 0,
        "message": "success",
        "data": {"resources": items},
    }
