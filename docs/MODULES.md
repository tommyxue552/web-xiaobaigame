# 模块开发状态

## 当前版本: v0.7.7

---

## 模块进度总览

| 模块 | 名称 | 状态 | 说明 |
|------|------|------|------|
| 模块1 | 项目初始化 | ✅ 完成 | 项目骨架、FastAPI 入口、配置管理 |
| 模块2 | 数据模型 | ✅ 完成 | 7张数据表、ORM 模型、数据库初始化 |
| 模块3 | 游戏公开 API | ✅ 完成 | 游戏列表、详情、分类、Slug 查询 |
| 模块4 | 后台管理系统 | ✅ 完成 | 登录认证、游戏 CRUD、分类 CRUD、仪表盘 |
| 模块5 | SEO 优化 | ✅ 完成 | SSR 详情页、sitemap.xml、robots.txt、JSON-LD |
| 模块6 | 采集接口 | ✅ 完成 | Collector-Key 认证、批量导入、original_url 去重 |
| 模块7.1 | 下载资源管理 | ✅ 完成 | 下载资源 CRUD、游戏关联、网盘类型 |
| 模块7.2 | 下载渠道管理 | ✅ 完成 | 渠道 CRUD、8种预设渠道、使用量统计 |
| 模块7.3 | 前端下载展示 | ✅ 完成 | 游戏详情页多渠道按钮、下载二维码页 |
| 模块7.4 | 下载控制器 | ✅ 完成 | Token 化下载、设备分流（PC/Mobile）、下载日志
| 模块7.5 | SEO 基础系统 | ✅ 完成 | 动态 SITE_URL、sitemap 分类+分页索引、SEO meta 修复 |
| 模块7.6 | 下载统计系统 | ✅ 完成 |
| 模块7.7 | 游戏标签(Tag)与标签SEO | ✅ 完成 | Tag管理、Tag页面、SEO、相关推荐 | 下载日志增强、统计 API、后台统计面板 |
| 模块9 | AI 运营 | 🔴 预留 | 接口已定义，返回 501 |
| 模块10 | Docker 部署 | ✅ 完成 | Dockerfile + docker-compose.yml |

---

## 模块详情

### 模块1: 项目初始化

**状态**: ✅ 完成

- FastAPI 应用入口 (`backend/app/main.py`)
- 配置管理 (`backend/app/core/config.py`)，支持 `.env` 文件
- 异步数据库引擎 (`backend/app/core/database.py`)
- CORS 中间件配置
- 静态文件挂载（frontend、admin、uploads）
- 生命周期事件（启动时自动建表）
- Docker 容器化配置

### 模块2: 数据模型

**状态**: ✅ 完成

7 张数据表的 ORM 模型：

| 表 | 模型文件 | 说明 |
|----|----------|------|
| games | `models/game.py` | 游戏资源，含 SEO、采集、中转字段 |
| categories | `models/category.py` | 游戏分类，与 games 外键关联 |
| download_resources | `models/download_resource.py` | 下载资源，关联游戏和渠道 |
| download_providers | `models/download_provider.py` | 下载渠道（百度网盘/夸克等） |
| download_tokens | `models/download_token.py` | 下载 Token（模块7.4） |
| download_logs | `models/download_log.py` | 下载日志（模块7.4） |
| admin_users | `models/admin_user.py` | 管理员用户 |

### 模块3: 游戏公开 API

**状态**: ✅ 完成

- `GET /api/categories` — 分类列表
- `GET /api/games` — 游戏列表（分页 + 分类筛选 + 关键词搜索 + 排序）
- `GET /api/game/{id}` — 游戏详情（含下载资源列表、浏览量+1）
- `GET /api/game/slug/{slug}` — 通过 Slug 获取游戏详情
- `GET /api/qrcode/{game_id}` — 生成下载二维码（PNG）
- `GET /api/game/{game_id}/download-resources` — 游戏下载资源列表

### 模块4: 后台管理系统

**状态**: ✅ 完成

**认证**:
- `POST /api/admin/login` — 管理员登录，返回 JWT
- `GET /api/admin/me` — 获取当前登录管理员信息

**游戏管理**:
- `GET /api/admin/games` — 游戏列表（支持 status/keyword/category 筛选）
- `GET /api/admin/game/{id}` — 获取游戏详情
- `POST /api/admin/game` — 新增游戏
- `PUT /api/admin/game/{id}` — 更新游戏
- `DELETE /api/admin/game/{id}` — 删除游戏

**分类管理**:
- `GET /api/admin/categories` — 分类列表（含游戏计数）
- `POST /api/admin/category` — 新增分类
- `PUT /api/admin/category/{id}` — 更新分类
- `DELETE /api/admin/category/{id}` — 删除分类

**仪表盘**:
- `GET /api/admin/stats` — 统计概览（总数/发布数/草稿数/分类数/最近游戏）

**前端**:
- 登录页 (`admin/login.html`)
- 管理后台 SPA (`admin/index.html` + `admin/js/main.js`)
- 8个菜单：仪表盘、游戏管理、分类管理、下载资源、采集管理(隐藏)、资源中转(隐藏)、AI助手(隐藏)、系统设置

### 模块5: SEO 优化

**状态**: ✅ 完成

- `GET /game/{identifier}` — SSR 游戏详情页（完整 HTML + SEO 标签）
  - ID 访问自动 301 跳转到 Slug URL
  - `<title>`、`<meta description>`、`<meta keywords>`（自定义优先，否则自动生成）
  - Open Graph 标签（og:title、og:description、og:image、og:url）
  - Twitter Card 标签
  - Canonical URL
  - JSON-LD 结构化数据（SoftwareApplication schema）
  - 内嵌 `window.__GAME_DATA__` 供前端 JS 直接渲染
- `GET /sitemap.xml` — 动态站点地图
- `GET /robots.txt` — 爬虫规则（禁止后台/admin/和/api/admin/等路径）
- 前端 game-detail.js 优先使用 SSR 内嵌数据

### 模块6: 采集接口

**状态**: ✅ 完成

- `POST /api/crawler/import` — Collector-Key 认证 + 批量导入
- `GET /api/crawler/health` — 健康检查
- original_url 去重逻辑
- slug 自动生成（title + 时间戳 hash）
- 导入状态默认 draft
- 详细文档: `docs/crawler-api.md`

### 模块7.1: 下载资源管理

**状态**: ✅ 完成

- `GET /api/admin/download-resources` — 资源列表（支持 game_id/keyword/provider/status 筛选）
- `GET /api/admin/download-resources/{id}` — 单个资源详情
- `POST /api/admin/download-resources` — 新增资源
- `PUT /api/admin/download-resources/{id}` — 更新资源
- `DELETE /api/admin/download-resources/{id}` — 删除资源
- `GET /api/admin/download-resources-games` — 游戏下拉列表
- provider_id 与 provider 双字段兼容
- 状态管理：pending/active/disabled/invalid

### 模块7.2: 下载渠道管理

**状态**: ✅ 完成

- `GET /api/admin/download-providers` — 渠道列表（支持 keyword/status 筛选 + 使用量统计）
- `GET /api/admin/download-providers/active` — 启用渠道列表（下拉选择用）
- `GET /api/admin/download-providers/{id}` — 单个渠道详情
- `POST /api/admin/download-providers` — 新增渠道
- `PUT /api/admin/download-providers/{id}` — 更新渠道
- `DELETE /api/admin/download-providers/{id}` — 删除渠道（有使用量时阻止删除）
- 8种预设渠道：百度网盘、夸克、阿里云盘、115、迅雷、UC、移动云盘、天翼云盘

### 模块7.3: 前端下载展示

**状态**: ✅ 完成

- 游戏详情页底部固定下载栏，显示多渠道按钮
- 每个渠道按钮显示：渠道名 + 资源标题 + 提取码
- 点击渠道按钮跳转到统一下载页
- 旧版下载二维码页兼容（`download.html`，使用 Google Chart API）
- SSR 详情页内置下载栏和下载按钮

### 模块7.4: 下载控制器

**状态**: ✅ 完成

- `GET /download/{resource_id}` — 统一下载入口（设备检测 → Token 获取 → 分流处理）
- `GET /d/{token_str}` — Token 短链接（二维码目标）
- `GET /api/download/qr/{token_str}` — 二维码 PNG 图片生成
- Token 生成（`secrets.token_urlsafe(32)`）、并发安全（IntegrityError 回退）
- 设备类型检测（User-Agent 正则）
- PC 端：渲染下载页面（游戏名 + 渠道名 + 提取码 + 二维码 + 操作说明）
- Mobile 端：302 跳转到网盘分享链接
- 下载行为日志记录（IP、UA、设备类型、操作类型）
- 二维码内存缓存
- 错误页面渲染

---
### 模块7.7: 游戏标签(Tag)与标签SEO系统

**状态**: ✅ 完成

- `GET /api/admin/tags` — [后台] 标签列表
- `GET /api/admin/tags/active` — [后台] 启用标签下拉
- `GET /api/admin/tags/{id}` — [后台] 标签详情
- `POST /api/admin/tags` — [后台] 新增标签
- `PUT /api/admin/tags/{id}` — [后台] 更新标签
- `DELETE /api/admin/tags/{id}` — [后台] 删除标签
- `GET /api/admin/game/{id}/tags` — [后台] 游戏标签ID
- `PUT /api/admin/game/{id}/tags` — [后台] 更新标签关联
- `GET /tag/{slug}` — 标签详情页(SSR+SEO)
- 后台游戏编辑页标签多选
- 标签页面分页
- Sitemap 包含标签URL
- 游戏详情页相关推荐(同Tag+同Category)
- tags表 + game_tags多对多关联
- JSON-LD、OpenGraph、Canonical等SEO元数据


## 预留模块

| 模块 | 路由 | 当前行为 |
|------|------|----------|
| 模块8: 资源中转 | `POST /api/transfer/update-link` | 返回 501 Not Implemented |
| 模块9: AI 运营 | `POST /api/ai/generate` | 返回 501 Not Implemented |

预留模块的接口路由已在 `main.py` 中注册，Schema 已在对应 `__init__.py` 中定义，返回统一的 501 响应格式。


---

## 版本历史

| 版本 | 日期 | 内容 |
|------|------|------|
| v0.1.0 | - | 项目初始化、数据模型 |
| v0.2.0 | - | 游戏公开 API |
| v0.3.0 | - | 后台管理系统 |
| v0.4.0 | - | SEO 优化 |
| v0.5.0 | - | 采集接口 |
| v0.6.0 | - | 下载资源管理 |
| v0.7.0 | - | 下载渠道管理 |
| v0.7.1 | - | 前端下载展示 |
| v0.7.2 | - | 渠道关联下载资源 |
| v0.7.3 | - | 下载资源与渠道双字段兼容 |
| v0.7.4 | 2026-07-12 | 下载控制器（Token + 设备分流 + 日志） |
| v0.7.5 | 2026-07-12 | SEO 基础系统（SITE_URL 配置化、sitemap 分类+分页、meta 标签修复） |
| v0.7.6 | 2026-07-12 | 下载统计系统（日志增强、统计 API、后台统计面板） |
| v0.7.7 | 2026-07-15 | 游戏标签(Tag)与标签SEO系统 |
