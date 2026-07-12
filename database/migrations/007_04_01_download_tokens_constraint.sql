-- -----------------------------------------------------------
-- 下载 Token 唯一约束（模块7.4.1 补丁）
-- 确保同一资源在同一状态下只有一个有效 Token
-- -----------------------------------------------------------

-- 说明：
--   本 migration 在 (resource_id, status) 上创建唯一索引，
--   与 UNIQUE 约束在 SQLite 中等价。
--   已有数据经检查无重复，直接创建即可。
--   如果未来执行时存在重复数据，需要先清理：
--     DELETE FROM download_tokens WHERE id NOT IN (
--       SELECT MIN(id) FROM download_tokens GROUP BY resource_id, status
--     );

CREATE UNIQUE INDEX IF NOT EXISTS idx_dt_resource_status
    ON download_tokens(resource_id, status);
