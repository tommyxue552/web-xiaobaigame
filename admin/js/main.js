/**
 * 小白游戏资源站 - 后台管理脚本
 * ================================
 * 管理游戏资源，包含仪表盘、游戏管理、分类管理等模块。
 */

(function () {
    "use strict";

    // ==================== DOM 工具 ====================
    const $ = (sel) => document.querySelector(sel);
    const $$ = (sel) => document.querySelectorAll(sel);

    // ==================== 导航菜单配置 ====================
    const MENUS = [
        { id: "dashboard",      label: "仪表盘",       icon: "\u25A0", hidden: false },
        { id: "games",          label: "游戏管理",     icon: "\u25B6", hidden: false },
        { id: "categories",     label: "分类管理",     icon: "\u25CB", hidden: false },
        { id: "tags",           label: "标签管理",     icon: "\u2605", hidden: false },
        { id: "resources",      label: "资源管理",     icon: "\u2193", hidden: false },
        { id: "crawler",        label: "采集管理",     icon: "\u21C4", hidden: true  },
        { id: "transfer",       label: "资源中转",     icon: "\u21C5", hidden: true  },
        { id: "ai",             label: "AI助手",       icon: "\u2699", hidden: true  },
        { id: "settings",       label: "系统设置",     icon: "\u2630", hidden: false },
    ];

    // ==================== 状态管理 ====================
    const state = {
        currentMenu: "dashboard",
        games: { items: [], total: 0, page: 1, pageSize: 20 },
        categories: ["动作", "冒险", "角色扮演", "策略", "模拟", "射击", "体育", "竞速", "休闲"],
        tags: ["单机", "联机", "中文", "破解版", "硬盘版", "免安装"],
    };

    // ==================== 初始化导航 ====================
    function initSidebar() {
        const nav = $(".sidebar-nav");
        let html = "";
        let inHidden = false;

        MENUS.forEach((menu) => {
            if (menu.hidden && !inHidden) {
                html += `<div class="nav-divider">扩展功能（待开发）</div>`;
                inHidden = true;
            }
            html += `
                <div class="nav-item ${menu.hidden ? "hidden-menu" : ""} ${menu.id === state.currentMenu ? "active" : ""}"
                     data-menu="${menu.id}">
                    <span class="nav-icon">${menu.icon}</span>
                    <span>${menu.label}</span>
                </div>`;
        });

        nav.innerHTML = html;

        // 导航点击事件
        nav.addEventListener("click", (e) => {
            const item = e.target.closest(".nav-item");
            if (!item) return;
            const menuId = item.dataset.menu;
            if (menuId) switchMenu(menuId);
        });
    }

    function switchMenu(menuId) {
        state.currentMenu = menuId;

        // 更新导航激活状态
        $$(".nav-item").forEach((el) => {
            el.classList.toggle("active", el.dataset.menu === menuId);
        });

        // 更新页面标题
        const menu = MENUS.find((m) => m.id === menuId);
        $(".main-header h2").textContent = menu ? menu.label : "";

        // 渲染对应页面
        renderPage(menuId);
    }

    // ==================== 页面渲染 ====================

    function renderPage(menuId) {
        const body = $(".main-body");

        switch (menuId) {
            case "dashboard":
                renderDashboard(body);
                break;
            case "games":
                renderGameManagement(body);
                break;
            case "categories":
                renderCategoryManagement(body);
                break;
            case "tags":
                renderTagManagement(body);
                break;
            case "resources":
                renderResourceManagement(body);
                break;
            case "crawler":
            case "transfer":
            case "ai":
                renderPlaceholder(body, MENUS.find((m) => m.id === menuId));
                break;
            case "settings":
                renderSettings(body);
                break;
            default:
                body.innerHTML = `<div class="empty-state"><p>页面不存在</p></div>`;
        }
    }

    // ---------- 仪表盘 ----------
    async function renderDashboard(body) {
        // 尝试获取统计数据
        let totalGames = 0;
        let publishedGames = 0;
        let draftGames = 0;
        try {
            const res = await fetch("/api/admin/games?page=1&page_size=1");
            if (res.ok) {
                const data = await res.json();
                totalGames = data.data?.total || 0;
            }
            const resPub = await fetch("/api/admin/games?page=1&page_size=1&publish_status=published");
            if (resPub.ok) {
                const data = await resPub.json();
                publishedGames = data.data?.total || 0;
            }
            const resDraft = await fetch("/api/admin/games?page=1&page_size=1&publish_status=draft");
            if (resDraft.ok) {
                const data = await resDraft.json();
                draftGames = data.data?.total || 0;
            }
        } catch (e) { /* 后端未启动时使用默认值 */ }

        body.innerHTML = `
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-label">游戏总数</div>
                    <div class="stat-value">${totalGames}</div>
                    <div class="stat-sub">全部游戏资源</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">已发布</div>
                    <div class="stat-value">${publishedGames}</div>
                    <div class="stat-sub">前台可见</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">草稿</div>
                    <div class="stat-value">${draftGames}</div>
                    <div class="stat-sub">待编辑发布</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">系统状态</div>
                    <div class="stat-value" style="font-size:1.2rem;color:#2e7d32;">运行中</div>
                    <div class="stat-sub">v1.0.0</div>
                </div>
            </div>
            <div class="panel">
                <div class="panel-header"><h3>快速操作</h3></div>
                <div class="panel-body" style="padding:20px;">
                    <button class="btn btn-primary" onclick="document.querySelector('.nav-item[data-menu=games]').click()">
                        管理游戏资源
                    </button>
                    <span style="color:#888;margin-left:12px;font-size:0.85rem;">前往游戏管理进行增删改查操作</span>
                </div>
            </div>
        `;
    }

    // ---------- 游戏管理 ----------
    async function renderGameManagement(body) {
        body.innerHTML = `
            <div class="panel">
                <div class="panel-header">
                    <h3>游戏列表</h3>
                    <button class="btn btn-primary add-game-btn">+ 添加游戏</button>
                </div>
                <div class="panel-body">
                    <div class="game-table-container">
                        <p style="padding:20px;color:#888;">加载中...</p>
                    </div>
                </div>
            </div>
            <!-- 添加/编辑游戏弹窗 -->
            <div class="modal-overlay game-modal">
                <div class="modal">
                    <div class="modal-header">
                        <h3>添加游戏</h3>
                        <button class="modal-close-btn">&times;</button>
                    </div>
                    <div class="modal-body">
                        <form id="game-form">
                            <div class="form-row">
                                <div class="form-group">
                                    <label>游戏标题 *</label>
                                    <input name="title" required placeholder="输入游戏标题">
                                </div>
                                <div class="form-group">
                                    <label>URL 标识 *</label>
                                    <input name="slug" required placeholder="如 grand-theft-auto-v">
                                </div>
                            </div>
                            <div class="form-row">
                                <div class="form-group">
                                    <label>封面图片 URL</label>
                                    <input name="cover" placeholder="https://...">
                                </div>
                                <div class="form-group">
                                    <label>分类</label>
                                    <select name="category">
                                        <option value="">请选择分类</option>
                                        ${state.categories.map((c) => `<option value="${c}">${c}</option>`).join("")}
                                    </select>
                                </div>
                            </div>
                            <div class="form-row">
                                <div class="form-group">
                                    <label>运行平台</label>
                                    <input name="system" placeholder="如 Windows/Mac/Linux">
                                </div>
                                <div class="form-group">
                                    <label>语言</label>
                                    <input name="language" placeholder="如 中文/英文">
                                </div>
                            </div>
                            <div class="form-row">
                                <div class="form-group">
                                    <label>文件大小</label>
                                    <input name="size" placeholder="如 50GB">
                                </div>
                                <div class="form-group">
                                    <label>版本号</label>
                                    <input name="version" placeholder="如 v1.2.3">
                                </div>
                            </div>
                            <div class="form-row">
                                <div class="form-group">
                                    <label>发行商</label>
                                    <input name="publisher">
                                </div>
                                <div class="form-group">
                                    <label>开发商</label>
                                    <input name="developer">
                                </div>
                            </div>
                            <div class="form-row">
                                <div class="form-group">
                                    <label>发布日期</label>
                                    <input name="release_date" type="date">
                                </div>
                                <div class="form-group">
                                    <label>发布状态</label>
                                    <select name="publish_status">
                                        <option value="draft">草稿</option>
                                        <option value="published">已发布</option>
                                        <option value="hidden">隐藏</option>
                                    </select>
                                </div>
                            </div>
                            <div class="form-group">
                                <label>标签（逗号分隔）</label>
                                <input name="tags_str" placeholder="单机, 动作, 中文">
                            </div>
                            <div class="form-group">
                                <label>下载链接</label>
                                <input name="download_url" placeholder="https://...">
                            </div>
                            <div class="form-group">
                                <label>原始来源 URL</label>
                                <input name="original_url" placeholder="https://...">
                            </div>
                            <div class="form-group">
                                <label>游戏描述</label>
                                <textarea name="description" rows="4" placeholder="输入游戏简介..."></textarea>
                            </div>
                            <input type="hidden" name="id" value="">
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button class="btn btn-outline modal-cancel-btn">取消</button>
                        <button class="btn btn-primary modal-save-btn">保存</button>
                    </div>
                </div>
            </div>
        `;

        await loadGameTable();
        bindGameEvents();
    }

    async function loadGameTable() {
        const container = $(".game-table-container");
        if (!container) return;

        try {
            const res = await fetch(
                `/api/admin/games?page=${state.games.page}&page_size=${state.games.pageSize}`
            );
            const data = await res.json();
            if (data.code === 0) {
                state.games.items = data.data.items;
                state.games.total = data.data.total;
                renderGameTable(container);
            }
        } catch (e) {
            container.innerHTML = `<div class="empty-state"><p>加载失败，请确认后端服务已启动</p></div>`;
        }
    }

    function renderGameTable(container) {
        const games = state.games.items;
        if (games.length === 0) {
            container.innerHTML = `<div class="empty-state"><p>暂无游戏数据，点击"添加游戏"开始</p></div>`;
            return;
        }
        let html = `<table>
            <thead><tr>
                <th>ID</th><th>封面</th><th>标题</th><th>分类</th><th>平台</th>
                <th>状态</th><th>中转</th><th>创建时间</th><th>操作</th>
            </tr></thead><tbody>`;
        games.forEach((g) => {
            const statusClass = `badge-${g.publish_status}`;
            const statusLabel = { published: "已发布", draft: "草稿", hidden: "隐藏" }[g.publish_status] || g.publish_status;
            const transferClass = `badge-${g.transfer_status}`;
            const transferLabel = { pending: "待中转", transferring: "中转中", completed: "已完成", failed: "失败" }[g.transfer_status] || g.transfer_status;
            html += `<tr>
                <td>${g.id}</td>
                <td><img src="${g.cover || "/frontend/images/placeholder.svg"}"
                         style="width:48px;height:30px;object-fit:cover;border-radius:4px;background:#eee;"
                         onerror="this.src='/frontend/images/placeholder.svg'"></td>
                <td><strong>${escHtml(g.title)}</strong></td>
                <td>${escHtml(g.category || "-")}</td>
                <td>${escHtml(g.system || "-")}</td>
                <td><span class="badge ${statusClass}">${statusLabel}</span></td>
                <td><span class="badge ${transferClass}">${transferLabel}</span></td>
                <td>${(g.created_at || "").slice(0, 10)}</td>
                <td>
                    <button class="btn btn-sm btn-outline edit-btn" data-id="${g.id}">编辑</button>
                    <button class="btn btn-sm btn-danger delete-btn" data-id="${g.id}">删除</button>
                </td>
            </tr>`;
        });
        html += "</tbody></table>";
        container.innerHTML = html;
    }

    function bindGameEvents() {
        // 添加游戏按钮
        $(".add-game-btn")?.addEventListener("click", () => {
            const form = $("#game-form");
            form.reset();
            form.querySelector("[name=id]").value = "";
            $(".game-modal .modal-header h3").textContent = "添加游戏";
            $(".game-modal").classList.add("active");
        });

        // 关闭弹窗
        $(".modal-close-btn")?.addEventListener("click", closeGameModal);
        $(".modal-cancel-btn")?.addEventListener("click", closeGameModal);
        $(".game-modal")?.addEventListener("click", (e) => {
            if (e.target === e.currentTarget) closeGameModal();
        });

        // 保存游戏
        $(".modal-save-btn")?.addEventListener("click", saveGame);

        // 编辑与删除（事件委托）
        $(".game-table-container")?.addEventListener("click", async (e) => {
            const editBtn = e.target.closest(".edit-btn");
            const deleteBtn = e.target.closest(".delete-btn");

            if (editBtn) {
                const id = editBtn.dataset.id;
                const game = state.games.items.find((g) => g.id == id);
                if (game) openEditModal(game);
            }

            if (deleteBtn) {
                const id = deleteBtn.dataset.id;
                if (confirm("确定删除该游戏吗？此操作不可恢复。")) {
                    await deleteGame(id);
                }
            }
        });
    }

    function closeGameModal() {
        $(".game-modal").classList.remove("active");
    }

    async function saveGame() {
        const form = $("#game-form");
        const formData = new FormData(form);
        const id = formData.get("id");

        // 处理 tags：逗号分隔转数组
        const tagsStr = formData.get("tags_str") || "";
        const tags = tagsStr.split(",").map((t) => t.trim()).filter(Boolean);

        const payload = {
            title: formData.get("title"),
            slug: formData.get("slug"),
            cover: formData.get("cover") || "",
            images: [],
            description: formData.get("description") || "",
            system: formData.get("system") || "",
            language: formData.get("language") || "",
            size: formData.get("size") || "",
            version: formData.get("version") || "",
            publisher: formData.get("publisher") || "",
            developer: formData.get("developer") || "",
            release_date: formData.get("release_date") || null,
            category: formData.get("category") || "",
            tags: tags,
            download_url: formData.get("download_url") || "",
            original_url: formData.get("original_url") || "",
            publish_status: formData.get("publish_status") || "draft",
        };

        try {
            let res;
            if (id) {
                res = await fetch(`/api/admin/game/${id}`, {
                    method: "PUT",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload),
                });
            } else {
                res = await fetch("/api/admin/game", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload),
                });
            }
            const data = await res.json();
            if (data.code === 0) {
                alert(id ? "更新成功" : "创建成功");
                closeGameModal();
                await loadGameTable();
            } else {
                alert("操作失败: " + (data.message || "未知错误"));
            }
        } catch (e) {
            alert("请求失败: " + e.message);
        }
    }

    function openEditModal(game) {
        const form = $("#game-form");
        form.querySelector("[name=id]").value = game.id;
        form.querySelector("[name=title]").value = game.title;
        form.querySelector("[name=slug]").value = game.slug;
        form.querySelector("[name=cover]").value = game.cover;
        form.querySelector("[name=category]").value = game.category;
        form.querySelector("[name=system]").value = game.system;
        form.querySelector("[name=language]").value = game.language;
        form.querySelector("[name=size]").value = game.size;
        form.querySelector("[name=version]").value = game.version;
        form.querySelector("[name=publisher]").value = game.publisher;
        form.querySelector("[name=developer]").value = game.developer;
        form.querySelector("[name=release_date]").value = game.release_date || "";
        form.querySelector("[name=publish_status]").value = game.publish_status;
        form.querySelector("[name=tags_str]").value = (game.tags || []).join(", ");
        form.querySelector("[name=download_url]").value = game.download_url;
        form.querySelector("[name=original_url]").value = game.original_url;
        form.querySelector("[name=description]").value = game.description;
        $(".game-modal .modal-header h3").textContent = "编辑游戏";
        $(".game-modal").classList.add("active");
    }

    async function deleteGame(id) {
        try {
            const res = await fetch(`/api/admin/game/${id}`, { method: "DELETE" });
            const data = await res.json();
            if (data.code === 0) {
                await loadGameTable();
            } else {
                alert("删除失败: " + data.message);
            }
        } catch (e) {
            alert("请求失败: " + e.message);
        }
    }

    // ---------- 分类管理 ----------
    function renderCategoryManagement(body) {
        body.innerHTML = `
            <div class="panel">
                <div class="panel-header">
                    <h3>分类管理</h3>
                    <button class="btn btn-primary" id="add-category-btn">+ 添加分类</button>
                </div>
                <div class="panel-body" style="padding:0;">
                    <table>
                        <thead><tr><th>序号</th><th>分类名称</th><th>游戏数量</th><th>操作</th></tr></thead>
                        <tbody id="category-tbody">
                            ${state.categories.map((c, i) => `
                                <tr>
                                    <td>${i + 1}</td>
                                    <td>${escHtml(c)}</td>
                                    <td>-</td>
                                    <td>
                                        <button class="btn btn-sm btn-outline">编辑</button>
                                        <button class="btn btn-sm btn-danger">删除</button>
                                    </td>
                                </tr>
                            `).join("")}
                        </tbody>
                    </table>
                </div>
            </div>
        `;
    }

    // ---------- 标签管理 ----------
    function renderTagManagement(body) {
        body.innerHTML = `
            <div class="panel">
                <div class="panel-header">
                    <h3>标签管理</h3>
                    <button class="btn btn-primary" id="add-tag-btn">+ 添加标签</button>
                </div>
                <div class="panel-body" style="padding:0;">
                    <table>
                        <thead><tr><th>序号</th><th>标签名称</th><th>关联游戏</th><th>操作</th></tr></thead>
                        <tbody>
                            ${state.tags.map((t, i) => `
                                <tr>
                                    <td>${i + 1}</td>
                                    <td><span class="badge" style="background:#eef2ff;color:#4f46e5;">${escHtml(t)}</span></td>
                                    <td>-</td>
                                    <td>
                                        <button class="btn btn-sm btn-outline">编辑</button>
                                        <button class="btn btn-sm btn-danger">删除</button>
                                    </td>
                                </tr>
                            `).join("")}
                        </tbody>
                    </table>
                </div>
            </div>
        `;
    }

    // ---------- 资源管理 ----------
    function renderResourceManagement(body) {
        body.innerHTML = `
            <div class="panel">
                <div class="panel-header"><h3>资源文件管理</h3></div>
                <div class="panel-body">
                    <div class="empty-state">
                        <p>资源中转模块尚未启用</p>
                        <p style="font-size:0.85rem;color:#bbb;margin-top:8px;">
                            此处将展示已中转的游戏资源文件，支持查看、清理、重新中转等操作。
                        </p>
                    </div>
                </div>
            </div>
        `;
    }

    // ---------- 系统设置 ----------
    function renderSettings(body) {
        body.innerHTML = `
            <div class="panel">
                <div class="panel-header"><h3>系统设置</h3></div>
                <div class="panel-body" style="padding:20px;">
                    <div class="form-group">
                        <label>站点名称</label>
                        <input value="小白游戏资源站" disabled>
                    </div>
                    <div class="form-group">
                        <label>API 版本</label>
                        <input value="v1.0.0" disabled>
                    </div>
                    <div class="form-group">
                        <label>数据库类型</label>
                        <input value="SQLite（可切换 MySQL/PostgreSQL）" disabled>
                    </div>
                    <div class="form-group">
                        <label>采集程序状态</label>
                        <input value="未启用（预留接口已就绪）" disabled>
                    </div>
                    <div class="form-group">
                        <label>资源中转状态</label>
                        <input value="未启用（预留接口已就绪）" disabled>
                    </div>
                    <div class="form-group">
                        <label>AI 助手状态</label>
                        <input value="未启用（预留接口已就绪）" disabled>
                    </div>
                    <p style="font-size:0.8rem;color:#888;margin-top:16px;">
                        以上设置为只读展示。后续可通过配置文件或环境变量进行修改。
                    </p>
                </div>
            </div>
        `;
    }

    // ---------- 占位页面（隐藏菜单） ----------
    function renderPlaceholder(body, menu) {
        body.innerHTML = `
            <div class="placeholder-page">
                <div class="placeholder-icon">\u{1F6A7}</div>
                <h3>${menu.label} - 功能开发中</h3>
                <p>此模块为预留功能，将在后续版本中实现。</p>
                <p style="font-size:0.8rem;color:#bbb;margin-top:8px;">相关 API 接口已预留，可直接对接外部程序。</p>
            </div>
        `;
    }

    // ==================== 工具函数 ====================
    function escHtml(str) {
        const div = document.createElement("div");
        div.textContent = str;
        return div.innerHTML;
    }

    // ==================== 启动 ====================
    function init() {
        initSidebar();
        renderPage(state.currentMenu);
    }

    document.addEventListener("DOMContentLoaded", init);
})();
