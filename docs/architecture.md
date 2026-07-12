# 系统架构

## 总体架构

```
┌─────────────────────────────────────────────────────────────┐
│                         浏览器                               │
├──────────────┬──────────────────┬───────────────────────────┤
│  前台页面     │  后台管理页面       │  下载页面                  │
│  frontend/   │  admin/           │  (服务端渲染)              │
│  HTML+CSS+JS │  HTML+CSS+JS      │                           │
└──────┬───────┴────────┬─────────┴─────────────┬─────────────┘
       │                │                       │
       ▼                ▼                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI 后端服务                           │
│                    backend/app/main.py                       │
├────────────┬──────────┬──────────┬──────────┬───────────────┤
│ games.py   │ admin.py │crawler.py│download_ │download_      │
│ (公开API)  │ (管理API) │(采集API) │providers │resources      │
│            │          │          │.py       │.py            │
├────────────┼──────────┼──────────┼──────────┼───────────────┤
│ transfer.py│ ai.py    │download_controller.py               │
│ (预留501)  │ (预留501)│ (模块7.4 - 统一下载)                  │
├────────────┴──────────┴─────────────────────────────────────┤
│                    download_service.py                       │
│                    (Token管理 + 设备分流)                      │
├─────────────────────────────────────────────────────────────┤
│                    core/                                     │
│         auth.py  │  config.py  │  database.py               │
│         (JWT)    │  (配置管理)   │  (SQLAlchemy async)        │
├─────────────────────────────────────────────────────────────┤
│                    models/                                   │
│  game.py │ category.py │ download_resource.py │ ...         │
│  download_provider.py │ download_token.py │ download_log.py │
│  admin_user.py                                               │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    SQLite 数据库                              │
│                    database/xiaobaigame.db                   │
├──────────────┬──────────────┬──────────────┬────────────────┤
│   games      │  categories  │download_     │download_       │
│              │              │resources     │providers       │
├──────────────┼──────────────┼──────────────┼────────────────┤
│download_     │download_logs │admin_users   │                │
│tokens        │              │              │                │
└──────────────┴──────────────┴──────────────┴────────────────┘
```

## 前端架构

```
frontend/
├── index.html          # 首页：分类导航 + 搜索 + 最新/热门游戏网格
├── games.html          # 游戏列表页：筛选 + 分页浏览
├── game.html           # 游戏详情页：JS 动态加载模式
├── download.html       # 下载二维码页（旧版兼容，使用 Google Chart API）
├── css/style.css       # 全局样式 (~19KB)
├── js/
│   ├── main.js         # 首页逻辑：分类切换、搜索、卡片渲染 (~9.7KB)
│   ├── games.js        # 列表页逻辑：分页、筛选、弹窗 (~10.5KB)
│   └── game-detail.js  # 详情页逻辑：SSR内嵌数据优先、截图灯箱、多渠道下载 (~14.5KB)
└── images/
    └── placeholder.svg # 封面占位图
```

### 前端特点

- **零依赖**：无 npm/webpack，纯原生 JS
- **SSR + CSR 混合**：游戏详情页支持服务端渲染 HTML（`/game/{slug}` 返回完整 HTML，含内嵌 `window.__GAME_DATA__`），JS 端检测到内嵌数据后直接渲染，否则回退到 API 加载
- **SEO 优化**：服务端渲染的详情页包含 og:title、og:description、og:image、twitter:card、canonical、JSON-LD 结构化数据
- **移动端适配**：响应式设计，移动端菜单按钮

## 后台管理架构

```
admin/
├── login.html          # 管理员登录页
├── index.html          # 管理后台 SPA 入口
├── auto_login.html     # 自动登录（开发调试用）
├── js/main.js          # 管理后台主逻辑 (~52KB)：SPA 路由、仪表盘、游戏CRUD、分类CRUD、资源管理、渠道管理
└── css/style.css       # 管理后台样式 (~16KB)
```

### 管理后台功能模块

| 模块 | 功能 |
|------|------|
| 仪表盘 | 总游戏数、发布/草稿统计、分类数、最近游戏 |
| 游戏管理 | 列表(分页+筛选)、新增、编辑、删除、发布状态管理 |
| 分类管理 | 列表、新增、编辑、删除（含游戏计数） |
| 下载资源 | 列表(按游戏/渠道筛选)、新增、编辑、删除、游戏下拉选择 |
| 下载渠道 | 列表、新增、编辑、删除（使用量检查） |

### 认证流程

```
登录页 → POST /api/admin/login (username + password)
       → 返回 JWT Token
       → 存入 localStorage
       → 后续请求携带 Authorization: Bearer {token}
       → 401 时自动跳转登录页
```

## 后端架构

### 路由注册（main.py）

| 路由模块 | 前缀 | 状态 |
|----------|------|------|
| `games.py` | `/api` | 已实现 |
| `admin.py` | `/api/admin` | 已实现 |
| `crawler.py` | `/api/crawler` | 已实现 |
| `download_resources.py` | `/api/admin` | 已实现 |
| `download_providers.py` | `/api/admin` | 已实现 |
| `download_controller.py` | `/api/download`, `/d` | 已实现 (模块7.4) |
| `transfer.py` | `/api/transfer` | 预留 (501) |
| `ai.py` | `/api/ai` | 预留 (501) |

### 分层设计

```
Controller 层 (api/*.py)
    ↓ 调用
Service 层 (services/download_service.py)
    ↓ 调用
Model 层 (models/*.py)
    ↓ ORM
Database (SQLite via SQLAlchemy async)
```

当前 Service 层仅 `download_service.py`（模块7.4）。CRUD 操作直接在 Controller 层通过 SQLAlchemy 查询完成。

### 配置管理 (core/config.py)

使用 `pydantic-settings`，从 `.env` 文件加载配置：

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| DATABASE_URL | 空（自动使用 SQLite） | 数据库连接 |
| APP_NAME | 小白游戏资源站 | 应用名称 |
| APP_VERSION | 1.0.0 | 版本号 |
| DEBUG | true | 调试模式 |
| HOST | 0.0.0.0 | 监听地址 |
| PORT | 8000 | 监听端口 |
| JWT_SECRET_KEY | (内置默认值) | JWT 签名密钥 |
| JWT_EXPIRE_MINUTES | 480 | Token 有效期 |
| COLLECTOR_KEY | (内置默认值) | 采集器认证 Key |
| CRAWLER_ENABLED | false | 采集功能开关（预留） |
| AI_ENABLED | false | AI 功能开关（预留） |
| TRANSFER_ENABLED | false | 中转功能开关（预留） |

## 数据库架构

- **类型**：SQLite
- **ORM**：SQLAlchemy 2.0 Async
- **引擎**：`create_async_engine` + `aiosqlite`
- **表创建**：启动时通过 `Base.metadata.create_all` 自动建表
- **迁移**：SQL 文件位于 `database/migrations/`
- **SQLite 文件**：`database/xiaobaigame.db`

详见 [DATABASE.md](./DATABASE.md)。

## Web 与 Collector 解耦关系

```
┌─────────────────────────┐       ┌──────────────────────────┐
│   web-xiaobaigame        │       │  xiaobai-game-collector   │
│   (本站)                  │       │  (独立采集程序)            │
├─────────────────────────┤       ├──────────────────────────┤
│  POST /api/crawler/import│◄──────│  HTTP 请求                │
│                          │       │  Header: Collector-Key    │
│  接收导入数据              │       │                          │
│  original_url 去重        │       │  爬取各站点游戏信息        │
│  slug 自动生成            │       │  批量 POST 导入           │
│  状态设为 draft           │       │                          │
└─────────────────────────┘       └──────────────────────────┘
```

### 解耦设计要点

1. **独立部署**：collector 是独立程序，不需要与 web 部署在同一服务器
2. **API Key 认证**：通过 `Collector-Key` HTTP Header 认证
3. **original_url 去重**：导入时根据 `original_url` 判断是否已存在，避免重复导入
4. **草稿状态**：采集导入的游戏默认 `publish_status = draft`，需管理员审核后发布
5. **slug 自动生成**：根据 title + 时间戳 hash 自动生成唯一 slug

## 下载系统架构（模块7.4）

```
用户点击下载按钮
       │
       ▼
GET /download/{resourceId}
       │
       ├─── PC端 (User-Agent 检测)
       │      │
       │      ▼
       │   下载服务生成/获取 Token
       │      │
       │      ▼
       │   渲染下载页：游戏名 + 渠道名 + 提取码 + 二维码
       │   二维码编码 → /d/{token} (不暴露真实网盘链接)
       │
       └─── 移动端 (User-Agent 检测)
              │
              ▼
           下载服务生成/获取 Token
              │
              ▼
           302 Redirect → my_share_url (网盘直链)
```

### 设计特点

- **二维码永久有效**：二维码编码的是 `/d/{token}`（Token 中间页），不直接编码网盘链接
- **链接可更换**：管理员修改 `download_resources.my_share_url`，二维码无需重新生成
- **Token 唯一约束**：每个 DownloadResource 同一状态下只有一个有效 Token（`UNIQUE(resource_id, status)`）
- **下载日志预留**：`download_logs` 表记录每次访问行为（IP、UA、设备类型、操作类型）
- **设备智能分流**：服务端通过 User-Agent 正则判断设备类型（Android/iPhone/iPad 等）
- **二维码缓存**：内存缓存已生成的二维码 PNG，避免重复渲染

详见 [ARCHITECTURE.md 下载系统部分](./ARCHITECTURE.md#下载系统模块74)。
