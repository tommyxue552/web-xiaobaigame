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
from ..core.config import settings
from ..models.game import Game
from ..models.category import Category
from ..models.download_resource import DownloadResource
from ..services import download_selector
from ..models.download_provider import DownloadProvider
from ..models.tag import Tag
from ..models.game_tag import GameTag
import qrcode

router = APIRouter(tags=['Games'])

MOBILE_UA_REGEX = r'Android|iPhone|iPad|iPod|webOS|BlackBerry|Windows Phone'

SITE_NAME = settings.APP_NAME
def _site_url():
    return settings.SITE_URL.rstrip('/')



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
    canon = _site_url() + "/game/" + slug
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
    <meta name="description" content=\"""" + d + """">
    <meta name="keywords" content=\"""" + kw + """">
    <meta property="og:title" content=\"""" + t + """">
    <meta property="og:description" content=\"""" + d + """">
    <meta property="og:type" content="website">
    <meta property="og:url" content=\"""" + canon + """">
    <meta property="og:site_name" content=\"""" + SITE_NAME + """">
    <meta property="og:locale" content="zh_CN">
    """ + og_img + """
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content=\"""" + t + """">
    <meta name="twitter:description" content=\"""" + d + """">
    """ + tw_img + """
    <link rel="canonical" href=\"""" + canon + """">
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
                <a href="/games">游戏列表</a>
                <a href="/admin">后台管理</a>
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
            <a href="/games">游戏列表</a>
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

    # Inject related games section before </main>
    related_games = await _get_related_games(db, game.id, game.category_id, limit=8)
    if related_games:
        rel_cards = ""
        for rg in related_games:
            rt = html_esc(rg["title"])
            rs = html_esc(rg["slug"])
            rc = html_esc(rg.get("cover", "") or "")
            rcat = html_esc(rg.get("category", "") or "")
            rsz = html_esc(rg.get("size", "") or "")
            rc_html = f'<img src="{rc}" alt="{rt}" loading="lazy" onerror="this.style.display=\'none\'">' if rc else '<div class="game-card-placeholder"></div>'
            rel_cards += f'<a href="/game/{rs}" class="game-card"><div class="game-card-cover">{rc_html}</div><div class="game-card-body"><h3 class="game-card-title">{rt}</h3><div class="game-card-meta"><span>{rcat}</span><span>{rsz}</span></div></div></a>'
        rel_section = '<section class="detail-section related-games-section"><h2 class="detail-section-title">相关推荐</h2><div class="game-cards-grid">' + rel_cards + '</div></section>'
        html = html.replace('</main>', rel_section + '\n</main>')

    return HTMLResponse(content=html)


# ==================== SEO 站点文件 ====================

@router.get('/sitemap.xml', summary='站点地图')
async def sitemap(db: AsyncSession = Depends(get_db)):
    """生成符合搜索引擎标准的 sitemap.xml（支持分类URL和分页索引）"""
    # 查询已发布的游戏
    result = await db.execute(
        select(Game).where(Game.publish_status == 'published').order_by(Game.updated_at.desc())
    )
    games = result.scalars().all()
    
    # 查询分类
    cat_result = await db.execute(select(Category).order_by(Category.id))
    
    # 查询标签
    tag_result = await db.execute(select(Tag).where(Tag.is_active == True).order_by(Tag.sort_order.asc()))
    tags = tag_result.scalars().all()
    categories = cat_result.scalars().all()
    
    # 计算总URL数：首页 + 游戏列表 + 分类页 + 各游戏详情
    base_url_count = 2  # 首页 + 游戏列表页
    cat_url_count = len(categories)
    tag_url_count = len(tags) if tags else 0
    game_url_count = len(games)
    total_urls = base_url_count + cat_url_count + tag_url_count + game_url_count
    
    # Sitemap 协议限制：单文件最多 50000 条 URL
    MAX_URLS_PER_SITEMAP = 50000
    
    if total_urls <= MAX_URLS_PER_SITEMAP:
        # 小站点：直接返回完整 sitemap
        urls = _build_sitemap_urls(games, categories, tags)
        xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + '\n'.join(urls) + '\n</urlset>'
        return HTMLResponse(content=xml, media_type='application/xml')
    
    # 大站点：返回 sitemap index
    total_pages = (total_urls + MAX_URLS_PER_SITEMAP - 1) // MAX_URLS_PER_SITEMAP
    index_urls = []
    for p in range(1, total_pages + 1):
        index_urls.append(
            '  <sitemap>\n    <loc>' + _site_url() + '/sitemap-' + str(p) + '.xml</loc>\n  </sitemap>'
        )
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + '\n'.join(index_urls) + '\n</sitemapindex>'
    return HTMLResponse(content=xml, media_type='application/xml')


@router.get('/sitemap-{page}.xml', summary='站点地图分页')
async def sitemap_page(
    page: int,
    db: AsyncSession = Depends(get_db),
):
    """分页站点地图，每页最多 50000 条 URL"""
    MAX_URLS_PER_SITEMAP = 50000
    
    # 查询所有已发布游戏和分类
    result = await db.execute(
        select(Game).where(Game.publish_status == 'published').order_by(Game.updated_at.desc())
    )
    games = result.scalars().all()
    
    cat_result = await db.execute(select(Category).order_by(Category.id))
    categories = cat_result.scalars().all()

    # ????
    tag_result = await db.execute(select(Tag).where(Tag.is_active == True).order_by(Tag.sort_order.asc()))
    tags = tag_result.scalars().all()
    
    # 构建完整的URL列表
    all_urls = _build_sitemap_urls(games, categories, tags)
    total_urls = len(all_urls)
    total_pages = (total_urls + MAX_URLS_PER_SITEMAP - 1) // MAX_URLS_PER_SITEMAP
    
    if page < 1 or page > total_pages:
        raise HTTPException(status_code=404, detail='Sitemap page not found')
    
    start = (page - 1) * MAX_URLS_PER_SITEMAP
    end = min(start + MAX_URLS_PER_SITEMAP, total_urls)
    page_urls = all_urls[start:end]
    
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + '\n'.join(page_urls) + '\n</urlset>'
    return HTMLResponse(content=xml, media_type='application/xml')


# ==================== ????? (??7.7) ====================

def _build_tag_meta(tag: Tag) -> dict:
    """构建标签页 SEO 元数据"""
    title = tag.seo_title or f"{tag.name} 游戏合集 - {SITE_NAME}"
    desc = tag.seo_description or tag.description or f"浏览{tag.name}游戏推荐列表"
    keywords = tag.seo_keywords or f"{tag.name},游戏,单机游戏,游戏下载"
    return {
        "title": title,
        "description": desc[:300],
        "keywords": keywords,
    }


def _render_tag_page_html(tag: Tag, games_data: list, meta: dict, page: int, total: int, page_size: int) -> str:
    """渲染标签页 HTML (SSR + SEO)"""
    t = html_esc(meta["title"])
    d = html_esc(meta["description"])
    kw = html_esc(meta["keywords"])
    canon = _site_url() + "/tag/" + tag.slug
    tag_name = html_esc(tag.name)
    tag_desc = html_esc(tag.description or "")

    # Build game cards HTML
    cards = ""
    for g in games_data:
        g_title = html_esc(g.get("title", ""))
        g_slug = html_esc(g.get("slug", ""))
        g_cover = html_esc(g.get("cover", "") or "")
        g_cat = html_esc(g.get("category", "") or "")
        g_size = html_esc(g.get("size", "") or "")
        cover_html = f'<img src="{g_cover}" alt="{g_title}" loading="lazy" onerror="this.style.display=\'none\'">' if g_cover else '<div class="game-card-placeholder"></div>'
        cards += f"""<a href="/game/{g_slug}" class="game-card">
    <div class="game-card-cover">{cover_html}</div>
    <div class="game-card-body">
        <h3 class="game-card-title">{g_title}</h3>
        <div class="game-card-meta">
            <span>{g_cat}</span>
            <span>{g_size}</span>
        </div>
    </div>
</a>"""

    # Pagination
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
    pagination = ""
    if total_pages > 1:
        pagination += '<div class="pagination">'
        if page > 1:
            pagination += f'<a href="/tag/{tag.slug}?page={page-1}" class="page-btn">&laquo; 上一页</a>'
        for p in range(max(1, page - 2), min(total_pages + 1, page + 3)):
            active = ' active' if p == page else ''
            pagination += f'<a href="/tag/{tag.slug}?page={p}" class="page-btn{active}">{p}</a>'
        if page < total_pages:
            pagination += f'<a href="/tag/{tag.slug}?page={page+1}" class="page-btn">下一页 &raquo;</a>'
        pagination += '</div>'

    jld = {
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": tag.name,
        "description": meta["description"],
        "url": canon,
    }
    jld_s = json.dumps(jld, ensure_ascii=False)

    desc_section = f'<div class="tag-description">{tag_desc}</div>' if tag_desc else ""

    return """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>""" + t + """</title>
    <meta name="description" content=\"""" + d + """">
    <meta name="keywords" content=\"""" + kw + """">
    <meta property="og:title" content=\"""" + t + """">
    <meta property="og:description" content=\"""" + d + """">
    <meta property="og:type" content="website">
    <meta property="og:url" content=\"""" + canon + """">
    <meta property="og:site_name" content=\"""" + SITE_NAME + """">
    <meta property="og:locale" content="zh_CN">
    <meta name="twitter:card" content="summary">
    <meta name="twitter:title" content=\"""" + t + """">
    <meta name="twitter:description" content=\"""" + d + """">
    <link rel="canonical" href="""" + canon + """">
    <script type="application/ld+json">""" + jld_s + """</script>
    <link rel="stylesheet" href="/frontend/css/style.css">
</head>
<body>
    <header class="site-header">
        <div class="header-inner">
            <a href="/" class="logo">小白<span>游戏</span></a>
            <nav class="main-nav">
                <a href="/">首页</a>
                <a href="/games">全部游戏</a>
                <a href="/admin">后台管理</a>
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
            <span class="breadcrumb-current">""" + tag_name + """</span>
        </div>
    </nav>

    <main class="container tag-page-main">
        <section class="tag-header">
            <h1 class="tag-title">""" + tag_name + """</h1>
            """ + desc_section + """
            <p class="tag-count">共 <strong>""" + str(total) + """</strong> 款游戏</p>
        </section>

        <section class="game-cards-grid">
            """ + cards + """
        </section>

        """ + pagination + """
    </main>

    <footer class="site-footer">
        <div class="container">
            <p>&copy; 2026 """ + SITE_NAME + """. All rights reserved.</p>
        </div>
    </footer>
</body>
</html>"""


@router.get("/tag/{slug}", summary="标签详情页 (SEO)")
async def tag_page(
    slug: str,
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """标签详情页 - SSR + SEO"""
    result = await db.execute(
        select(Tag).where(Tag.slug == slug, Tag.is_active == True)
    )
    tag = result.scalar_one_or_none()
    if not tag:
        raise HTTPException(status_code=404, detail="标签不存在")

    # Count games with this tag
    count_query = select(func.count()).select_from(GameTag).where(GameTag.tag_id == tag.id)
    total = (await db.execute(count_query)).scalar() or 0

    # Get paginated game IDs for this tag
    offset = (page - 1) * page_size
    gt_result = await db.execute(
        select(GameTag.game_id)
        .where(GameTag.tag_id == tag.id)
        .order_by(GameTag.id.desc())
        .offset(offset)
        .limit(page_size)
    )
    game_ids = [row[0] for row in gt_result.all()]

    # Fetch games
    games_data = []
    if game_ids:
        g_result = await db.execute(
            select(Game)
            .where(Game.id.in_(game_ids), Game.publish_status == "published")
        )
        games = {g.id: g for g in g_result.scalars().all()}
        # Preserve order from game_tags
        for gid in game_ids:
            if gid in games:
                g = games[gid]
                games_data.append({
                    "id": g.id, "title": g.title, "slug": g.slug,
                    "cover": g.cover or "", "category": g.category or "",
                    "size": g.size or "",
                })

    meta = _build_tag_meta(tag)
    html = _render_tag_page_html(tag, games_data, meta, page, total, page_size)
    return HTMLResponse(content=html)



async def _get_related_games(db: AsyncSession, game_id: int, category_id: int, limit: int = 8) -> list:
    """获取相关游戏推荐，优先同Tag，其次同Category"""
    related_ids = set()

    # 1. Same tags
    tag_result = await db.execute(
        select(GameTag.game_id)
        .where(GameTag.game_id != game_id)
        .where(
            GameTag.tag_id.in_(
                select(GameTag.tag_id).where(GameTag.game_id == game_id)
            )
        )
        .limit(limit)
    )
    for row in tag_result.all():
        related_ids.add(row[0])

    # 2. Same category (fill remaining)
    remaining = limit - len(related_ids)
    if remaining > 0 and category_id:
        cat_result = await db.execute(
            select(Game.id)
            .where(
                Game.id != game_id,
                Game.category_id == category_id,
                Game.publish_status == "published",
            )
            .order_by(Game.views.desc())
            .limit(remaining * 2)
        )
        for row in cat_result.all():
            if row[0] not in related_ids:
                related_ids.add(row[0])
            if len(related_ids) >= limit:
                break

    if not related_ids:
        return []

    # Fetch game data
    g_result = await db.execute(
        select(Game).where(Game.id.in_(list(related_ids)), Game.publish_status == "published")
    )
    games = []
    for g in g_result.scalars().all():
        games.append({
            "id": g.id, "title": g.title, "slug": g.slug,
            "cover": g.cover or "", "category": g.category or "",
            "size": g.size or "",
        })
    return games[:limit]



def _build_sitemap_urls(games, categories, tags=None) -> list:
    """构建 sitemap URL 列表（包含首页、分类、游戏详情）"""
    urls = []
    base = _site_url()
    
    # 首页
    urls.append('  <url>\n    <loc>' + base + '</loc>\n    <changefreq>daily</changefreq>\n    <priority>1.0</priority>\n  </url>')
    
    # 游戏列表页
    urls.append('  <url>\n    <loc>' + base + '/games</loc>\n    <changefreq>daily</changefreq>\n    <priority>0.9</priority>\n  </url>')
    
    # 分类页
    for cat in categories:
        urls.append(
            '  <url>\n    <loc>' + base + '/games?category=' + (cat.slug or '') + '</loc>\n    <changefreq>weekly</changefreq>\n    <priority>0.7</priority>\n  </url>'
        )
    
    # 标签页
    if tags:
        for tag in tags:
            urls.append(
                '  <url>\n    <loc>' + base + '/tag/' + (tag.slug or '') + '</loc>\n    <changefreq>weekly</changefreq>\n    <priority>0.6</priority>\n  </url>'
            )

    # 游戏详情页
    for g in games:
        loc = base + '/game/' + (g.slug or str(g.id))
        lm = str(g.updated_at)[:10] if g.updated_at else (str(g.created_at)[:10] if g.created_at else '')
        lm_line = '\n    <lastmod>' + lm + '</lastmod>' if lm else ''
        urls.append('  <url>\n    <loc>' + loc + '</loc>' + lm_line + '\n    <changefreq>weekly</changefreq>\n    <priority>0.8</priority>\n  </url>')
    
    return urls


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

Sitemap: """ + _site_url() + """/sitemap.xml
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


# ==================== ??7.8: ???????? ====================

@router.get("/api/game/{game_id}/download", summary="??????????")
async def get_best_game_download(
    game_id: int,
    db: AsyncSession = Depends(get_db),
):
    """????????????????? priority DESC ???????? active ???"""
    best = await download_selector.get_best_resource(db, game_id)
    if not best:
        raise HTTPException(status_code=404, detail="???????????")
    return {
        "code": 0,
        "message": "success",
        "data": best,
    }


async def _get_game_downloads(db: AsyncSession, game_id: int) -> list:
    result = await db.execute(
        select(DownloadResource)
        .where(
            DownloadResource.game_id == game_id,
            DownloadResource.status.in_(["active", "pending"]),
        )
        .order_by(DownloadResource.priority.desc(), DownloadResource.display_order.asc(), DownloadResource.id.asc())
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
            "priority": r.priority if r.priority is not None else 100,
            "is_primary": bool(r.is_primary) if r.is_primary is not None else False,
            "success_count": r.success_count if r.success_count is not None else 0,
            "fail_count": r.fail_count if r.fail_count is not None else 0,
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
