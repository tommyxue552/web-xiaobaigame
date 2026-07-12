"""下载资源模型
-----------
download_resources 表：存储游戏的多网盘下载资源。
一个游戏可以关联多个下载资源，支持百度网盘、夸克、阿里云盘、115等。
后续网盘中转系统会更新 my_share_url。
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base


class DownloadResource(Base):
    __tablename__ = "download_resources"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    game_id = Column(
        Integer,
        ForeignKey("games.id", ondelete="CASCADE"),
        nullable=False,
        comment="关联游戏ID",
    )
    provider = Column(
        String(20),
        nullable=False,
        default="baidu",
        comment="网盘类型：baidu/quark/alipan/115",
    )
    title = Column(String(255), default="", comment="资源标题（如：百度网盘v1.2）")
    origin_url = Column(
        String(1000), default="", comment="原始来源URL，后续供采集器更新使用"
    )
    my_share_url = Column(
        String(1000), default="", comment="我的分享链接，网站展示优先使用"
    )
    extract_code = Column(String(20), default="", comment="提取码")
    status = Column(
        String(20), default="active", comment="状态：active/inactive/broken"
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

    # 反向关系（可选，用于从资源反查游戏）
    game = relationship("Game", back_populates="download_resources")

    __table_args__ = (
        Index("idx_dr_game_id", "game_id"),
        Index("idx_dr_provider", "provider"),
        Index("idx_dr_status", "status"),
    )

    def __repr__(self):
        return f"<DownloadResource(id={self.id}, game_id={self.game_id}, provider={self.provider!r})>"
