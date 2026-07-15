"""GameTag association model - many-to-many between games and tags."""
from sqlalchemy import Column, Integer, ForeignKey, Index
from ..core.database import Base


class GameTag(Base):
    __tablename__ = "game_tags"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    game_id = Column(Integer, ForeignKey("games.id", ondelete="CASCADE"), nullable=False, comment="游戏ID")
    tag_id = Column(Integer, ForeignKey("tags.id", ondelete="CASCADE"), nullable=False, comment="标签ID")

    __table_args__ = (
        Index("idx_gt_game_id", "game_id"),
        Index("idx_gt_tag_id", "tag_id"),
    )

    def __repr__(self):
        return f"<GameTag(game_id={self.game_id}, tag_id={self.tag_id})>"
