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
