"""
下载服务（模块7.4）
-----------------
提供 Token 生成、获取、日志记录等核心业务逻辑。
Controller 层通过此 Service 访问数据。
模块7.6 增强：日志记录新增 provider_id 和 referer 字段。
"""
import secrets
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from ..models.download_token import DownloadToken
from ..models.download_resource import DownloadResource
from ..models.download_provider import DownloadProvider
from ..models.download_log import DownloadLog
from ..models.game import Game


async def get_or_create_token(
    db: AsyncSession, resource_id: int
) -> Tuple[DownloadToken, bool]:
    """获取或创建下载 Token。
    
    如果该资源已有 Token 则直接返回，否则创建新 Token。
    Token 使用 secrets.token_urlsafe(32) 生成。
    并发安全：捕获 IntegrityError 后回退到查询已有 Token。
    
    Returns:
        (token, created): Token 对象和是否为新创建
    """
    result = await db.execute(
        select(DownloadToken).where(
            DownloadToken.resource_id == resource_id,
            DownloadToken.status == "active",
        )
    )
    existing = result.scalars().first()
    if existing:
        return existing, False

    # 获取下载资源信息
    result = await db.execute(
        select(DownloadResource).where(DownloadResource.id == resource_id)
    )
    resource = result.scalar_one_or_none()
    if not resource:
        raise ValueError(f"下载资源 {resource_id} 不存在")

    token_str = secrets.token_urlsafe(32)
    token = DownloadToken(
        token=token_str,
        resource_id=resource_id,
        game_id=resource.game_id,
        provider_code=resource.provider,
        status="active",
    )
    db.add(token)
    try:
        await db.flush()
    except IntegrityError:
        # 并发场景：另一个请求已创建同资源 Token，或 Token 字符串意外碰撞
        # 回滚当前插入，重新查询已有 Token
        await db.rollback()
        result = await db.execute(
            select(DownloadToken).where(
                DownloadToken.resource_id == resource_id,
                DownloadToken.status == "active",
            )
        )
        existing = result.scalars().first()
        if existing:
            return existing, False
        # Token 字符串碰撞（极低概率）：重新抛出，由调用方决定重试
        raise

    await db.refresh(token)
    return token, True


async def get_token_by_string(
    db: AsyncSession, token_str: str
) -> Optional[DownloadToken]:
    """根据 Token 字符串查找 Token 记录。"""
    result = await db.execute(
        select(DownloadToken).where(
            DownloadToken.token == token_str,
            DownloadToken.status == "active",
        )
    )
    return result.scalar_one_or_none()


async def resolve_resource_for_download(
    db: AsyncSession, token: DownloadToken
) -> Optional[dict]:
    """根据 Token 解析出完整的下载信息（含网盘链接、渠道名称等）。
    
    Returns:
        dict 包含 game_title, provider_name, provider_code,
             provider_id, share_url, extract_code, resource_title
    """
    result = await db.execute(
        select(DownloadResource).where(
            DownloadResource.id == token.resource_id
        )
    )
    resource = result.scalar_one_or_none()
    if not resource or resource.status not in ("active", "pending"):
        return None

    result = await db.execute(
        select(Game).where(Game.id == token.game_id)
    )
    game = result.scalar_one_or_none()
    game_title = game.title if game else ""

    provider_name = ""
    provider_code = token.provider_code or resource.provider
    provider_id = resource.provider_id  # 模块7.6: 用于统计
    if resource.provider_rel:
        provider_name = resource.provider_rel.name
        if not provider_id:
            provider_id = resource.provider_rel.id
    else:
        # 尝试从 provider 表查找
        result = await db.execute(
            select(DownloadProvider).where(
                DownloadProvider.code == resource.provider
            )
        )
        p = result.scalar_one_or_none()
        if p:
            provider_name = p.name
            provider_id = p.id

    if not resource.my_share_url:
        return None

    return {
        "game_title": game_title,
        "game_id": token.game_id,
        "provider_name": provider_name,
        "provider_code": provider_code,
        "provider_id": provider_id,
        "share_url": resource.my_share_url,
        "extract_code": resource.extract_code or "",
        "resource_title": resource.title or "",
    }


async def log_download_action(
    db: AsyncSession,
    token_str: str,
    resource_id: int,
    game_id: int,
    ip_address: str,
    user_agent: str,
    device_type: str,
    action: str,
    provider_id: Optional[int] = None,
    referer: str = "",
):
    """记录下载行为日志（模块7.6增强：新增 provider_id 和 referer）。
    
    日志记录失败不会阻塞主流程。
    """
    try:
        log_entry = DownloadLog(
            token=token_str,
            resource_id=resource_id,
            game_id=game_id,
            provider_id=provider_id,
            ip_address=ip_address or "",
            user_agent=user_agent or "",
            referer=referer or "",
            device_type=device_type,
            action=action,
        )
        db.add(log_entry)
        await db.flush()
    except Exception:
        # 日志记录失败不影响主流程
        pass