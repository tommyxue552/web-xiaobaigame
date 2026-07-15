"""Tag model - tags table for game tagging and SEO."""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.sql import func
from ..core.database import Base


class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    name = Column(String(100), nullable=False, comment="标签名称")
    slug = Column(String(100), unique=True, nullable=False, comment="URL友好标识")
    description = Column(Text, default="", comment="标签描述")
    seo_title = Column(String(255), default="", comment="自定义SEO标题")
    seo_description = Column(String(500), default="", comment="自定义SEO描述")
    seo_keywords = Column(String(500), default="", comment="自定义SEO关键词")
    sort_order = Column(Integer, default=0, comment="排序")
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    def __repr__(self):
        return f"<Tag(id={self.id}, name={self.name!r})>"
