-- ============================================================
-- 灏忕櫧娓告垙璧勬簮绔?- 鏁版嵁搴撳垵濮嬪寲鑴氭湰
-- ============================================================
-- 鏁版嵁搴擄細SQLite锛堝彲杩佺Щ鑷?MySQL/PostgreSQL锛?
-- 鏇存柊鏃堕棿锛?026-07-12
-- ============================================================

-- -----------------------------------------------------------
-- 鍒嗙被琛?
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS categories (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            VARCHAR(100)     NOT NULL              , -- 鍒嗙被鍚嶇О
    slug            VARCHAR(100)     NOT NULL UNIQUE       , -- URL 鍙嬪ソ鏍囪瘑
    created_at      DATETIME         DEFAULT CURRENT_TIMESTAMP
);

-- -----------------------------------------------------------
-- 娓告垙璧勬簮涓昏〃
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

    category_id     INTEGER         REFERENCES categories(id) , -- 鍒嗙被澶栭敭
    category        VARCHAR(100)     DEFAULT ''            , -- 鍒嗙被鍚嶇О锛堝啑浣欙級
    tags            TEXT             DEFAULT '[]'          ,

    download_url    VARCHAR(500)     DEFAULT ''            ,
    original_url    VARCHAR(500)     DEFAULT ''            ,

    crawler_source  VARCHAR(100)     DEFAULT ''            ,
    crawler_url     VARCHAR(500)     DEFAULT ''            ,

    transfer_status VARCHAR(50)      DEFAULT 'pending'     ,
    transfer_time   DATETIME         NULL                  ,

    -- SEO 浼樺寲瀛楁
    seo_title       VARCHAR(255)     DEFAULT ''            , -- 鑷畾涔?SEO 鏍囬
    seo_description VARCHAR(500)     DEFAULT ''            , -- 鑷畾涔?SEO 鎻忚堪
    seo_keywords    VARCHAR(500)     DEFAULT ''            , -- 鑷畾涔?SEO 鍏抽敭璇?

    -- 璁块棶缁熻
    views           INTEGER          DEFAULT 0             , -- 娓告垙娴忚娆℃暟

    publish_status  VARCHAR(20)      DEFAULT 'draft'       ,

    created_at      DATETIME         DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME         DEFAULT CURRENT_TIMESTAMP
);

-- -----------------------------------------------------------
-- 绱㈠紩
-- -----------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_games_slug             ON games(slug);
CREATE INDEX IF NOT EXISTS idx_games_category         ON games(category);
CREATE INDEX IF NOT EXISTS idx_games_category_id      ON games(category_id);
CREATE INDEX IF NOT EXISTS idx_games_crawler_source   ON games(crawler_source);
CREATE INDEX IF NOT EXISTS idx_games_transfer_status  ON games(transfer_status);
CREATE INDEX IF NOT EXISTS idx_games_publish_status   ON games(publish_status);
CREATE INDEX IF NOT EXISTS idx_games_created_at       ON games(created_at);
CREATE INDEX IF NOT EXISTS idx_games_title            ON games(title);
CREATE INDEX IF NOT EXISTS idx_games_original_url   ON games(original_url);

-- -----------------------------------------------------------
-- 绉嶅瓙鏁版嵁锛氬垎绫?
-- -----------------------------------------------------------
INSERT OR IGNORE INTO categories (id, name, slug) VALUES (1, '鍔ㄤ綔娓告垙', 'action');
INSERT OR IGNORE INTO categories (id, name, slug) VALUES (2, '瑙掕壊鎵紨', 'rpg');
INSERT OR IGNORE INTO categories (id, name, slug) VALUES (3, '鍐掗櫓娓告垙', 'adventure');
INSERT OR IGNORE INTO categories (id, name, slug) VALUES (4, '妯℃嫙缁忚惀', 'simulation');
INSERT OR IGNORE INTO categories (id, name, slug) VALUES (5, '绛栫暐娓告垙', 'strategy');
INSERT OR IGNORE INTO categories (id, name, slug) VALUES (6, '灏勫嚮娓告垙', 'shooter');
INSERT OR IGNORE INTO categories (id, name, slug) VALUES (7, '浼戦棽娓告垙', 'casual');


-- -----------------------------------------------------------
-- 绠＄悊鍛樿〃
-- -----------------------------------------------------------
-- -----------------------------------------------------------
-- 下载资源表（多网盘支持）
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS download_resources (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id         INTEGER         NOT NULL REFERENCES games(id) ON DELETE CASCADE , -- 关联游戏
    provider        VARCHAR(20)     NOT NULL DEFAULT 'baidu'   , -- 网盘类型：baidu/quark/alipan/115
    title           VARCHAR(255)    DEFAULT ''                , -- 资源标题
    origin_url      VARCHAR(1000)   DEFAULT ''                , -- 原始来源URL
    my_share_url    VARCHAR(1000)   DEFAULT ''                , -- 我的分享链接
    extract_code    VARCHAR(20)     DEFAULT ''                , -- 提取码
    remark          TEXT            DEFAULT ''                , -- 备注
    display_order   INTEGER         DEFAULT 0                   , -- 显示排序
    priority        INTEGER         NOT NULL DEFAULT 100       , -- 下载优先级(越大越优先)
    is_primary      BOOLEAN         NOT NULL DEFAULT 0         , -- 是否默认资源
    success_count   INTEGER         NOT NULL DEFAULT 0         , -- 成功跳转次数
    fail_count      INTEGER         NOT NULL DEFAULT 0         , -- 失败次数
    last_check_at   DATETIME        NULL                        , -- 最后检查时间
    status          VARCHAR(20)     DEFAULT 'active'          , -- pending/active/disabled/invalid
    created_at      DATETIME        DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME        DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_dr_game_id   ON download_resources(game_id);
CREATE INDEX IF NOT EXISTS idx_dr_provider  ON download_resources(provider);
CREATE INDEX IF NOT EXISTS idx_dr_status    ON download_resources(status);
CREATE INDEX IF NOT EXISTS idx_dr_priority  ON download_resources(priority);
CREATE INDEX IF NOT EXISTS idx_dr_primary   ON download_resources(is_primary);

-- -----------------------------------------------------------
-- 下载渠道表
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS download_providers (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    code            VARCHAR(20)     NOT NULL UNIQUE       , -- 渠道代码：baidu/quark/alipan/115/xunlei/uc/mobile/tianyi
    name            VARCHAR(50)     NOT NULL              , -- 渠道名称：百度网盘/夸克网盘...
    icon            VARCHAR(255)    DEFAULT ''            , -- 图标
    status          VARCHAR(20)     DEFAULT 'active'      , -- active/disabled
    display_order   INTEGER         DEFAULT 0             , -- 排序
    remark          TEXT            DEFAULT ''            , -- 备注
    created_at      DATETIME        DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME        DEFAULT CURRENT_TIMESTAMP
);

-- 渠道种子数据
INSERT OR IGNORE INTO download_providers (id, code, name, icon, status, display_order, remark) VALUES (1, 'baidu', '百度网盘', '', 'active', 1, '');
INSERT OR IGNORE INTO download_providers (id, code, name, icon, status, display_order, remark) VALUES (2, 'quark', '夸克网盘', '', 'active', 2, '');
INSERT OR IGNORE INTO download_providers (id, code, name, icon, status, display_order, remark) VALUES (3, 'alipan', '阿里云盘', '', 'active', 3, '');
INSERT OR IGNORE INTO download_providers (id, code, name, icon, status, display_order, remark) VALUES (4, '115', '115网盘', '', 'active', 4, '');
INSERT OR IGNORE INTO download_providers (id, code, name, icon, status, display_order, remark) VALUES (5, 'xunlei', '迅雷云盘', '', 'active', 5, '');
INSERT OR IGNORE INTO download_providers (id, code, name, icon, status, display_order, remark) VALUES (6, 'uc', 'UC网盘', '', 'active', 6, '');
INSERT OR IGNORE INTO download_providers (id, code, name, icon, status, display_order, remark) VALUES (7, 'mobile', '中国移动云盘', '', 'active', 7, '');
INSERT OR IGNORE INTO download_providers (id, code, name, icon, status, display_order, remark) VALUES (8, 'tianyi', '天翼云盘', '', 'active', 8, '');

CREATE INDEX IF NOT EXISTS idx_dp_code   ON download_providers(code);
CREATE INDEX IF NOT EXISTS idx_dp_status ON download_providers(status);

CREATE TABLE IF NOT EXISTS admin_users (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    username        VARCHAR(50)      NOT NULL UNIQUE       ,
    password_hash   VARCHAR(255)     NOT NULL              ,
    created_at      DATETIME         DEFAULT CURRENT_TIMESTAMP
);





-- -----------------------------------------------------------
-- 下载 Token 表（模块7.4）
-- 每个下载资源对应一个唯一 Token，Token 永久有效
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS download_tokens (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    token           VARCHAR(64)     NOT NULL UNIQUE       , -- 唯一下载 Token
    resource_id     INTEGER         NOT NULL REFERENCES download_resources(id) ON DELETE CASCADE , -- 关联下载资源
    game_id         INTEGER         NOT NULL REFERENCES games(id) ON DELETE CASCADE             , -- 关联游戏（冗余，加速查询）
    provider_code   VARCHAR(20)     DEFAULT """"           , -- 网盘代码
    status          VARCHAR(20)     DEFAULT ""active""     , -- active/disabled
    created_at      DATETIME        DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME        DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_dt_token      ON download_tokens(token);
CREATE INDEX IF NOT EXISTS idx_dt_resource   ON download_tokens(resource_id);
CREATE INDEX IF NOT EXISTS idx_dt_game       ON download_tokens(game_id);

-- -----------------------------------------------------------
-- 下载日志表（模块7.4 预留）
-- 为后续下载统计模块做准备
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS download_logs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    token           VARCHAR(64)     DEFAULT """"           , -- 下载 Token
    resource_id     INTEGER         DEFAULT NULL            , -- 关联下载资源
    game_id         INTEGER         DEFAULT NULL            , -- 关联游戏
    ip_address      VARCHAR(45)     DEFAULT """"           , -- 用户 IP
    user_agent      TEXT            DEFAULT """"           , -- User-Agent
    device_type     VARCHAR(20)     DEFAULT """"           , -- pc/mobile/unknown
    action          VARCHAR(20)     DEFAULT ""view""       , -- view(查看下载页)/redirect(跳转下载)
    created_at      DATETIME        DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_dl_token    ON download_logs(token);
CREATE INDEX IF NOT EXISTS idx_dl_created  ON download_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_dl_action   ON download_logs(action);
CREATE INDEX IF NOT EXISTS idx_dl_game_id      ON download_logs(game_id);
CREATE INDEX IF NOT EXISTS idx_dl_provider_id  ON download_logs(provider_id);
CREATE INDEX IF NOT EXISTS idx_dl_created_action ON download_logs(created_at, action);


-- -----------------------------------------------------------
-- 游戏标签表（模块7.7）
-- -----------------------------------------------------------
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

-- -----------------------------------------------------------
-- 游戏-标签关联表（模块7.7）
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS game_tags (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id         INTEGER         NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    tag_id          INTEGER         NOT NULL REFERENCES tags(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_gt_game_id ON game_tags(game_id);
CREATE INDEX IF NOT EXISTS idx_gt_tag_id ON game_tags(tag_id);
