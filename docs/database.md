# 数据库文档

## 概述

- **数据库类型**: SQLite
- **ORM**: SQLAlchemy 2.0 Async
- **文件路径**: `database/xiaobaigame.db`
- **Schema 文件**: `database/schema.sql`
- **迁移目录**: `database/migrations/`

数据库表在应用启动时通过 `Base.metadata.create_all` 自动创建，SQLAlchemy ORM 模型与 schema.sql 保持一致。

---

## 表关系图

```
 categories                     games
┌──────────────┐              ┌──────────────────────────┐
│ id        PK │◄─────────────│ category_id          FK  │
│ name         │              │ id                   PK  │
│ slug   UNIQUE│              │ title                    │
│ created_at   │              │ slug              UNIQUE │
└──────────────┘              │ cover                    │
                              │ images              JSON │
                              │ description              │
 download_providers           │ system / language / size │
┌──────────────┐              │ version / publisher      │
│ id        PK │              │ developer / release_date │
│ code   UNIQUE│              │ category                 │
│ name         │              │ tags                JSON │
│ icon         │              │ download_url             │
│ status       │              │ original_url             │
│ display_order│              │ crawler_source           │
│ created_at   │              │ crawler_url              │
│ updated_at   │              │ transfer_status          │
└──────┬───────┘              │ views                    │
       │                      │ seo_*                    │
       │                      │ publish_status           │
       │                      │ created_at / updated_at  │
       │                      └──────┬───────────────────┘
       │                             │
       │    download_resources       │
       │   ┌──────────────────────┐  │
       ├───│ provider_id     FK   │  │
       │   │ id              PK   │  │
       │   │ game_id         FK   │◄─┘
       │   │ provider              │
       │   │ title                 │
       │   │ origin_url            │
       │   │ my_share_url          │
       │   │ extract_code          │
       │   │ remark                │
       │   │ display_order         │
       │   │ status                │
       │   │ created_at/updated_at │
       │   └──────────┬───────────┘
       │              │
       │    download_tokens
       │   ┌──────────────────────┐
       │   │ id              PK   │
       │   │ token      UNIQUE    │
       │   │ resource_id     FK   │◄── download_resources.id (CASCADE)
       │   │ game_id         FK   │◄── games.id (CASCADE)
       │   │ provider_code        │
       │   │ status               │
       │   │ created_at/updated_at│
       │   └──────────────────────┘
       │
       │    download_logs
       │   ┌──────────────────────┐
       │   │ id              PK   │
       │   │ token                │
       │   │ resource_id          │
       │   │ game_id              │
       │   │ ip_address           │
       │   │ user_agent           │
       │   │ device_type          │
       │   │ action               │
       │   │ created_at           │
       │   └──────────────────────┘

 admin_users
┌──────────────┐
│ id        PK │
│ username     │
│ password_hash│
│ created_at   │
└──────────────┘
```

---

## 表定义

### 1. categories（游戏分类）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, AUTOINCREMENT | 主键 |
| name | VARCHAR(100) | NOT NULL | 分类名称 |
| slug | VARCHAR(100) | NOT NULL, UNIQUE | URL 友好标识 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |

**预设数据**：
| id | name | slug |
|----|------|------|
| 1 | 动作游戏 | action |
| 2 | 角色扮演 | rpg |
| 3 | 冒险游戏 | adventure |
| 4 | 模拟游戏 | simulation |
| 5 | 策略游戏 | strategy |
| 6 | 射击游戏 | shooter |
| 7 | 休闲游戏 | casual |

---

### 2. games（游戏资源）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, AUTOINCREMENT | 主键 |
| title | VARCHAR(255) | NOT NULL | 游戏标题 |
| slug | VARCHAR(255) | NOT NULL, UNIQUE | URL 标识 |
| cover | VARCHAR(500) | DEFAULT " | 封面图片 URL |
| images | TEXT | DEFAULT "[]" | 游戏截图列表（JSON 数组） |
| description | TEXT | DEFAULT " | 游戏简介 |
| system | VARCHAR(100) | DEFAULT " | 运行平台 |
| language | VARCHAR(50) | DEFAULT " | 语言 |
| size | VARCHAR(50) | DEFAULT " | 文件大小 |
| version | VARCHAR(50) | DEFAULT " | 版本号 |
| publisher | VARCHAR(100) | DEFAULT " | 发行商 |
| developer | VARCHAR(100) | DEFAULT " | 开发商 |
| release_date | DATE | NULL | 发布日期 |
| category_id | INTEGER | FK → categories.id | 分类ID |
| category | VARCHAR(100) | DEFAULT " | 分类名称（冗余） |
| tags | TEXT | DEFAULT "[]" | 标签列表（JSON 数组） |
| download_url | VARCHAR(500) | DEFAULT " | 下载链接 |
| original_url | VARCHAR(500) | DEFAULT " | 原始来源 URL |
| crawler_source | VARCHAR(100) | DEFAULT " | 采集来源标识 |
| crawler_url | VARCHAR(500) | DEFAULT " | 采集源页面 URL |
| transfer_status | VARCHAR(50) | DEFAULT "pending" | 中转状态 |
| transfer_time | DATETIME | NULL | 中转完成时间 |
| seo_title | VARCHAR(255) | DEFAULT " | 自定义 SEO 标题 |
| seo_description | VARCHAR(500) | DEFAULT " | 自定义 SEO 描述 |
| seo_keywords | VARCHAR(500) | DEFAULT " | 自定义 SEO 关键词 |
| views | INTEGER | DEFAULT 0 | 浏览计数 |
| publish_status | VARCHAR(20) | DEFAULT "draft" | 发布状态：draft / published |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 更新时间 |

**索引**: slug, category, category_id, crawler_source, transfer_status, publish_status, created_at, title, original_url

---

### 3. download_resources（下载资源）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, AUTOINCREMENT | 主键 |
| game_id | INTEGER | FK → games.id (CASCADE) | 关联游戏 |
| provider | VARCHAR(20) | NOT NULL, DEFAULT "baidu" | 网盘代码（保留字段） |
| provider_id | INTEGER | FK → download_providers.id (SET NULL) | 关联渠道ID |
| title | VARCHAR(255) | DEFAULT " | 资源标题 |
| origin_url | VARCHAR(1000) | DEFAULT " | 原始来源 URL |
| my_share_url | VARCHAR(1000) | DEFAULT " | 我的分享链接（展示优先） |
| extract_code | VARCHAR(20) | DEFAULT " | 提取码 |
| remark | TEXT | DEFAULT " | 备注 |
| display_order | INTEGER | DEFAULT 0 | 显示排序 |
| status | VARCHAR(20) | DEFAULT "active" | pending / active / disabled / invalid |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 更新时间 |

**索引**: game_id, provider, provider_id, status

---

### 4. download_providers（下载渠道）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, AUTOINCREMENT | 主键 |
| code | VARCHAR(20) | NOT NULL, UNIQUE | 渠道代码 |
| name | VARCHAR(50) | NOT NULL | 渠道名称 |
| icon | VARCHAR(255) | DEFAULT " | 图标 |
| status | VARCHAR(20) | DEFAULT "active" | active / disabled |
| display_order | INTEGER | DEFAULT 0 | 排序 |
| remark | TEXT | DEFAULT " | 备注 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 更新时间 |

**预设数据**：

| id | code | name |
|----|------|------|
| 1 | baidu | 百度网盘 |
| 2 | quark | 夸克网盘 |
| 3 | alipan | 阿里云盘 |
| 4 | 115 | 115网盘 |
| 5 | xunlei | 迅雷云盘 |
| 6 | uc | UC网盘 |
| 7 | mobile | 中国移动云盘 |
| 8 | tianyi | 天翼云盘 |

**索引**: code, status

---

### 5. download_tokens（下载 Token，模块7.4）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, AUTOINCREMENT | 主键 |
| token | VARCHAR(64) | NOT NULL, UNIQUE | 唯一 Token（secrets.token_urlsafe(32)） |
| resource_id | INTEGER | FK → download_resources.id (CASCADE) | 关联下载资源 |
| game_id | INTEGER | FK → games.id (CASCADE) | 关联游戏（冗余） |
| provider_code | VARCHAR(20) | DEFAULT " | 网盘代码 |
| status | VARCHAR(20) | DEFAULT "active" | active / disabled |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 更新时间 |

**唯一约束**: `UNIQUE(resource_id, status)` — 每个资源同一状态下只有一个有效 Token

**索引**: token, resource_id, game_id

---

### 6. download_logs（下载日志，模块7.4）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, AUTOINCREMENT | 主键 |
| token | VARCHAR(64) | DEFAULT " | 下载 Token |
| resource_id | INTEGER | NULL | 关联资源 ID |
| game_id | INTEGER | NULL | 关联游戏 ID |
| ip_address | VARCHAR(45) | DEFAULT " | 用户 IP |
| user_agent | TEXT | DEFAULT " | User-Agent |
| device_type | VARCHAR(20) | DEFAULT " | pc / mobile / unknown |
| action | VARCHAR(20) | DEFAULT "view" | view(查看下载页) / redirect(跳转下载) |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |

**索引**: token, created_at, action

---

### 7. admin_users（管理员用户）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, AUTOINCREMENT | 主键 |
| username | VARCHAR(50) | NOT NULL, UNIQUE | 用户名 |
| password_hash | VARCHAR(255) | NOT NULL | bcrypt 密码哈希 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |

---

## 关系说明

| 关系 | 方向 | 类型 |
|------|------|------|
| games → categories | 多对一 | category_id FK → categories.id |
| games → download_resources | 一对多 | games.download_resources 反向关系 |
| download_resources → download_providers | 多对一 | provider_id FK → download_providers.id |
| download_tokens → download_resources | 多对一 | resource_id FK（CASCADE 删除） |
| download_tokens → games | 多对一 | game_id FK（CASCADE 删除，冗余加速查询） |

## 迁移记录

| 文件 | 说明 |
|------|------|
| `migrations/007_04_download_tokens.sql` | 下载 Token 表创建 |
| `migrations/007_04_01_download_tokens_constraint.sql` | Token 唯一约束更新 |
