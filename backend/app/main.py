"""小白游戏资源站 - 主应用入口 v0.8.1A"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
from pathlib import Path

from .core.config import settings
from .core.database import init_db
from .api.games import router as games_router
from .api.admin import router as admin_router
from .api.crawler import router as crawler_router
from .api.transfer import router as transfer_router
from .api.ai import router as ai_router
from .api.download_resources import router as download_resources_router
from .api.download_providers import router as download_providers_router
from .api.download_controller import router as download_controller_router
from .api.download_stats import router as download_stats_router
from .api.tags import router as tags_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    print(f"[启动] {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"[启动] 数据库已初始化: {settings.db_url}")
    print(f"[启动] 监听地址: http://{settings.HOST}:{settings.PORT}")
    yield
    print("[关闭] 应用已停止")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="游戏资源分享网站 - 后端 API 服务",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册 API 路由
app.include_router(games_router)
app.include_router(admin_router)
app.include_router(crawler_router)
app.include_router(transfer_router)
app.include_router(ai_router)
app.include_router(download_resources_router)
app.include_router(download_providers_router)
app.include_router(download_controller_router)
app.include_router(download_stats_router)
app.include_router(tags_router)

# 静态文件
frontend_dir = settings.PROJECT_ROOT / "frontend"
admin_dir = settings.PROJECT_ROOT / "admin"
uploads_dir = settings.PROJECT_ROOT / "uploads"

if frontend_dir.exists():
    app.mount("/frontend", StaticFiles(directory=str(frontend_dir)), name="frontend")

# Admin static assets mounted at /admin-static (CSS, JS, images)
if admin_dir.exists():
    app.mount("/admin-static", StaticFiles(directory=str(admin_dir)), name="admin_static")

if uploads_dir.exists():
    app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")


# ==================== 页面路由 ====================

@app.get("/", summary="首页")
async def root():
    index_path = settings.PROJECT_ROOT / "frontend" / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"name": settings.APP_NAME, "version": settings.APP_VERSION}


@app.get("/games", summary="游戏列表页")
async def games_page():
    """游戏列表页 - 转发到 frontend/games.html"""
    games_path = settings.PROJECT_ROOT / "frontend" / "games.html"
    if games_path.exists():
        return FileResponse(str(games_path))
    return RedirectResponse(url="/frontend/games.html")


# ==================== 后台管理页面路由 ====================

def _get_token_from_cookie(request: Request) -> str | None:
    """从 Cookie 或 Header 中提取 token"""
    token = request.cookies.get("admin_token")
    if not token:
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:]
    return token


def _is_admin_authenticated(request: Request) -> bool:
    """检查请求是否携带有效的 admin token"""
    from .core.auth import decode_access_token
    token = _get_token_from_cookie(request)
    if not token:
        return False
    payload = decode_access_token(token)
    return payload is not None


@app.get("/admin", summary="后台首页")
@app.get("/admin/", summary="后台首页")
async def admin_index(request: Request):
    """后台入口：未登录跳转到登录页"""
    if not _is_admin_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=302)
    return FileResponse(str(admin_dir / "index.html"))


@app.get("/admin/login", summary="后台登录页")
@app.get("/admin/login.html", summary="后台登录页")
async def admin_login_page(request: Request):
    """后台登录页面"""
    if _is_admin_authenticated(request):
        return RedirectResponse(url="/admin", status_code=302)
    return FileResponse(str(admin_dir / "login.html"))


@app.get("/admin/index.html", summary="后台仪表盘")
async def admin_dashboard(request: Request):
    """后台仪表盘 - 需要登录"""
    if not _is_admin_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=302)
    return FileResponse(str(admin_dir / "index.html"))


@app.get("/{path:path}", summary="SPA fallback")
async def spa_fallback(path: str):
    """未知路径返回 404"""
    from fastapi.responses import JSONResponse
    return JSONResponse({"detail": "Not Found"}, status_code=404)
