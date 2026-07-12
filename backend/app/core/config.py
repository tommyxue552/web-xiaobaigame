"""
应用配置模块
-----------
集中管理所有环境变量和应用设置。
后续可通过 .env 文件或环境变量覆盖默认值。
"""

from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """应用全局配置"""

    # 项目基础路径
    PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent.parent.parent

    # 数据库配置（默认使用 SQLite，后续可切换为 MySQL/PostgreSQL）
    DATABASE_URL: str = ""

    @property
    def db_url(self) -> str:
        """获取数据库连接 URL，优先使用环境变量，否则使用默认 SQLite"""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        db_path = self.PROJECT_ROOT / "database" / "xiaobaigame.db"
        return f"sqlite+aiosqlite:///{db_path}"

    # 服务配置
    APP_NAME: str = "小白游戏资源站"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # 上传配置
    UPLOAD_DIR: Path = PROJECT_ROOT / "uploads"
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024  # 100MB

    # 存储配置（采集资源中转用）
    STORAGE_DIR: Path = PROJECT_ROOT / "storage"

    # CORS 配置
    ALLOWED_ORIGINS: list[str] = ["*"]

    # 预留：采集程序配置
    CRAWLER_ENABLED: bool = False
    CRAWLER_INTERVAL: int = 3600  # 采集间隔（秒）

    # 预留：AI 程序配置
    AI_ENABLED: bool = False
    AI_API_KEY: str = ""

    # 预留：资源中转配置
    TRANSFER_ENABLED: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
