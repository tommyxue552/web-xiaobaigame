# -*- coding: utf-8 -*-
"""
??????
-----------
????????????????
????? .env ?????????????
"""

from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """??????"""

    # ??????
    PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent.parent.parent

    # ?????
    DATABASE_URL: str = ""

    @property
    def db_url(self) -> str:
        """??????? URL"""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        db_path = self.PROJECT_ROOT / "database" / "xiaobaigame.db"
        return f"sqlite+aiosqlite:///{db_path}"

    # ????
    APP_NAME: str = "???????"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # ????
    UPLOAD_DIR: Path = PROJECT_ROOT / "uploads"
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024

    # ????
    STORAGE_DIR: Path = PROJECT_ROOT / "storage"

    # CORS ??
    ALLOWED_ORIGINS: list[str] = ["*"]

    # JWT ??
    JWT_SECRET_KEY: str = "xiaobaigame-admin-secret-key-change-in-production-2026"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 480

    # ??????????
    CRAWLER_ENABLED: bool = False
    CRAWLER_INTERVAL: int = 3600

    # AI ????????
    AI_ENABLED: bool = False
    AI_API_KEY: str = ""

    # ??????????
    TRANSFER_ENABLED: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
