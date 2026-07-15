-- ============================================================
-- 模块7.8: 下载资源优先级与智能选择系统
-- 新增字段: priority, is_primary, success_count, fail_count, last_check_at
-- 新增索引: idx_dr_priority, idx_dr_primary
-- ============================================================

-- 新增优先权字段
ALTER TABLE download_resources ADD COLUMN priority INTEGER NOT NULL DEFAULT 100;
ALTER TABLE download_resources ADD COLUMN is_primary BOOLEAN NOT NULL DEFAULT 0;
ALTER TABLE download_resources ADD COLUMN success_count INTEGER NOT NULL DEFAULT 0;
ALTER TABLE download_resources ADD COLUMN fail_count INTEGER NOT NULL DEFAULT 0;
ALTER TABLE download_resources ADD COLUMN last_check_at DATETIME NULL;

-- 新增索引
CREATE INDEX IF NOT EXISTS idx_dr_priority ON download_resources(priority);
CREATE INDEX IF NOT EXISTS idx_dr_primary ON download_resources(is_primary);