"""
下载渠道模型
-----------
download_providers 表：管理下载渠道（百度网盘/夸克网盘 等）。
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base


class DownloadProvider(Base):
    __tablename__ = "download_providers"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    code = Column(String(20), unique=True, nullable=False, comment="渠道代码：baidu/quark/alipan/115/xunlei/uc/mobile/tianyi")
    name = Column(String(50), nullable=False, comment="渠道名称：百度网盘/夸克网盘...")
    icon = Column(String(255), default="", comment="图标")
    status = Column(String(20), default="active", comment="active/disabled")
    display_order = Column(Integer, default=0, comment="排序")
    remark = Column(Text, default="", comment="备注")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    download_resources = relationship("DownloadResource", back_populates="provider_rel", lazy="selectin")

    __table_args__ = (
        Index("idx_dp_code", "code"),
        Index("idx_dp_status", "status"),
    )

    def __repr__(self):
        return f"<DownloadProvider(id={self.id}, code={self.code!r}, name={self.name!r})>"
