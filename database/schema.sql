-- ============================================================
-- 小白游戏资源站 - 数据库初始化脚本
-- ============================================================
-- 数据库：SQLite（可迁移至 MySQL/PostgreSQL）
-- 创建时间：2026-07-11
--
-- 注意：
-- 使用 SQLAlchemy ORM 时，表结构由 models/game.py 定义，
-- 启动应用时会自动创建表。此文件作为参考文档和手动建表用。
-- ============================================================

-- -----------------------------------------------------------
-- 游戏资源主表
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS games (
    -- 基础标识
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    title           VARCHAR(255)     NOT NULL              , -- 游戏标题
    slug            VARCHAR(255)     NOT NULL UNIQUE       , -- URL 友好标识

    -- 媒体资源
    cover           VARCHAR(500)     DEFAULT ''            , -- 封面图片 URL
    images          TEXT             DEFAULT '[]'          , -- 游戏截图（JSON 数组）

    -- 游戏详情
    description     TEXT             DEFAULT ''            , -- 游戏简介
    system          VARCHAR(100)     DEFAULT ''            , -- 运行平台
    language        VARCHAR(50)      DEFAULT ''            , -- 语言
    size            VARCHAR(50)      DEFAULT ''            , -- 文件大小
    version         VARCHAR(50)      DEFAULT ''            , -- 版本号
    publisher       VARCHAR(100)     DEFAULT ''            , -- 发行商
    developer       VARCHAR(100)     DEFAULT ''            , -- 开发商
    release_date    DATE             NULL                  , -- 发布日期

    -- 分类与标签
    category        VARCHAR(100)     DEFAULT ''            , -- 游戏分类
    tags            TEXT             DEFAULT '[]'          , -- 标签列表（JSON 数组）

    -- 下载与来源
    download_url    VARCHAR(500)     DEFAULT ''            , -- 下载链接（中转后直链）
    original_url    VARCHAR(500)     DEFAULT ''            , -- 原始来源 URL

    -- 采集追踪（预留）
    crawler_source  VARCHAR(100)     DEFAULT ''            , -- 采集来源标识
    crawler_url     VARCHAR(500)     DEFAULT ''            , -- 采集源页面 URL

    -- 资源中转（预留）
    transfer_status VARCHAR(50)      DEFAULT 'pending'     , -- 中转状态
    transfer_time   DATETIME         NULL                  , -- 中转完成时间

    -- 发布控制
    publish_status  VARCHAR(20)      DEFAULT 'draft'       , -- 发布状态

    -- 时间戳
    created_at      DATETIME         DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME         DEFAULT CURRENT_TIMESTAMP
);

-- -----------------------------------------------------------
-- 索引
-- -----------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_games_slug             ON games(slug);
CREATE INDEX IF NOT EXISTS idx_games_category         ON games(category);
CREATE INDEX IF NOT EXISTS idx_games_crawler_source   ON games(crawler_source);
CREATE INDEX IF NOT EXISTS idx_games_transfer_status  ON games(transfer_status);
CREATE INDEX IF NOT EXISTS idx_games_publish_status   ON games(publish_status);
CREATE INDEX IF NOT EXISTS idx_games_created_at       ON games(created_at);
CREATE INDEX IF NOT EXISTS idx_games_title            ON games(title);
