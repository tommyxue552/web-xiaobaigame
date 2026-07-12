"""
采集接口（预留）
--------------
后续采集程序通过此接口批量导入游戏数据。
当前返回 501 Not Implemented。
"""

from fastapi import APIRouter

router = APIRouter(prefix="/api/crawler", tags=["Crawler"])


@router.post("/import", summary="[预留] 采集数据批量导入")
async def crawler_import():
    """采集程序批量导入游戏资源的入口。
    
    请求格式（预留）：
    {
        "source": "steam",          // 采集来源
        "batch_id": "uuid",         // 批次标识
        "games": [...]              // 游戏数据列表
    }
    """
    return {
        "code": 501,
        "message": "采集模块尚未实现，此接口为预留接口",
        "data": None,
    }
