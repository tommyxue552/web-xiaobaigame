# 小白游戏资源站 (web-xiaobaigame)

## 项目定位

小白游戏资源站是一个**游戏资源分享网站**，面向中文用户提供单机游戏资源的浏览、搜索与下载服务。项目采用前后端分离架构，后端使用 FastAPI + SQLAlchemy，前端使用原生 HTML/CSS/JavaScript，数据库使用 SQLite。

## 产品目标

1. **游戏资源聚合展示** — 提供结构化的游戏信息浏览体验，包括封面、截图、分类、标签、元数据等
2. **多渠道下载支持** — 支持百度网盘、夸克网盘、阿里云盘、115网盘、迅雷云盘、UC网盘、中国移动云盘、天翼云盘等8种下载渠道
3. **自动化资源采集** — 通过独立的 `xiaobai-game-collector` 采集程序批量导入游戏数据，web 与 collector 解耦
4. **SEO 友好** — 服务端渲染游戏详情页，支持 sitemap.xml、robots.txt、结构化数据（JSON-LD）
5. **后台管理** — 提供完整的后台管理系统，支持游戏 CRUD、分类管理、下载资源管理、渠道管理

## 用户流程

### 前台用户

```
首页 (/)
 ├── 分类导航 → 筛选游戏
 ├── 搜索框 → 关键词搜索
 ├── 最新游戏 → 游戏卡片网格
 ├── 热门推荐 → 游戏卡片网格
 └── 点击卡片 → 游戏详情页 (/game/{slug})
                    ├── 封面 + 元数据
                    ├── 游戏截图（灯箱查看）
                    ├── 游戏简介
                    ├── 下载渠道按钮（多网盘）
                    └── 点击下载 → 统一下载页 (/download/{resourceId})
                                      ├── PC端 → 展示二维码（扫码用手机下载）
                                      └── 移动端 → 302跳转网盘直链
```

### 后台管理员

```
登录 (/admin/login.html)
 └── 仪表盘 → 数据概览（游戏总数、发布数、草稿数等）
       ├── 游戏管理 → 增删改查游戏
       ├── 分类管理 → 增删改查分类
       └── 下载资源 → 管理每个游戏的下载渠道、提取码、分享链接
```

### 采集程序

```
xiaobai-game-collector (独立程序)
 └── POST /api/crawler/import (携带 Collector-Key)
       └── 批量导入游戏 → 自动去重（基于 original_url）→ 状态设为 draft
```

## 当前版本

**v0.7.4** — 下载控制器模块完成，支持 Token 化下载 + 设备分流（PC 二维码 / 移动端 302 跳转）

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | FastAPI 0.115 |
| ORM | SQLAlchemy 2.0 (async) |
| 数据库 | SQLite (aiosqlite) |
| 认证 | JWT (python-jose) |
| 密码 | bcrypt (passlib) |
| 前端 | 原生 HTML/CSS/JS |
| 容器化 | Docker + docker-compose |
| 二维码 | qrcode + Google Chart API (fallback) |
