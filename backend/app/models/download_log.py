"""
下载日志模型（模块7.4 预留，模块7.6 增强）
----------------------------------------
download_logs 表：记录每次下载页访问和跳转行为。
模块7.6 新增 provider_id 和 referer 字段用于渠道/来源分析。
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Index, ForeignKey
from sqlalchemy.sql import func
from ..core.database import Base


class DownloadLog(Base):
    __tablename__ = "download_logs"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    token = Column(String(64), default="", comment="下载Token")
    resource_id = Column(Integer, default=None, nullable=True, comment="关联下载资源ID")
    game_id = Column(Integer, default=None, nullable=True, comment="关联游戏ID")
    provider_id = Column(
        Integer,
        ForeignKey("download_providers.id", ondelete="SET NULL"),
        default=None,
        nullable=True,
        comment="关联下载渠道ID（模块7.6）",
    )
    ip_address = Column(String(45), default="", comment="用户IP")
    user_agent = Column(Text, default="", comment="User-Agent")
    referer = Column(String(500), default="", comment="HTTP Referer（模块7.6）")
    device_type = Column(String(20), default="", comment="pc/mobile/unknown")
    action = Column(
        String(20), default="view", comment="view(查看)/redirect(跳转)"
    )
    created_at = Column(
        DateTime, server_default=func.now(), comment="创建时间"
    )

    __table_args__ = (
        Index("idx_dl_token", "token"),
        Index("idx_dl_created", "created_at"),
        Index("idx_dl_action", "action"),
        Index("idx_dl_game_id", "game_id"),
        Index("idx_dl_provider_id", "provider_id"),
        Index("idx_dl_created_action", "created_at", "action"),
    )

    def __repr__(self):
        return f"<DownloadLog(id={self.id}, action={self.action!r})>"