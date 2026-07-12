"""
AI 运营接口（预留）
----------------
后续 AI 程序通过此接口生成游戏描述、标签等内容。
当前返回 501 Not Implemented。
"""

from fastapi import APIRouter

router = APIRouter(prefix="/api/ai", tags=["AI"])


@router.post("/generate", summary="[预留] AI 生成游戏内容")
async def ai_generate():
    """AI 程序自动生成游戏描述、标签、推荐内容的入口。

    请求格式（预留）：
    {
        "game_id": 123,
        "task": "description",      // 任务类型
        "options": {}               // 生成选项
    }
    """
    return {
        "code": 501,
        "message": "AI 模块尚未实现，此接口为预留接口",
        "data": None,
    }
