# 项目开发规范

## 代码风格

### Python（后端）

- **框架**: FastAPI 0.115
- **异步**: 所有数据库操作使用 `AsyncSession`，路由函数使用 `async def`
- **类型标注**: Pydantic v2 模型用于请求/响应验证
- **配置**: 通过 `pydantic-settings` 从 `.env` 文件加载，`core/config.py` 统一管理
- **文件编码**: UTF-8（含 BOM 头统一处理）
- **依赖注入**: 数据库会话通过 `Depends(get_db)` 注入
- **异常**: 使用 FastAPI 的 `HTTPException`，返回标准错误格式
- **模型序列化**: Controller 层使用自定义 `serialize_*` 函数而非 model_dump

### JavaScript（前端）

- **模块模式**: 使用 IIFE（立即执行函数表达式）避免全局污染
- **零依赖**: 不使用 npm/webpack，原生 DOM API
- **DOM 选择器**: 统一使用 `$`(querySelector) / `$$`(querySelectorAll) 辅助函数
- **事件委托**: 列表项事件通过父级容器委托处理
- **安全**: 所有动态内容使用 `esc()` 函数进行 HTML 转义

### SQL（数据库）

- **文件**: schema.sql 为权威表结构定义
- **ORM 同步**: SQLAlchemy 模型字段需与 schema.sql 保持一致
- **迁移**: 增量 SQL 文件放在 `database/migrations/` 目录

---

## 禁止修改 Collector 原则

`xiaobai-game-collector` 是独立的采集程序，不在本仓库中。以下原则必须遵守：

1. **不修改 collector 代码**: collector 是独立项目，本仓库仅提供导入接口
2. **接口稳定性**: `POST /api/crawler/import` 的请求/响应格式变更需评估对 collector 的影响
3. **original_url 去重**: 采集接口的去重逻辑基于 `original_url` 字段，修改此逻辑会影响 collector 的导入行为
4. **Collector-Key 认证**: 认证 Key 通过 `settings.COLLECTOR_KEY` 管理，修改 Key 需同步更新 collector 配置
5. **导入状态**: collector 导入的游戏默认 `draft` 状态，该约定不应更改

---

## 模块开发流程

### 新增模块

1. **数据模型** — 在 `backend/app/models/` 创建 ORM 模型文件，并在 `models/__init__.py` 中导入
2. **Schema 同步** — 在 `database/schema.sql` 中添加对应的 CREATE TABLE 语句
3. **API 路由** — 在 `backend/app/api/` 创建路由模块
4. **路由注册** — 在 `backend/app/main.py` 中 `include_router`
5. **服务层** (可选) — 复杂业务逻辑在 `backend/app/services/` 中实现
6. **前端页面** (可选) — 在 `frontend/` 或 `admin/` 添加对应页面
7. **文档更新** — 更新 `docs/API.md` 和 `docs/MODULES.md`

### 修改现有模块

1. **兼容性优先**: 新增字段应有默认值，修改字段类型需考虑兼容性
2. **测试验证**: 修改 API 后验证 Swagger 文档 (`/docs`) 正确
3. **前端同步**: API 变更需同步更新前端 JS 中对应的 fetch 调用和渲染逻辑

### 数据库迁移

1. 修改 `database/schema.sql` 对应表结构
2. 在 `database/migrations/` 创建增量迁移 SQL 文件，命名格式: `{序号}_{描述}.sql`
3. SQLAlchemy 模型同步更新字段定义
4. ORM `create_all` 自动处理新表，但字段修改建议手动执行迁移 SQL

---

## 文件组织规范

```
web-xiaobaigame/
├── admin/            # 后台管理前端（独立 SPA）
│   ├── css/          # 管理后台样式
│   ├── js/           # 管理后台脚本（main.js 为 SPA 入口）
│   ├── images/       # 管理后台图片
│   ├── login.html    # 登录页
│   └── index.html    # 管理后台主页
├── api/              # 独立 API 模块入口（预留，当前为空壳）
├── backend/          # 后端 Python 代码
│   └── app/
│       ├── main.py           # FastAPI 入口
│       ├── core/             # 配置、数据库引擎、认证
│       ├── models/           # SQLAlchemy ORM 模型
│       ├── api/              # API 路由控制器
│       └── services/         # 业务服务层
├── database/         # 数据库相关
│   ├── schema.sql            # 表结构定义
│   ├── xiaobaigame.db        # SQLite 数据文件
│   ├── migrations/           # 增量迁移 SQL
│   └── seeds/                # 种子数据脚本
├── docker/           # Docker 配置
├── docs/             # 项目文档
├── frontend/         # 前台前端
│   ├── css/          # 全局样式
│   ├── js/           # 前台脚本
│   ├── images/       # 前台图片
│   └── *.html        # 前台页面
├── logs/             # 日志文件
├── screenshots/      # 截图（开发用）
├── storage/          # 中转存储目录
└── uploads/          # 上传文件目录
    ├── covers/       # 游戏封面
    └── games/        # 游戏文件
```

---

## 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 表名 | 蛇形命名，复数 | `download_resources` |
| 模型类 | PascalCase，单数 | `DownloadResource` |
| API 路由 | 蛇形路径，资源用复数 | `/api/admin/download-resources` |
| 函数 | 蛇形命名 | `get_or_create_token` |
| 文件 | 蛇形命名 | `download_service.py` |
| 前端 JS 变量 | camelCase | `activeCategory` |
| 前端 JS 函数 | camelCase | `renderGameCards` |
| CSS 类 | kebab-case | `game-card`, `detail-hero` |

---

## 安全规范

1. **JWT 认证**: 管理接口强制要求 Bearer Token，401 时前端自动跳转登录页
2. **密码存储**: 使用 bcrypt 哈希，不存储明文密码
3. **Collector-Key**: 采集接口的 API Key 验证，防止未授权导入
4. **SQL 注入防护**: 全部使用 SQLAlchemy 参数化查询，无裸 SQL 拼接
5. **XSS 防护**: 前端所有动态内容通过 `esc()` 函数 HTML 转义
6. **CORS**: 配置 `ALLOWED_ORIGINS`，开发阶段允许所有来源
7. **secret 管理**: JWT Secret Key 和 Collector Key 通过 `.env` 管理，不硬编码在代码中（代码中仅有开发默认值）

---

## 部署规范

1. **Docker**: 使用 `docker/Dockerfile` + `docker-compose.yml` 容器化部署
2. **持久化**: 数据库、上传文件、存储目录通过 Volume 挂载
3. **环境变量**: 通过 docker-compose 的 `environment` 或 `.env` 文件配置
4. **端口**: 默认 8000，通过环境变量 `PORT` 可修改
5. **生产环境**: 设置 `DEBUG=false`，修改默认 JWT Secret 和 Collector Key
