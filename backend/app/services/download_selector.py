"""
下载资源选择器（模块7.8）
-----------------------
根据优先级自动选择最优下载资源，支持故障切换和优先级排序。
"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from ..models.download_resource import DownloadResource
from ..models.download_provider import DownloadProvider


async def get_best_resource(db: AsyncSession, game_id: int) -> Optional[dict]:
    """获取游戏的最优下载资源。

    查询条件：
    - game_id 匹配
    - status 为 active
    - 按 priority DESC 排序，返回第一条

    Returns:
        dict 包含 resource_id, provider, provider_name, url, priority, extract_code
        如果无可用资源则返回 None
    """
    result = await db.execute(
        select(DownloadResource)
        .options(joinedload(DownloadResource.provider_rel))
        .where(
            DownloadResource.game_id == game_id,
            DownloadResource.status == "active",
        )
        .order_by(DownloadResource.priority.desc())
        .limit(1)
    )
    resource = result.unique().scalar_one_or_none()
    if not resource or not resource.my_share_url:
        return None

    return _serialize_selector_result(resource)


async def get_fallback_resource(
    db: AsyncSession, game_id: int, current_resource_id: int
) -> Optional[dict]:
    """获取故障切换备选资源。

    查询当前游戏全部 active 资源，排除当前资源，按 priority DESC 返回下一条。

    Returns:
        dict 或 None（无备选资源时）
    """
    result = await db.execute(
        select(DownloadResource)
        .options(joinedload(DownloadResource.provider_rel))
        .where(
            DownloadResource.game_id == game_id,
            DownloadResource.status == "active",
            DownloadResource.id != current_resource_id,
        )
        .order_by(DownloadResource.priority.desc())
        .limit(1)
    )
    resource = result.unique().scalar_one_or_none()
    if not resource or not resource.my_share_url:
        return None

    return _serialize_selector_result(resource)


def _serialize_selector_result(resource: DownloadResource) -> dict:
    """将 DownloadResource 序列化为选择器返回格式"""
    provider_code = resource.provider
    provider_name = resource.provider
    if resource.provider_rel:
        provider_code = resource.provider_rel.code
        provider_name = resource.provider_rel.name

    return {
        "resource_id": resource.id,
        "provider": provider_code,
        "provider_name": provider_name,
        "url": resource.my_share_url,
        "priority": resource.priority,
        "extract_code": resource.extract_code or "",
        "title": resource.title or "",
    }