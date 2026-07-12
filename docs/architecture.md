# web-xiaobaigame 系统架构

## 下载系统（模块7.4）

### 概述

所有游戏下载统一经过 `DownloadController`，根据设备类型分流处理。

### 下载流程

```
Game Detail Page (frontend)
        |
        v
DownloadController (/download/{resourceId})
        |
        +--[设备检测]--+
        |              |
       PC            Mobile
        |              |
        v              v
  DownloadService  DownloadService
  .get_or_create   .get_or_create
  _token()         _token()
        |              |
        v              v
  DownloadToken   DownloadToken
  (永久有效)       (永久有效)
        |              |
        v              v
  DownloadProvider DownloadProvider
  (网盘渠道)        (网盘渠道)
        |              |
        v              v
  渲染下载页       302 Redirect
  + 二维码         到真实网盘链接
```

### 设备分流

**PC 端：**
- 访问 `/download/{resourceId}` 或扫码访问 `/d/{token}`
- 展示下载页面，包含：
  - 游戏名称、资源标题
  - 网盘名称、提取码
  - 二维码（编码 `/d/{token}`）
  - 下载操作说明

**Mobile 端：**
- 访问 `/download/{resourceId}` 或扫码访问 `/d/{token}`
- 服务端通过 User-Agent 检测移动设备
- 302 跳转到真实网盘链接（DownloadResource.my_share_url）

### 设计要点

1. **二维码不保存真实网盘地址**
   - 二维码编码的是 `/d/{token}`（Token 链接），而非网盘直链
   - Token 与 DownloadResource 绑定，永久有效

2. **更换网盘链接时二维码无需变化**
   - 管理员在后台修改 `download_resources.my_share_url` 即可
   - Token 不变 → 二维码不变 → 用户扫码后自动跳转到新链接

3. **Token 唯一性**
   - 每个 DownloadResource 在同一状态下只有一个有效 Token
   - 数据库层面 `UNIQUE(resource_id, status)` 约束保证

4. **下载日志预留**
   - `download_logs` 表记录每次 view / redirect 行为
   - 包含 IP、User-Agent、设备类型、操作类型
   - 为后续下载统计模块准备

### 数据模型

**download_tokens**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 主键 |
| token | VARCHAR(64) UNIQUE | 随机 Token |
| resource_id | INTEGER FK | 关联 download_resources |
| game_id | INTEGER FK | 关联 games（冗余） |
| provider_code | VARCHAR(20) | 网盘代码 |
| status | VARCHAR(20) | active / disabled |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

唯一约束：`(resource_id, status)`

**download_logs**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 主键 |
| token | VARCHAR(64) | 下载 Token |
| resource_id | INTEGER | 关联资源 |
| game_id | INTEGER | 关联游戏 |
| ip_address | VARCHAR(45) | 用户 IP |
| user_agent | TEXT | User-Agent |
| device_type | VARCHAR(20) | pc / mobile / unknown |
| action | VARCHAR(20) | view / redirect |
| created_at | DATETIME | 创建时间 |

### API 路由

| 路由 | 说明 |
|------|------|
| `GET /download/{resource_id}` | 统一下载入口 |
| `GET /d/{token}` | Token 链接（二维码目标） |
| `GET /api/download/qr/{token}` | 二维码 PNG 图片 |
| `GET /api/game/{game_id}/download-resources` | 游戏下载资源列表 |

### 分层

```
Controller (download_controller.py)
    |
Service (download_service.py)
    |
Model (download_token.py, download_log.py)
    |
Database (download_tokens, download_logs)
```
