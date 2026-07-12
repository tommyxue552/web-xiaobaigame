# 小白游戏资源站 - API 文档

## 基本信息

- **基础 URL**: `http://localhost:8000`
- **内容类型**: `application/json`
- **交互式文档**: 启动服务后访问 `http://localhost:8000/docs`（Swagger UI）

## 通用响应格式

所有接口统一返回 JSON：

```json
{
    "code": 0,
    "message": "success",
    "data": { ... }
}
```

| code | 说明 |
|------|------|
| 0    | 成功 |
| 501  | 功能未实现（预留接口） |
| 400  | 请求参数错误 |
| 404  | 资源不存在 |

---

## 一、公开接口

### GET /api/games

获取已发布的游戏列表（分页）。

**查询参数**：

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| page | int | 否 | 1 | 页码 |
| page_size | int | 否 | 20 | 每页数量（最大100） |
| category | string | 否 | "" | 按分类筛选 |
| keyword | string | 否 | "" | 按标题关键词搜索 |

**响应示例**：

```json
{
    "code": 0,
    "message": "success",
    "data": {
        "items": [
            {
                "id": 1,
                "title": "GTA V",
                "slug": "grand-theft-auto-v",
                "cover": "https://...",
                "category": "动作",
                "tags": ["开放世界", "犯罪"],
                "system": "Windows",
                "language": "中文",
                "size": "100GB",
                "version": "v1.0",
                "publisher": "Rockstar Games",
                "developer": "Rockstar North",
                "release_date": "2015-04-14",
                "created_at": "2026-07-11 12:00:00"
            }
        ],
        "total": 100,
        "page": 1,
        "page_size": 20
    }
}
```

---

### GET /api/game/{id}

获取单个游戏详情。

**路径参数**：

| 参数 | 类型 | 说明 |
|------|------|------|
| id | int | 游戏ID |

**响应示例**：见上文，额外包含 `description`、`images`、`download_url`、`original_url` 等完整字段。

---

## 二、管理接口

> 管理接口前缀：`/api/admin`

### GET /api/admin/games

获取所有游戏列表（含未发布）。

**查询参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | int | 否 | 页码 |
| page_size | int | 否 | 每页数量 |
| publish_status | string | 否 | 按状态筛选：`draft` / `published` / `hidden` |

---

### GET /api/admin/game/{id}

获取任意状态的游戏详情。

---

### POST /api/admin/game

创建新游戏。

**请求体**：

```json
{
    "title": "游戏标题",
    "slug": "game-slug",
    "cover": "https://...",
    "images": ["https://..."],
    "description": "游戏简介",
    "system": "Windows",
    "language": "中文",
    "size": "50GB",
    "version": "v1.0",
    "publisher": "发行商",
    "developer": "开发商",
    "release_date": "2024-01-01",
    "category": "动作",
    "tags": ["标签1", "标签2"],
    "download_url": "https://...",
    "original_url": "https://...",
    "crawler_source": "",
    "crawler_url": "",
    "transfer_status": "pending",
    "publish_status": "draft"
}
```

---

### PUT /api/admin/game/{id}

更新游戏信息（所有字段可选，仅更新传入的字段）。

---

### DELETE /api/admin/game/{id}

删除游戏记录。

---

## 三、预留接口（HTTP 501）

> 以下接口已预留路由，暂返回 501 Not Implemented。

### POST /api/crawler/import

采集程序批量导入游戏数据。

**预留请求格式**：

```json
{
    "source": "steam",
    "batch_id": "uuid-v4",
    "games": [
        {
            "title": "...",
            "slug": "...",
            "cover": "..."
        }
    ]
}
```

---

### POST /api/transfer/update-link

资源中转程序更新下载链接。

**预留请求格式**：

```json
{
    "game_id": 123,
    "download_url": "https://cdn.example.com/game.zip",
    "file_size": "50GB",
    "transfer_status": "completed"
}
```

---

### POST /api/ai/generate

AI 程序自动生成内容。

**预留请求格式**：

```json
{
    "game_id": 123,
    "task": "description",
    "options": {}
}
```

---

## 四、静态文件

| URL | 说明 |
|-----|------|
| `/frontend/index.html` | 前台游戏列表页 |
| `/frontend/download.html` | 下载二维码页面 |
| `/admin/index.html` | 后台管理面板 |
| `/uploads/` | 上传文件目录 |

---

## ER 图

```
+=====================================================================+
|                              games                                   |
+=====================================================================+
| PK | id              | INTEGER        | 主键，自增                     |
|    | title           | VARCHAR(255)   | 游戏标题，NOT NULL             |
| UK | slug            | VARCHAR(255)   | URL 标识，UNIQUE，NOT NULL     |
|    | cover           | VARCHAR(500)   | 封面图片 URL                   |
|    | images          | JSON/TEXT      | 截图列表                       |
|    | description     | TEXT           | 游戏简介                       |
|    | system          | VARCHAR(100)   | 运行平台                       |
|    | language        | VARCHAR(50)    | 语言                           |
|    | size            | VARCHAR(50)    | 文件大小                       |
|    | version         | VARCHAR(50)    | 版本号                         |
|    | publisher       | VARCHAR(100)   | 发行商                         |
|    | developer       | VARCHAR(100)   | 开发商                         |
|    | release_date    | DATE           | 发布日期                       |
|    | category        | VARCHAR(100)   | 游戏分类      [索引]           |
|    | tags            | JSON/TEXT      | 标签列表                       |
|    | download_url    | VARCHAR(500)   | 下载直链                       |
|    | original_url    | VARCHAR(500)   | 原始来源 URL                   |
|    | crawler_source  | VARCHAR(100)   | 采集来源标识   [索引]           |
|    | crawler_url     | VARCHAR(500)   | 采集源页面 URL                 |
|    | transfer_status | VARCHAR(50)    | 中转状态       [索引]           |
|    | transfer_time   | DATETIME       | 中转完成时间                   |
|    | publish_status  | VARCHAR(20)    | 发布状态       [索引]           |
|    | created_at      | DATETIME       | 创建时间       [索引]           |
|    | updated_at      | DATETIME       | 更新时间                       |
+=====================================================================+
```
