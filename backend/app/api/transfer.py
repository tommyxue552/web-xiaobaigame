"""
资源中转接口（预留）
-----------------
后续资源中转程序通过此接口更新下载链接。
当前返回 501 Not Implemented。
"""

from fastapi import APIRouter

router = APIRouter(prefix="/api/transfer", tags=["Transfer"])


@router.post("/update-link", summary="[预留] 更新资源下载链接")
async def transfer_update_link():
    """资源中转程序更新游戏下载链接的入口。

    请求格式（预留）：
    {
        "game_id": 123,
        "download_url": "https://...",
        "file_size": "1.2GB",
        "transfer_status": "completed"
    }
    """
    return {
        "code": 501,
        "message": "资源中转模块尚未实现，此接口为预留接口",
        "data": None,
    }
