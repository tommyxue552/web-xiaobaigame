-- ============================================================
-- 模块7.7: 游戏标签(Tag)系统 - 新增 tags 和 game_tags 表
-- ============================================================

CREATE TABLE IF NOT EXISTS tags (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            VARCHAR(100)     NOT NULL              , -- 标签名称
    slug            VARCHAR(100)     NOT NULL UNIQUE       , -- URL友好标识
    description     TEXT             DEFAULT ''            , -- 标签描述
    seo_title       VARCHAR(255)     DEFAULT ''            , -- 自定义SEO标题
    seo_description VARCHAR(500)     DEFAULT ''            , -- 自定义SEO描述
    seo_keywords    VARCHAR(500)     DEFAULT ''            , -- 自定义SEO关键词
    sort_order      INTEGER          DEFAULT 0             , -- 排序
    is_active       BOOLEAN          DEFAULT 1             , -- 是否启用
    created_at      DATETIME         DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME         DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_tags_slug ON tags(slug);
CREATE INDEX IF NOT EXISTS idx_tags_is_active ON tags(is_active);

CREATE TABLE IF NOT EXISTS game_tags (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id         INTEGER         NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    tag_id          INTEGER         NOT NULL REFERENCES tags(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_gt_game_id ON game_tags(game_id);
CREATE INDEX IF NOT EXISTS idx_gt_tag_id ON game_tags(tag_id);
