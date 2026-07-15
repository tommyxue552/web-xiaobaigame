-- ============================================================
-- 迁移 007_06: 下载日志增强（模块7.6 下载统计系统）
-- ============================================================
-- 新增字段:
--   provider_id  - 关联下载渠道，用于渠道统计分析
--   referer      - HTTP Referer，用于用户来源分析
-- 新增索引:
--   idx_dl_game_id     - 按游戏统计（热门游戏排行）
--   idx_dl_provider_id - 按渠道统计（网盘渠道分析）
--   idx_dl_created_action - 按时间+事件类型复合索引（趋势查询加速）
-- ============================================================

ALTER TABLE download_logs ADD COLUMN provider_id INTEGER DEFAULT NULL;
ALTER TABLE download_logs ADD COLUMN referer VARCHAR(500) DEFAULT """";

CREATE INDEX IF NOT EXISTS idx_dl_game_id ON download_logs(game_id);
CREATE INDEX IF NOT EXISTS idx_dl_provider_id ON download_logs(provider_id);
CREATE INDEX IF NOT EXISTS idx_dl_created_action ON download_logs(created_at, action);
