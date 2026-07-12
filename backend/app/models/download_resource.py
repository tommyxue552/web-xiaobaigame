"""
下载资源模型
-----------
download_resources 表 - 存储游戏的下载资源信息。
支持多网盘，每个游戏可以有多个下载资源。
展示时优先使用 my_share_url。
provider_id 关联 download_providers 表。
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base


class DownloadResource(Base):
    __tablename__ = "download_resources"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="资源ID")
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
        comment="网盘类型（保留字段，兼容旧数据）",
    )
    provider_id = Column(
        Integer,
        ForeignKey("download_providers.id", ondelete="SET NULL"),
        nullable=True,
        comment="关联下载渠道ID",
    )
    title = Column(String(255), default="", comment="资源标题，如 v1.2 版本")
    origin_url = Column(
        String(1000), default="", comment="原始来源URL，用于采集器更新"
    )
    my_share_url = Column(
        String(1000), default="", comment="我的分享链接，网站展示时优先使用"
    )
    extract_code = Column(String(20), default="", comment="提取码")
    remark = Column(Text, default="", comment="备注信息")
    display_order = Column(
        Integer, default=0, comment="显示排序，数字越小越靠前"
    )
    status = Column(
        String(20),
        default="active",
        comment="状态：pending/active/disabled/invalid",
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

    # 关联游戏表
    game = relationship("Game", back_populates="download_resources")
    # 关联下载渠道表
    provider_rel = relationship("DownloadProvider", back_populates="download_resources", lazy="joined")

    __table_args__ = (
        Index("idx_dr_game_id", "game_id"),
        Index("idx_dr_provider", "provider"),
        Index("idx_dr_provider_id", "provider_id"),
        Index("idx_dr_status", "status"),
    )

    def __repr__(self):
        return f"<DownloadResource(id={self.id}, game_id={self.game_id}, provider={self.provider!r})>"
