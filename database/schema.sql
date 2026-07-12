-- ============================================================
-- 小白游戏资源站 - 数据库初始化脚本
-- ============================================================
-- 数据库：SQLite（可迁移至 MySQL/PostgreSQL）
-- 更新时间：2026-07-12
-- ============================================================

-- -----------------------------------------------------------
-- 分类表
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS categories (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            VARCHAR(100)     NOT NULL              , -- 分类名称
    slug            VARCHAR(100)     NOT NULL UNIQUE       , -- URL 友好标识
    created_at      DATETIME         DEFAULT CURRENT_TIMESTAMP
);

-- -----------------------------------------------------------
-- 游戏资源主表
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS games (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    title           VARCHAR(255)     NOT NULL              ,
    slug            VARCHAR(255)     NOT NULL UNIQUE       ,

    cover           VARCHAR(500)     DEFAULT ''            ,
    images          TEXT             DEFAULT '[]'          ,

    description     TEXT             DEFAULT ''            ,
    system          VARCHAR(100)     DEFAULT ''            ,
    language        VARCHAR(50)      DEFAULT ''            ,
    size            VARCHAR(50)      DEFAULT ''            ,
    version         VARCHAR(50)      DEFAULT ''            ,
    publisher       VARCHAR(100)     DEFAULT ''            ,
    developer       VARCHAR(100)     DEFAULT ''            ,
    release_date    DATE             NULL                  ,

    category_id     INTEGER         REFERENCES categories(id) , -- 分类外键
    category        VARCHAR(100)     DEFAULT ''            , -- 分类名称（冗余）
    tags            TEXT             DEFAULT '[]'          ,

    download_url    VARCHAR(500)     DEFAULT ''            ,
    original_url    VARCHAR(500)     DEFAULT ''            ,

    crawler_source  VARCHAR(100)     DEFAULT ''            ,
    crawler_url     VARCHAR(500)     DEFAULT ''            ,

    transfer_status VARCHAR(50)      DEFAULT 'pending'     ,
    transfer_time   DATETIME         NULL                  ,

    publish_status  VARCHAR(20)      DEFAULT 'draft'       ,

    created_at      DATETIME         DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME         DEFAULT CURRENT_TIMESTAMP
);

-- -----------------------------------------------------------
-- 索引
-- -----------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_games_slug             ON games(slug);
CREATE INDEX IF NOT EXISTS idx_games_category         ON games(category);
CREATE INDEX IF NOT EXISTS idx_games_category_id      ON games(category_id);
CREATE INDEX IF NOT EXISTS idx_games_crawler_source   ON games(crawler_source);
CREATE INDEX IF NOT EXISTS idx_games_transfer_status  ON games(transfer_status);
CREATE INDEX IF NOT EXISTS idx_games_publish_status   ON games(publish_status);
CREATE INDEX IF NOT EXISTS idx_games_created_at       ON games(created_at);
CREATE INDEX IF NOT EXISTS idx_games_title            ON games(title);

-- -----------------------------------------------------------
-- 种子数据：分类
-- -----------------------------------------------------------
INSERT OR IGNORE INTO categories (id, name, slug) VALUES (1, '动作游戏', 'action');
INSERT OR IGNORE INTO categories (id, name, slug) VALUES (2, '角色扮演', 'rpg');
INSERT OR IGNORE INTO categories (id, name, slug) VALUES (3, '冒险游戏', 'adventure');
INSERT OR IGNORE INTO categories (id, name, slug) VALUES (4, '模拟经营', 'simulation');
INSERT OR IGNORE INTO categories (id, name, slug) VALUES (5, '策略游戏', 'strategy');
INSERT OR IGNORE INTO categories (id, name, slug) VALUES (6, '射击游戏', 'shooter');
INSERT OR IGNORE INTO categories (id, name, slug) VALUES (7, '休闲游戏', 'casual');

-- -----------------------------------------------------------
-- 管理员表
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS admin_users (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    username        VARCHAR(50)      NOT NULL UNIQUE       ,
    password_hash   VARCHAR(255)     NOT NULL              ,
    created_at      DATETIME         DEFAULT CURRENT_TIMESTAMP
);
