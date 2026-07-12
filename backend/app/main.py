"""
小白游戏资源站 - 主应用入口
=========================
FastAPI 应用的主入口，负责注册路由、中间件、生命周期事件。
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from .core.config import settings
from .core.database import init_db
from .api.games import router as games_router
from .api.admin import router as admin_router
from .api.crawler import router as crawler_router
from .api.transfer import router as transfer_router
from .api.ai import router as ai_router
from .api.download_resources import router as download_resources_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时：初始化数据库表
    await init_db()
    print(f"[启动] {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"[启动] 数据库已初始化: {settings.db_url}")
    print(f"[启动] 监听地址: http://{settings.HOST}:{settings.PORT}")
    yield
    # 关闭时：清理资源
    print("[关闭] 应用已停止")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="游戏资源分享网站 - 后端 API 服务",
    lifespan=lifespan,
)

# ==================== CORS 中间件 ====================
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== 注册路由 ====================
app.include_router(games_router)       # 公开游戏接口
app.include_router(admin_router)       # 后台管理接口
app.include_router(crawler_router)     # 采集接口（预留）
app.include_router(transfer_router)    # 资源中转接口（预留）
app.include_router(ai_router)          # AI ??????
app.include_router(download_resources_router)   # ???????? 接口（预留）

# ==================== 静态文件服务 ====================
# 前台页面
frontend_dir = settings.PROJECT_ROOT / "frontend"
if frontend_dir.exists():
    app.mount("/frontend", StaticFiles(directory=str(frontend_dir)), name="frontend")

# 后台管理页面
admin_dir = settings.PROJECT_ROOT / "admin"
if admin_dir.exists():
    app.mount("/admin", StaticFiles(directory=str(admin_dir), html=True), name="admin")

# 上传文件访问
uploads_dir = settings.PROJECT_ROOT / "uploads"
if uploads_dir.exists():
    app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")


# ==================== 根路径 ====================

@app.get("/", summary="首页")
async def root():
    """返回前端首页 HTML"""
    from fastapi.responses import FileResponse
    index_path = settings.PROJECT_ROOT / "frontend" / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"name": settings.APP_NAME, "version": settings.APP_VERSION}

