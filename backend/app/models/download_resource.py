"""
??????
-----------
download_resources ???????????????
??????????????????????????????115??
??????????? my_share_url?
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base


class DownloadResource(Base):
    __tablename__ = "download_resources"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="??ID")
    game_id = Column(
        Integer,
        ForeignKey("games.id", ondelete="CASCADE"),
        nullable=False,
        comment="????ID",
    )
    provider = Column(
        String(20),
        nullable=False,
        default="baidu",
        comment="?????baidu/quark/alipan/115",
    )
    title = Column(String(255), default="", comment="???????????v1.2?")
    origin_url = Column(
        String(1000), default="", comment="????URL???????????"
    )
    my_share_url = Column(
        String(1000), default="", comment="???????????????"
    )
    extract_code = Column(String(20), default="", comment="???")
    remark = Column(Text, default="", comment="????")
    display_order = Column(
        Integer, default=0, comment="????????????"
    )
    status = Column(
        String(20),
        default="active",
        comment="???pending/active/disabled/invalid",
    )
    created_at = Column(
        DateTime, server_default=func.now(), comment="????"
    )
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        comment="????",
    )

    # ??????????????????
    game = relationship("Game", back_populates="download_resources")

    __table_args__ = (
        Index("idx_dr_game_id", "game_id"),
        Index("idx_dr_provider", "provider"),
        Index("idx_dr_status", "status"),
    )

    def __repr__(self):
        return f"<DownloadResource(id={self.id}, game_id={self.game_id}, provider={self.provider!r})>"
