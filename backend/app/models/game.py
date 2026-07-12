"""
游戏资源模型
-----------
games 表：存储从各渠道采集的游戏资源信息。
字段设计充分考虑了后续自动采集、资源中转、AI 运营等扩展需求。
"""

from sqlalchemy import (
    Column, Integer, String, Text, Date, DateTime, Index, JSON, ForeignKey
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base


class Game(Base):
    __tablename__ = 'games'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    title = Column(String(255), nullable=False, comment='游戏标题')
    slug = Column(String(255), unique=True, nullable=False, comment='URL 友好标识')

    cover = Column(String(500), default='', comment='封面图片 URL')
    images = Column(JSON, default=list, comment='游戏截图列表（JSON 数组）')

    description = Column(Text, default='', comment='游戏简介/描述')
    system = Column(String(100), default='', comment='运行平台（Windows/Mac/Linux/Android/iOS）')
    language = Column(String(50), default='', comment='语言（中文/英文/多语言）')
    size = Column(String(50), default='', comment='文件大小（如 1.2GB）')
    version = Column(String(50), default='', comment='游戏版本号')
    publisher = Column(String(100), default='', comment='发行商')
    developer = Column(String(100), default='', comment='开发商')
    release_date = Column(Date, nullable=True, comment='发布日期')

    category_id = Column(Integer, ForeignKey('categories.id'), nullable=True, comment='分类ID')
    category = Column(String(100), default='', comment='游戏分类（冗余字段）')
    tags = Column(JSON, default=list, comment='标签列表（JSON 数组）')

    download_url = Column(String(500), default='', comment='下载链接（中转后的直链）')
    original_url = Column(String(500), default='', comment='原始来源 URL')

    crawler_source = Column(String(100), default='', comment='采集来源标识')
    crawler_url = Column(String(500), default='', comment='采集时的源页面 URL')

    views = Column(Integer, default=0, comment='游戏浏览次数')

    seo_title = Column(String(255), default='', comment='自定义 SEO 标题')
    seo_description = Column(String(500), default='', comment='自定义 SEO 描述')
    seo_keywords = Column(String(500), default='', comment='自定义 SEO 关键词')

    transfer_status = Column(String(50), default='pending', comment='中转状态')
    transfer_time = Column(DateTime, nullable=True, comment='资源中转完成时间')

    publish_status = Column(String(20), default='draft', comment='发布状态')

    created_at = Column(DateTime, server_default=func.now(), comment='创建时间')
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment='更新时间')

    download_resources = relationship("DownloadResource", back_populates="game", lazy="selectin")

    category_rel = relationship('Category', backref='games', lazy='joined')

    __table_args__ = (
        Index('idx_games_slug', 'slug'),
        Index('idx_games_category', 'category'),
        Index('idx_games_category_id', 'category_id'),
        Index('idx_games_crawler_source', 'crawler_source'),
        Index('idx_games_transfer_status', 'transfer_status'),
        Index('idx_games_publish_status', 'publish_status'),
        Index('idx_games_created_at', 'created_at'),
        Index('idx_games_title', 'title'),
        Index('idx_games_original_url', 'original_url'),
    )

    def __repr__(self):
        return f'<Game(id={self.id}, title={self.title!r})>'

