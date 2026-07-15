# API 文档

## 基本信息

- **基础 URL**: `http://localhost:8000`
- **内容类型**: `application/json`
- **交互式文档**: `http://localhost:8000/docs` (Swagger UI)

## 通用响应格式

```json
{
    "code": 0,
    "message": "success",
    "data": { ... }
}
```

| code | 说明 |
|------|------|
| 0 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未授权 / Token 无效 |
| 404 | 资源不存在 |
| 422 | 请求体验证失败 |
| 501 | 功能未实现（预留接口） |

---

## 一、公开接口

### GET /api/categories

获取分类列表。

**响应**：
```json
{
    "code": 0,
    "message": "success",
    "data": [
        {"id": 1, "name": "动作游戏", "slug": "action"},
        {"id": 2, "name": "角色扮演", "slug": "rpg"}
    ]
}
```

---

### GET /api/games

获取已发布游戏列表（分页）。

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| page | int | 否 | 1 | 页码 |
| page_size | int | 否 | 20 | 每页数量（最大100） |
| category | string | 否 | "" | 按分类名称筛选 |
| keyword | string | 否 | "" | 按标题关键词搜索 |
| sort | string | 否 | "latest" | latest（最新）/ hot（热门，按ID降序） |

**响应**：
```json
{
    "code": 0,
    "message": "success",
    "data": {
        "games": [
            {
                "id": 1,
                "title": "GTA V",
                "slug": "grand-theft-auto-v",
                "cover": "https://...",
                "category": "动作游戏",
                "category_name": "动作游戏",
                "tags": ["开放世界", "犯罪"],
                "system": "Windows",
                "language": "中文",
                "size": "100GB",
                "version": "v1.0",
                "publisher": "Rockstar Games",
                "developer": "Rockstar North",
                "release_date": "2015-04-14",
                "created_at": "2026-07-11 12:00:00",
                "views": 150
            }
        ],
        "total": 100,
        "page": 1,
        "size": 20
    }
}
```

---

### GET /api/game/{id}

获取已发布游戏详情。

| 参数 | 类型 | 说明 |
|------|------|------|
| id | int (path) | 游戏ID |

**响应**：返回游戏完整信息，包含：
- 基础信息（title、slug、cover、images、description）
- 元数据（system、language、size、version、publisher、developer、release_date）
- 分类与标签（category、category_name、tags）
- 下载相关（download_url、original_url、download_resources）
- 采集相关（crawler_source、transfer_status）
- 统计（views、created_at、updated_at）

访问时会自动增加 `views` 计数。

---

### GET /api/game/slug/{slug}

通过 Slug 获取已发布游戏详情。返回内容与 `GET /api/game/{id}` 相同。

| 参数 | 类型 | 说明 |
|------|------|------|
| slug | string (path) | 游戏 Slug |

---

### GET /api/game/{game_id}/download-resources

获取游戏关联的下载资源列表。

| 参数 | 类型 | 说明 |
|------|------|------|
| game_id | int (path) | 游戏ID |

**响应**：
```json
{
    "code": 0,
    "message": "success",
    "data": {
        "resources": [
            {
                "id": 1,
                "provider_code": "baidu",
                "provider_name": "百度网盘",
                "title": "v1.2 绿色版",
                "extract_code": "abcd",
                "display_order": 0
            }
        ]
    }
}
```

---

### GET /api/qrcode/{game_id}

生成游戏下载二维码（PNG 图片）。

| 参数 | 类型 | 说明 |
|------|------|------|
| game_id | int (path) | 游戏ID |

**响应**: `image/png` — 二维码图片（编码 `download_url` 内容）

---

### GET /game/{identifier}

SEO 优化的游戏详情页（返回完整 HTML）。

| 参数 | 类型 | 说明 |
|------|------|------|
| identifier | string (path) | 游戏ID（数字）或 Slug（字符串） |

- ID 访问自动 301 跳转到 Slug URL
- HTML 包含完整的 SEO 标签（og、twitter、canonical、JSON-LD）
- 内嵌 `window.__GAME_DATA__` 供前端 JS 使用
- 访问时自动增加 views 计数

---

### GET /game/{game_id}/download-qr

PC 端二维码下载页（旧版兼容）。

| 参数 | 类型 | 说明 |
|------|------|------|
| game_id | int (path) | 游戏ID |

- 移动端 User-Agent → 302 跳转到 download_url
- PC 端 → 展示二维码下载页面

---

### GET /sitemap.xml

动态站点地图。

**响应**: `application/xml` — 符合搜索引擎标准的站点地图

---

### GET /sitemap-{page}.xml

分页站点地图，每页最多 50000 条 URL。

| 参数 | 类型 | 说明 |
|------|------|------|
| page | int (path) | 页码（从 1 开始） |

**响应**: pplication/xml`r

---

### GET /robots.txt

爬虫规则（Sitemap 地址使用动态 SITE_URL 配置）。

**响应**: `text/plain`

---


---

## 二、下载控制器接口（模块7.4）

### GET /download/{resource_id}

统一下载入口。根据 User-Agent 判断设备类型分流。

| 参数 | 类型 | 说明 |
|------|------|------|
| resource_id | int (path) | 下载资源ID |

- **PC 端**: 返回下载页面 HTML（游戏名 + 渠道名 + 提取码 + 二维码 + 操作说明）
- **移动端**: 302 跳转到 `my_share_url`（网盘直链）

系统自动为资源创建或获取 Token，并记录下载日志。

---

### GET /d/{token_str}

Token 短链接（二维码编码目标）。

| 参数 | 类型 | 说明 |
|------|------|------|
| token_str | string (path) | 下载 Token |

行为与 `/download/{resource_id}` 相同：
- PC 端 → 下载页面
- 移动端 → 302 跳转

---

### GET /api/download/qr/{token_str}

生成 Token 二维码图片。

| 参数 | 类型 | 说明 |
|------|------|------|
| token_str | string (path) | 下载 Token |

**响应**: `image/png` — 二维码（编码 `/d/{token_str}`），已加内存缓存。

---

## 三、下载统计接口（模块7.6）

> 所有统计接口需要 JWT 认证，Header: `Authorization: Bearer {token}`

### GET /api/admin/download-stats/overview

下载统计总览。

**响应**：
```json
{
    "code": 0,
    "message": "success",
    "data": {
        "today": 150,
        "today_view": 120,
        "today_redirect": 30,
        "yesterday": 135,
        "total": 12500
    }
}
```

| 字段 | 说明 |
|------|------|
| today | 今日下载总次数（view + redirect） |
| today_view | 今日查看下载页次数 |
| today_redirect | 今日跳转网盘次数 |
| yesterday | 昨日下载总次数 |
| total | 历史累计总次数 |

---

### GET /api/admin/download-stats/top-games

热门游戏下载排行。

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| limit | int | 否 | 10 | 返回数量（1-100） |

**响应**：
```json
{
    "code": 0,
    "message": "success",
    "data": {
        "ranking": [
            {"game_id": 1, "game_title": "GTA V", "download_count": 520},
            {"game_id": 2, "game_title": "巫师3", "download_count": 480}
        ],
        "total_items": 2
    }
}
```

---

### GET /api/admin/download-stats/providers

网盘渠道下载统计。

**响应**：
```json
{
    "code": 0,
    "message": "success",
    "data": {
        "providers": [
            {
                "provider_id": 1,
                "provider_name": "百度网盘",
                "provider_code": "baidu",
                "total_count": 300,
                "view_count": 250,
                "redirect_count": 50
            }
        ]
    }
}
```

| 字段 | 说明 |
|------|------|
| total_count | 总下载行为次数 |
| view_count | 查看下载页次数 |
| redirect_count | 跳转网盘次数 |

---

### GET /api/admin/download-stats/trend

下载量时间趋势。

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| days | int | 否 | 7 | 统计天数（1-90） |

**响应**：
```json
{
    "code": 0,
    "message": "success",
    "data": {
        "trend": [
            {"date": "2026-07-06", "count": 45},
            {"date": "2026-07-07", "count": 52}
        ],
        "days": 7
    }
}
```

无数据的日期 count 为 0。

---

## 四、管理接口

> 所有管理接口需要 JWT 认证，Header: `Authorization: Bearer {token}`

### POST /api/admin/login

管理员登录。

**请求体**：
```json
{
    "username": "admin",
    "password": "password123"
}
```

**响应**：
```json
{
    "code": 0,
    "message": "登录成功",
    "data": {
        "token": "eyJhbGciOiJIUzI1NiIs...",
        "username": "admin"
    }
}
```

**错误** (401): `{"detail": "用户名或密码错误"}`

---

### GET /api/admin/me

获取当前登录管理员信息。

**响应**：
```json
{
    "code": 0,
    "message": "success",
    "data": {"id": 1, "username": "admin"}
}
```

---

### GET /api/admin/stats

仪表盘统计数据。

**响应**：
```json
{
    "code": 0,
    "message": "success",
    "data": {
        "total_games": 150,
        "published_games": 120,
        "draft_games": 30,
        "category_count": 7,
        "recent_games": [...]
    }
}
```

---

### 游戏管理

| 方法 | 路由 | 说明 |
|------|------|------|
| GET | `/api/admin/games` | 游戏列表 |
| GET | `/api/admin/game/{id}` | 游戏详情 |
| POST | `/api/admin/game` | 新增游戏 |
| PUT | `/api/admin/game/{id}` | 更新游戏（部分更新） |
| DELETE | `/api/admin/game/{id}` | 删除游戏 |

**列表查询参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | int | 否 | 页码（默认1） |
| page_size | int | 否 | 每页数量（默认20） |
| keyword | string | 否 | 标题搜索 |
| publish_status | string | 否 | 状态筛选：draft / published |
| category | string | 否 | 分类筛选 |

**POST 请求体**（所有字段见 GameCreate schema）：
```json
{
    "title": "游戏标题",
    "slug": "game-slug",
    "cover": "https://...",
    "images": ["https://..."],
    "description": "简介",
    "system": "Windows",
    "language": "中文",
    "size": "50GB",
    "version": "v1.0",
    "publisher": "发行商",
    "developer": "开发商",
    "release_date": "2024-01-01",
    "category_id": 1,
    "category": "动作游戏",
    "tags": ["标签1", "标签2"],
    "download_url": "https://...",
    "original_url": "https://...",
    "crawler_source": "",
    "crawler_url": "",
    "transfer_status": "pending",
    "seo_title": "",
    "seo_description": "",
    "seo_keywords": "",
    "publish_status": "draft"
}
```

**PUT 请求体**：所有字段均为可选，仅更新传入的字段。

---

### 分类管理

| 方法 | 路由 | 说明 |
|------|------|------|
| GET | `/api/admin/categories` | 分类列表（含游戏计数） |
| POST | `/api/admin/category` | 新增分类 |
| PUT | `/api/admin/category/{id}` | 更新分类 |
| DELETE | `/api/admin/category/{id}` | 删除分类 |

**POST 请求体**：
```json
{"name": "分类名称", "slug": "category-slug"}
```

---

### 下载资源管理

| 方法 | 路由 | 说明 |
|------|------|------|
| GET | `/api/admin/download-resources` | 资源列表 |
| GET | `/api/admin/download-resources/{id}` | 资源详情 |
| POST | `/api/admin/download-resources` | 新增资源 |
| PUT | `/api/admin/download-resources/{id}` | 更新资源 |
| DELETE | `/api/admin/download-resources/{id}` | 删除资源 |
| GET | `/api/admin/download-resources-games` | 游戏下拉列表（供选择用） |

**列表查询参数**：

| 参数 | 类型 | 说明 |
|------|------|------|
| game_id | int | 按游戏筛选 |
| keyword | string | 按游戏名称搜索 |
| provider | string | 按网盘代码筛选 |
| provider_id | int | 按渠道ID筛选 |
| status | string | 按状态筛选 |
| page | int | 页码 |
| page_size | int | 每页数量 |

**POST 请求体**：
```json
{
    "game_id": 1,
    "provider_id": 1,
    "provider": "baidu",
    "title": "v1.2 绿色版",
    "origin_url": "https://source.com/...",
    "my_share_url": "https://pan.baidu.com/...",
    "extract_code": "abcd",
    "remark": "备注",
    "display_order": 0,
    "status": "active"
}
```

---

### 下载渠道管理

| 方法 | 路由 | 说明 |
|------|------|------|
| GET | `/api/admin/download-providers` | 渠道列表（含使用量统计） |
| GET | `/api/admin/download-providers/active` | 启用的渠道列表 |
| GET | `/api/admin/download-providers/{id}` | 渠道详情 |
| POST | `/api/admin/download-providers` | 新增渠道 |
| PUT | `/api/admin/download-providers/{id}` | 更新渠道 |
| DELETE | `/api/admin/download-providers/{id}` | 删除渠道 |

**限制**: 有下载资源关联的渠道无法删除（返回 400）

**POST 请求体**：
```json
{
    "code": "baidu",
    "name": "百度网盘",
    "icon": "",
    "status": "active",
    "display_order": 1,
    "remark": ""
}
```

---

## 五、采集接口

### POST /api/crawler/import

采集程序批量导入游戏。

**认证**: `Collector-Key` HTTP Header（与 `settings.COLLECTOR_KEY` 对比）

**请求体**：
```json
{
    "games": [
        {
            "title": "游戏名称",
            "cover": "https://example.com/cover.jpg",
            "description": "游戏描述",
            "category": "动作游戏",
            "size": "1.2 GB",
            "download_url": "https://example.com/download.zip",
            "original_url": "https://source.com/game/123",
            "source": "example-site"
        }
    ],
    "source": "xiaobai-game-collector"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| games | array | 是 | 游戏列表（至少1个） |
| games[].title | string | 是 | 游戏标题（≤255字符） |
| games[].original_url | string | 否 | 原始URL（用于去重） |
| source | string | 否 | 来源标识（默认 xiaobai-game-collector） |

**响应** (200)：
```json
{
    "success": true,
    "message": "import success",
    "imported": 5,
    "skipped": 2
}
```

- `imported`: 成功导入数量
- `skipped`: 跳过数量（original_url 重复 + 空标题）

**去重逻辑**: 根据 `original_url` 检查 games 表是否已存在，存在则跳过。

**注意**: 导入的游戏 `publish_status` 默认为 `draft`，需要管理员在后台审核发布。

**错误** (401): `{"detail": "Collector-Key 验证失败"}`

---

### GET /api/crawler/health

采集接口健康检查。

**响应**：
```json
{
    "success": true,
    "message": "crawler api is running",
    "version": "1.0.0"
}
```

---


---

## 八、标签管理 API（模块7.7）

所有接口需要 Admin 认证。

### GET /api/admin/tags

[后台] 标签列表。

**查询参数**：

| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| keyword | string | "" | 名称搜索 |
| is_active | bool | null | 启用状态筛选 |

### GET /api/admin/tags/active

[后台] 启用标签列表（轻量版，用于下拉选择）。

### GET /api/admin/tags/{tag_id}

[后台] 标签详情。

### POST /api/admin/tags

[后台] 新增标签。

### PUT /api/admin/tags/{tag_id}

[后台] 更新标签。

### DELETE /api/admin/tags/{tag_id}

[后台] 删除标签。

### GET /api/admin/game/{game_id}/tags

[后台] 获取游戏的标签ID列表。

### PUT /api/admin/game/{game_id}/tags

[后台] 更新游戏的标签关联。请求体为 tag_ids 数组。

---

## 九、标签公开页面（模块7.7）

### GET /tag/{slug}

标签详情页（SSR），无需认证。

**功能**：
- 标签介绍（name + description）
- 关联游戏列表（分页，默认 12 条/页）
- 面包屑导航
- 完整 SEO：title、description、keywords、canonical、OpenGraph、JSON-LD
- Sitemap 自动收录

## 六、预留接口

以下接口已注册路由，返回 `501 Not Implemented`。

### POST /api/transfer/update-link

资源中转更新下载链接（预留）。

### POST /api/ai/generate

AI 生成游戏内容（预留）。

---

## 七、静态文件路由

| URL | 说明 |
|-----|------|
| `/` | 首页（frontend/index.html） |
| `/frontend/...` | 前台静态资源 |
| `/admin/...` | 后台管理页面 |
| `/uploads/...` | 上传文件访问 |
