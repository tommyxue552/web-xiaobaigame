"""
下载 Token 模型（模块7.4）
-----------------------
download_tokens 表：每个下载资源对应一个唯一 Token。
Token 永久有效，更换资源链接时无需重新生成二维码。
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base


class DownloadToken(Base):
    __tablename__ = "download_tokens"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    token = Column(String(64), unique=True, nullable=False, comment="唯一下载Token")
    resource_id = Column(
        Integer,
        ForeignKey("download_resources.id", ondelete="CASCADE"),
        nullable=False,
        comment="关联下载资源ID",
    )
    game_id = Column(
        Integer,
        ForeignKey("games.id", ondelete="CASCADE"),
        nullable=False,
        comment="关联游戏ID（冗余加速查询）",
    )
    provider_code = Column(String(20), default="", comment="网盘代码")
    status = Column(
        String(20), default="active", comment="active/disabled"
    )
    created_at = Column(
        DateTime, server_default=func.now(), comment="创建时间"
    )
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        comment="更新时间",
    )

    resource = relationship("DownloadResource", lazy="joined")
    game = relationship("Game", lazy="joined")

    __table_args__ = (
        Index("idx_dt_token", "token"),
        Index("idx_dt_resource", "resource_id"),
        Index("idx_dt_game", "game_id"),
    )

    def __repr__(self):
        return f"<DownloadToken(id={self.id}, token={self.token!r})>"
