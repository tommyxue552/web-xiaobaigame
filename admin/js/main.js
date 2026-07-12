/**
 * 小白游戏资源站- 后台管理脚本
 * ================================
 * 管理游戏资源，包含仪表盘、游戏管理、分类管理等模块。 * 所有API 请求均携带JWT 认证令牌。 */

(function () {
    "use strict";

    // ==================== DOM 工具 ====================
    const $ = (sel) => document.querySelector(sel);
    const $$ = (sel) => document.querySelectorAll(sel);

    // ==================== Auth 工具 ====================
    function getToken() { return localStorage.getItem("admin_token"); }
    function getUsername() { return localStorage.getItem("admin_username") || "管理员"; }
    function clearAuth() { localStorage.removeItem("admin_token"); localStorage.removeItem("admin_username"); }

    async function apiFetch(url, options) {
        if (!options) options = {};
        if (!options.headers) options.headers = {};
        var token = getToken();
        if (token) options.headers["Authorization"] = "Bearer " + token;
        if (options.body && typeof options.body === "object" && !(options.body instanceof FormData)) {
            options.headers["Content-Type"] = "application/json";
            options.body = JSON.stringify(options.body);
        }
        var res = await fetch(url, options);
        if (res.status === 401) { clearAuth(); window.location.href = "/admin/login.html"; throw new Error("认证已过期"); }
        return res;
    }

    async function checkAuth() {
        var token = getToken();
        if (!token) { window.location.href = "/admin/login.html"; return false; }
        try {
            var res = await apiFetch("/api/admin/me");
            if (!res.ok) { clearAuth(); window.location.href = "/admin/login.html"; return false; }
            return true;
        } catch (e) { clearAuth(); window.location.href = "/admin/login.html"; return false; }
    }

    function handleLogout() { clearAuth(); window.location.href = "/admin/login.html"; }

    // ==================== 导航配置 ====================
    var MENUS = [
        { id: "dashboard", label: "仪表盘", icon: "\u25A0" },
        { id: "games", label: "游戏管理", icon: "\u25B6" },
        { id: "categories", label: "分类管理", icon: "\u25CB" },
        { id: "resources", label: "下载资源", icon: "\u2193" },
        { id: "crawler", label: "采集管理", icon: "\u21C4", hidden: true },
        { id: "transfer", label: "资源中转", icon: "\u21C5", hidden: true },
        { id: "ai", label: "AI助手", icon: "\u2699", hidden: true },
        { id: "settings", label: "系统设置", icon: "\u2630" },
    ];

    // ==================== 状态====================
    var state = {
        currentMenu: "dashboard",
        games: { items: [], total: 0, page: 1, pageSize: 20 },
        gameFilter: { keyword: "", publishStatus: "", category: "" },
        categories: [],
    };

    // ==================== 工具函数 ====================
    function escHtml(str) {
        if (!str) return "";
        var div = document.createElement("div");
        div.textContent = str;
        return div.innerHTML;
    }
    function statusLabel(s) { var m = { published: "已发布", draft: "草稿", hidden: "隐藏" }; return m[s] || s; }
    function transferLabel(s) { var m = { pending: "待中转", transferring: "中转中", completed: "已完成", failed: "失败" }; return m[s] || s; }
    function debounce(fn, delay) { var t; return function() { var ctx=this, a=arguments; clearTimeout(t); t=setTimeout(function(){fn.apply(ctx,a)},delay); }; }

    // ==================== 侧栏导航 ====================
    function initSidebar() {
        var nav = $(".sidebar-nav");
        var html = ""; var inHidden = false;
        MENUS.forEach(function(m) {
            if (m.hidden && !inHidden) { html += "<div class=\"nav-divider\">扩展功能（待开发）</div>"; inHidden = true; }
            html += "<div class=\"nav-item " + (m.hidden ? "hidden-menu" : "") + (m.id === state.currentMenu ? " active" : "") + "\" data-menu=\"" + m.id + "\"><span class=\"nav-icon\">" + m.icon + "</span><span>" + m.label + "</span></div>";
        });
        nav.innerHTML = html;
        nav.addEventListener("click", function(e) {
            var item = e.target.closest(".nav-item"); if (!item) return;
            switchMenu(item.dataset.menu);
        });
        var footer = $(".sidebar-footer");
        if (footer) {
            footer.innerHTML = "<span>" + escHtml(getUsername()) + "</span> | <span class=\"logout-link\" id=\"logout-btn\">退出/span>";
            document.getElementById("logout-btn").addEventListener("click", handleLogout);
        }
    }

    function switchMenu(menuId) {
        state.currentMenu = menuId;
        $$(".nav-item").forEach(function(el) { el.classList.toggle("active", el.dataset.menu === menuId); });
        var menu = MENUS.find(function(m) { return m.id === menuId; });
        $(".main-header h2").textContent = menu ? menu.label : "";
        renderPage(menuId);
    }

    // ==================== 页面路由 ====================
    function renderPage(menuId) {
        var body = $(".main-body");
        switch (menuId) {
        case "dashboard": renderDashboard(body); break;
        case "games": renderGameManagement(body); break;
        case "categories": renderCategoryManagement(body); break;
        case "resources": renderResourceManagement(body); break;
        case "settings": renderSettings(body); break;
        default: renderPlaceholder(body, MENUS.find(function(m){return m.id===menuId;})); break;
        }
    }

    // ==================== 仪表盘====================
    async function renderDashboard(body) {
        body.innerHTML = "<div style=\"padding:40px;text-align:center;color:#888;\">加载中..</div>";
        try {
            var res = await apiFetch("/api/admin/stats");
            var data = await res.json();
            if (data.code !== 0) throw new Error("获取统计数据失败");
            var stats = data.data;
            body.innerHTML =
                "<div class=\"stats-grid\">" +
                "<div class=\"stat-card\"><div class=\"stat-label\">游戏总数</div><div class=\"stat-value\">" + stats.total_games + "</div><div class=\"stat-sub\">全部游戏资源</div></div>" +
                "<div class=\"stat-card\"><div class=\"stat-label\">已发布/div><div class=\"stat-value\">" + stats.published_games + "</div><div class=\"stat-sub\">前台可见</div></div>" +
                "<div class=\"stat-card\"><div class=\"stat-label\">草稿</div><div class=\"stat-value\">" + stats.draft_games + "</div><div class=\"stat-sub\">待编辑发布/div></div>" +
                "<div class=\"stat-card\"><div class=\"stat-label\">分类数量</div><div class=\"stat-value\">" + stats.category_count + "</div><div class=\"stat-sub\">游戏分类</div></div>" +
                "</div>" +
                "<div class=\"panel\">" +
                "<div class=\"panel-header\"><h3>最近添加的游戏</h3></div>" +
                "<ul class=\"recent-list\">" +
                (stats.recent_games.length === 0
                    ? "<li style=\"justify-content:center;color:#888;\">暂无游戏数据</li>"
                    : stats.recent_games.map(function(g) {
                        return "<li>" +
                            "<img src=\"" + (g.cover || "/frontend/images/placeholder.svg") + "\" class=\"recent-cover\" onerror=\"this.src='/frontend/images/placeholder.svg'\">" +
                            "<span class=\"recent-title\">" + escHtml(g.title) + "</span>" +
                            "<span class=\"badge badge-" + g.publish_status + "\">" + statusLabel(g.publish_status) + "</span>" +
                            "<span class=\"recent-category\">" + escHtml(g.category || "-") + "</span>" +
                            "<span class=\"recent-time\">" + (g.created_at || "").slice(0, 10) + "</span>" +
                            "</li>";
                    }).join("")) +
                "</ul>" +
                "</div>" +
                "<div class=\"panel\" style=\"margin-top:16px;\">" +
                "<div class=\"panel-header\"><h3>系统状态/h3></div>" +
                "<div class=\"panel-body\" style=\"padding:20px;\">" +
                "<div style=\"display:flex;gap:20px;flex-wrap:wrap;\">" +
                "<div><span style=\"color:#888;font-size:0.85rem;\">API 版本</span><br><span style=\"font-weight:600;\">v1.0.0</span></div>" +
                "<div><span style=\"color:#888;font-size:0.85rem;\">数据库/span><br><span style=\"font-weight:600;\">SQLite</span></div>" +
                "<div><span style=\"color:#888;font-size:0.85rem;\">采集程序</span><br><span style=\"font-weight:600;color:#f57f17;\">待开发/span></div>" +
                "<div><span style=\"color:#888;font-size:0.85rem;\">资源中转</span><br><span style=\"font-weight:600;color:#f57f17;\">待开发/span></div>" +
                "<div><span style=\"color:#888;font-size:0.85rem;\">AI 助手</span><br><span style=\"font-weight:600;color:#f57f17;\">待开发/span></div>" +
                "</div></div></div>";
        } catch (e) {
            body.innerHTML = "<div class=\"empty-state\"><p>加载统计失败: " + escHtml(e.message) + "</p></div>";
        }
    }

    // ==================== 游戏管理 ====================
    function renderGameManagement(body) {
        body.innerHTML =
            "<div class=\"panel\">" +
            "<div class=\"panel-header\"><h3>游戏列表</h3><button class=\"btn btn-primary\" id=\"add-game-btn\">+ 添加游戏</button></div>" +
            "<div class=\"toolbar\">" +
            "<input type=\"text\" class=\"search-input\" id=\"game-search\" placeholder=\"搜索游戏标题...\">" +
            "<select id=\"game-status-filter\"><option value=\"\">全部状态/option><option value=\"published\">已发布/option><option value=\"draft\">草稿</option><option value=\"hidden\">隐藏</option></select>" +
            "<select id=\"game-category-filter\"><option value=\"\">全部分类</option></select>" +
            "<span class=\"toolbar-info\" id=\"game-count-info\"></span>" +
            "</div>" +
            "<div class=\"panel-body\"><div class=\"game-table-container\"><p style=\"padding:20px;color:#888;\">加载中..</p></div></div>" +
            "<div class=\"pagination\" id=\"game-pagination\"></div>" +
            "</div>" +
            // 游戏弹窗
            "<div class=\"modal-overlay game-modal\">" +
            "<div class=\"modal\">" +
            "<div class=\"modal-header\"><h3>添加游戏</h3><button class=\"modal-close-btn\">&times;</button></div>" +
            "<div class=\"modal-body\"><form id=\"game-form\">" +
            "<div class=\"form-row\"><div class=\"form-group\"><label>游戏标题 *</label><input name=\"title\" required placeholder=\"输入游戏标题\"></div>" +
            "<div class=\"form-group\"><label>URL 标识 *</label><input name=\"slug\" required placeholder=\"如grand-theft-auto-v\"></div></div>" +
            "<div class=\"form-row\"><div class=\"form-group\"><label>封面图片 URL</label><input name=\"cover\" placeholder=\"https://...\"></div>" +
            "<div class=\"form-group\"><label>分类</label><select name=\"category\" id=\"game-category-select\"><option value=\"\">请选择分类</option></select></div></div>" +
            "<div class=\"form-row\"><div class=\"form-group\"><label>运行平台</label><input name=\"system\" placeholder=\"如Windows/Mac/Linux\"></div>" +
            "<div class=\"form-group\"><label>语言</label><input name=\"language\" placeholder=\"如中文/英文\"></div></div>" +
            "<div class=\"form-row\"><div class=\"form-group\"><label>文件大小</label><input name=\"size\" placeholder=\"如50GB\"></div>" +
            "<div class=\"form-group\"><label>版本号/label><input name=\"version\" placeholder=\"如v1.2.3\"></div></div>" +
            "<div class=\"form-row\"><div class=\"form-group\"><label>发行商/label><input name=\"publisher\"></div>" +
            "<div class=\"form-group\"><label>开发商</label><input name=\"developer\"></div></div>" +
            "<div class=\"form-row\"><div class=\"form-group\"><label>发布日期</label><input name=\"release_date\" type=\"date\"></div>" +
            "<div class=\"form-group\"><label>发布状态/label><select name=\"publish_status\"><option value=\"draft\">草稿</option><option value=\"published\">已发布/option><option value=\"hidden\">隐藏</option></select></div></div>" +
            "<div class=\"form-group\"><label>标签（逗号分隔，/label><input name=\"tags_str\" placeholder=\"单机, 动作, 中文\"></div>" +
            "<div class=\"form-row\"><div class=\"form-group\"><label>下载链接</label><input name=\"download_url\" placeholder=\"https://...\"></div>" +
            "<div class=\"form-group\"><label>原始来源 URL</label><input name=\"original_url\" placeholder=\"https://...\"></div></div>" +
            "<div class=\"form-row\"><div class=\"form-group\"><label>中转状态/label><select name=\"transfer_status\"><option value=\"pending\">待中转/option><option value=\"transferring\">中转中/option><option value=\"completed\">已完成/option><option value=\"failed\">失败</option></select></div>" +
            "<div class=\"form-group\"><label>采集来源</label><input name=\"crawler_source\" placeholder=\"如steam\"></div></div>" +
            "<div class=\"form-group\"><label>游戏描述</label><textarea name=\"description\" rows=\"4\" placeholder=\"输入游戏简介..\"></textarea></div>" +
            "<input type=\"hidden\" name=\"id\" value=\"\">" +
            "</form></div>" +
            "<div class=\"modal-footer\"><button class=\"btn btn-outline modal-cancel-btn\">取消</button><button class=\"btn btn-primary modal-save-btn\">保存</button></div>" +
            "</div></div>";

        loadCategoriesForSelects();
        loadGameTable();
        bindGameEvents();
    }

    async function loadCategoriesForSelects() {
        try {
            var res = await apiFetch("/api/admin/categories");
            var data = await res.json();
            if (data.code === 0) {
                state.categories = data.data;
                var opts = state.categories.map(function(c) { return "<option value=\"" + escHtml(c.name) + "\">" + escHtml(c.name) + "</option>"; }).join("");
                var sel = document.getElementById("game-category-select");
                if (sel) sel.innerHTML = "<option value=\"\">请选择分类</option>" + opts;
                var fil = document.getElementById("game-category-filter");
                if (fil) fil.innerHTML = "<option value=\"\">全部分类</option>" + opts;
            }
        } catch (e) { console.error("加载分类失败:", e); }
    }

    async function loadGameTable() {
        var container = $(".game-table-container");
        if (!container) return;
        try {
            var params = "page=" + state.games.page + "&page_size=" + state.games.pageSize;
            if (state.gameFilter.keyword) params += "&keyword=" + encodeURIComponent(state.gameFilter.keyword);
            if (state.gameFilter.publishStatus) params += "&publish_status=" + encodeURIComponent(state.gameFilter.publishStatus);
            if (state.gameFilter.category) params += "&category=" + encodeURIComponent(state.gameFilter.category);
            var res = await apiFetch("/api/admin/games?" + params);
            var data = await res.json();
            if (data.code === 0) {
                state.games.items = data.data.items;
                state.games.total = data.data.total;
                renderGameTable();
                renderGamePagination();
                var info = document.getElementById("game-count-info");
                if (info) info.textContent = "共" + data.data.total + " 条";
            }
        } catch (e) { if (e.message.indexOf("认证") === -1) container.innerHTML = "<div class=\"empty-state\"><p>加载失败，请确认后端服务已启动/p></div>"; }
    }

    function renderGameTable() {
        var container = $(".game-table-container");
        var games = state.games.items;
        if (games.length === 0) { container.innerHTML = "<div class=\"empty-state\"><p>暂无游戏数据，点击「添加游戏」开始/p></div>"; return; }
        var html = "<table><thead><tr><th>ID</th><th>封面</th><th>标题</th><th>分类</th><th>大小</th><th>下载状态/th><th>发布</th><th>更新时间</th><th>操作</th></tr></thead><tbody>";
        games.forEach(function(g) {
            html += "<tr>" +
                "<td>" + g.id + "</td>" +
                "<td><img src=\"" + (g.cover || "/frontend/images/placeholder.svg") + "\" style=\"width:48px;height:30px;object-fit:cover;border-radius:4px;background:#eee;\" onerror=\"this.src='/frontend/images/placeholder.svg'\"></td>" +
                "<td><strong>" + escHtml(g.title) + "</strong></td>" +
                "<td>" + escHtml(g.category || "-") + "</td>" +
                "<td>" + escHtml(g.size || "-") + "</td>" +
                "<td><span class=\"badge badge-" + g.transfer_status + "\">" + transferLabel(g.transfer_status) + "</span></td>" +
                "<td><span class=\"badge badge-" + g.publish_status + "\">" + statusLabel(g.publish_status) + "</span></td>" +
                "<td>" + (g.updated_at || g.created_at || "").slice(0, 10) + "</td>" +
                "<td><button class=\"btn btn-sm btn-outline edit-btn\" data-id=\"" + g.id + "\">编辑</button> " +
                "<button class=\"btn btn-sm btn-danger delete-btn\" data-id=\"" + g.id + "\" data-title=\"" + escHtml(g.title) + "\">删除</button></td>" +
                "</tr>";
        });
        html += "</tbody></table>";
        container.innerHTML = html;
    }

    function renderGamePagination() {
        var pg = document.getElementById("game-pagination");
        if (!pg) return;
        var totalPages = Math.ceil(state.games.total / state.games.pageSize) || 1;
        var html = "<button " + (state.games.page <= 1 ? "disabled" : "") + " data-page=\"" + (state.games.page - 1) + "\">上一页/button>";
        var start = Math.max(1, state.games.page - 2);
        var end = Math.min(totalPages, state.games.page + 2);
        for (var i = start; i <= end; i++) {
            html += "<button class=\"" + (i === state.games.page ? "active" : "") + "\" data-page=\"" + i + "\">" + i + "</button>";
        }
        html += "<button " + (state.games.page >= totalPages ? "disabled" : "") + " data-page=\"" + (state.games.page + 1) + "\">下一页/button>";
        html += "<span class=\"page-info\">第" + state.games.page + "/" + totalPages + " 页/span>";
        pg.innerHTML = html;
        pg.querySelectorAll("button[data-page]").forEach(function(btn) {
            btn.addEventListener("click", function() { state.games.page = parseInt(btn.dataset.page); loadGameTable(); });
        });
    }

    function bindGameEvents() {
        document.getElementById("add-game-btn")?.addEventListener("click", function() {
            resetGameForm();
            $(".game-modal .modal-header h3").textContent = "添加游戏";
            $(".game-modal").classList.add("active");
            loadCategoriesForSelects();
        });
        $(".modal-close-btn")?.addEventListener("click", closeGameModal);
        $(".modal-cancel-btn")?.addEventListener("click", closeGameModal);
        $(".game-modal")?.addEventListener("click", function(e) { if (e.target === e.currentTarget) closeGameModal(); });
        $(".modal-save-btn")?.addEventListener("click", saveGame);

        $(".game-table-container")?.addEventListener("click", function(e) {
            var editBtn = e.target.closest(".edit-btn");
            var deleteBtn = e.target.closest(".delete-btn");
            if (editBtn) { var g = state.games.items.find(function(x) { return x.id == editBtn.dataset.id; }); if (g) openEditModal(g); }
            if (deleteBtn) { var id = deleteBtn.dataset.id; var t = deleteBtn.dataset.title || ("ID: " + id); if (confirm("确定删除游戏「" + t + "」吗？此操作不可恢复")) deleteGame(id); }
        });

        var si = document.getElementById("game-search");
        if (si) si.addEventListener("input", debounce(function() { state.gameFilter.keyword = si.value.trim(); state.games.page = 1; loadGameTable(); }, 400));
        var sf = document.getElementById("game-status-filter");
        if (sf) sf.addEventListener("change", function() { state.gameFilter.publishStatus = sf.value; state.games.page = 1; loadGameTable(); });
        var cf = document.getElementById("game-category-filter");
        if (cf) cf.addEventListener("change", function() { state.gameFilter.category = cf.value; state.games.page = 1; loadGameTable(); });
    }

    function closeGameModal() { $(".game-modal").classList.remove("active"); }

    function resetGameForm() { $("#game-form").reset(); $("#game-form [name=id]").value = ""; }

    async function saveGame() {
        var form = $("#game-form");
        var fd = new FormData(form);
        var id = fd.get("id");
        var ts = (fd.get("tags_str") || "").split(",").map(function(t) { return t.trim(); }).filter(Boolean);
        var payload = {
            title: fd.get("title"), slug: fd.get("slug"), cover: fd.get("cover") || "",
            images: [], description: fd.get("description") || "",
            system: fd.get("system") || "", language: fd.get("language") || "",
            size: fd.get("size") || "", version: fd.get("version") || "",
            publisher: fd.get("publisher") || "", developer: fd.get("developer") || "",
            release_date: fd.get("release_date") || null,
            category: fd.get("category") || "", tags: ts,
            download_url: fd.get("download_url") || "", original_url: fd.get("original_url") || "",
            transfer_status: fd.get("transfer_status") || "pending",
            crawler_source: fd.get("crawler_source") || "",
            seo_title: fd.get("seo_title") || "",
            seo_description: fd.get("seo_description") || "",
            seo_keywords: fd.get("seo_keywords") || "",
            publish_status: fd.get("publish_status") || "draft",
        };
        try {
            var res, url, method;
            if (id) { url = "/api/admin/game/" + id; method = "PUT"; }
            else { url = "/api/admin/game"; method = "POST"; }
            res = await apiFetch(url, { method: method, body: payload });
            var data = await res.json();
            if (data.code === 0) { alert(id ? "更新成功" : "创建成功"); closeGameModal(); await loadGameTable(); }
            else { alert("操作失败: " + (data.detail || data.message || "未知错误")); }
        } catch (e) { alert("请求失败: " + e.message); }
    }

    function openEditModal(game) {
        var form = $("#game-form");
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
        form.querySelector("[name=transfer_status]").value = game.transfer_status || "pending";
        form.querySelector("[name=crawler_source]").value = game.crawler_source || "";
        form.querySelector("[name=seo_title]").value = game.seo_title || "";
        form.querySelector("[name=seo_description]").value = game.seo_description || "";
        form.querySelector("[name=seo_keywords]").value = game.seo_keywords || "";
        form.querySelector("[name=description]").value = game.description;
        $(".game-modal .modal-header h3").textContent = "编辑游戏";
        $(".game-modal").classList.add("active");
        loadCategoriesForSelects();
    }

    async function deleteGame(id) {
        try {
            var res = await apiFetch("/api/admin/game/" + id, { method: "DELETE" });
            var data = await res.json();
            if (data.code === 0) { await loadGameTable(); }
            else { alert("删除失败: " + (data.detail || data.message)); }
        } catch (e) { alert("请求失败: " + e.message); }
    }

    // ==================== 分类管理 ====================
    async function renderCategoryManagement(body) {
        body.innerHTML =
            "<div class=\"panel\">" +
            "<div class=\"panel-header\"><h3>分类管理</h3><button class=\"btn btn-primary\" id=\"add-category-btn\">+ 添加分类</button></div>" +
            "<div class=\"panel-body\"><div class=\"category-table-container\"><p style=\"padding:20px;color:#888;\">加载中..</p></div></div>" +
            "</div>" +
            "<div class=\"modal-overlay category-modal\">" +
            "<div class=\"modal\">" +
            "<div class=\"modal-header\"><h3>添加分类</h3><button class=\"modal-close-btn cat-modal-close\">&times;</button></div>" +
            "<div class=\"modal-body\"><form id=\"category-form\">" +
            "<div class=\"form-group\"><label>分类名称 *</label><input name=\"cat_name\" required placeholder=\"输入分类名称\"></div>" +
            "<div class=\"form-group\"><label>URL 标识 *</label><input name=\"cat_slug\" required placeholder=\"如action\"></div>" +
            "<input type=\"hidden\" name=\"cat_id\" value=\"\">" +
            "</form></div>" +
            "<div class=\"modal-footer\"><button class=\"btn btn-outline cat-modal-cancel\">取消</button><button class=\"btn btn-primary cat-modal-save\">保存</button></div>" +
            "</div></div>";
        await loadCategoryTable();
        bindCategoryEvents();
    }

    async function loadCategoryTable() {
        var container = $(".category-table-container");
        if (!container) return;
        try {
            var res = await apiFetch("/api/admin/categories");
            var data = await res.json();
            if (data.code === 0) { state.categories = data.data; renderCategoryTable(container); }
        } catch (e) { container.innerHTML = "<div class=\"empty-state\"><p>加载失败</p></div>"; }
    }

    function renderCategoryTable(container) {
        var cats = state.categories;
        if (cats.length === 0) { container.innerHTML = "<div class=\"empty-state\"><p>暂无分类，点击「添加分类」开始/p></div>"; return; }
        var html = "<table><thead><tr><th>ID</th><th>分类名称</th><th>URL 标识</th><th>游戏数量</th><th>操作</th></tr></thead><tbody>";
        cats.forEach(function(c) {
            html += "<tr><td>" + c.id + "</td><td>" + escHtml(c.name) + "</td><td>" + escHtml(c.slug) + "</td><td>" + c.game_count + "</td>" +
                "<td><button class=\"btn btn-sm btn-outline cat-edit-btn\" data-id=\"" + c.id + "\">编辑</button> " +
                "<button class=\"btn btn-sm btn-danger cat-delete-btn\" data-id=\"" + c.id + "\" data-name=\"" + escHtml(c.name) + "\">删除</button></td></tr>";
        });
        html += "</tbody></table>";
        container.innerHTML = html;
    }

    function bindCategoryEvents() {
        document.getElementById("add-category-btn")?.addEventListener("click", function() {
            $("#category-form").reset(); $("#category-form [name=cat_id]").value = "";
            $(".category-modal .modal-header h3").textContent = "添加分类";
            $(".category-modal").classList.add("active");
        });
        $(".cat-modal-close")?.addEventListener("click", function() { $(".category-modal").classList.remove("active"); });
        $(".cat-modal-cancel")?.addEventListener("click", function() { $(".category-modal").classList.remove("active"); });
        $(".category-modal")?.addEventListener("click", function(e) { if (e.target === e.currentTarget) $(".category-modal").classList.remove("active"); });
        $(".cat-modal-save")?.addEventListener("click", saveCategory);
        $(".category-table-container")?.addEventListener("click", function(e) {
            var editBtn = e.target.closest(".cat-edit-btn");
            var deleteBtn = e.target.closest(".cat-delete-btn");
            if (editBtn) {
                var cat = state.categories.find(function(c) { return c.id == editBtn.dataset.id; });
                if (cat) {
                    $("#category-form [name=cat_id]").value = cat.id;
                    $("#category-form [name=cat_name]").value = cat.name;
                    $("#category-form [name=cat_slug]").value = cat.slug;
                    $(".category-modal .modal-header h3").textContent = "编辑分类";
                    $(".category-modal").classList.add("active");
                }
            }
            if (deleteBtn) {
                var id = deleteBtn.dataset.id, name = deleteBtn.dataset.name;
                if (confirm("确定删除分类「" + name + "」吗？")) {
                    apiFetch("/api/admin/category/" + id, { method: "DELETE" }).then(function(res) { return res.json(); }).then(function(data) {
                        if (data.code === 0) { loadCategoryTable(); loadCategoriesForSelects(); }
                        else { alert("删除失败: " + (data.detail || data.message)); }
                    }).catch(function(e) { alert("请求失败: " + e.message); });
                }
            }
        });
    }

    async function saveCategory() {
        var form = $("#category-form");
        var fd = new FormData(form);
        var id = fd.get("cat_id"), name = fd.get("cat_name"), slug = fd.get("cat_slug");
        if (!name || !slug) { alert("请填写分类名称和 URL 标识"); return; }
        try {
            var url, method, body;
            if (id) { url = "/api/admin/category/" + id; method = "PUT"; } else { url = "/api/admin/category"; method = "POST"; }
            body = { name: name, slug: slug };
            var res = await apiFetch(url, { method: method, body: body });
            var data = await res.json();
            if (data.code === 0) { alert(id ? "更新成功" : "创建成功"); $(".category-modal").classList.remove("active"); await loadCategoryTable(); await loadCategoriesForSelects(); }
            else { alert("操作失败: " + (data.detail || data.message)); }
        } catch (e) { alert("请求失败: " + e.message); }
    }

        // ==================== 下载资源管理 ====================
    var downloadResourceState = { page: 1, pageSize: 20, keyword: "", provider: "", status: "", editingId: null };

    function providerLabel(p) { var m = { baidu: "百度网盘", quark: "夸克网盘", alipan: "阿里云盘", "115": "115网盘" }; return m[p] || p; }
    function drStatusLabel(s) { var m = { pending: "待审核", active: "正常", disabled: "已禁用", invalid: "已失效" }; return m[s] || s; }

    function renderResourceManagement(body) {
        body.innerHTML =
            '<div class="panel">' +
            '<div class="panel-header"><h3>下载资源管理</h3><button class="btn btn-primary" id="add-resource-btn">+ 新增资源</button></div>' +
            '<div class="toolbar">' +
            '<input type="text" class="search-input" id="dr-keyword" placeholder="搜索游戏名称...">' +
            '<select id="dr-provider-filter"><option value="">全部网盘</option><option value="baidu">百度网盘</option><option value="quark">夸克网盘</option><option value="alipan">阿里云盘</option><option value="115">115网盘</option></select>' +
            '<select id="dr-status-filter"><option value="">全部状态</option><option value="pending">待审核</option><option value="active">正常</option><option value="disabled">已禁用</option><option value="invalid">已失效</option></select>' +
            '<span class="toolbar-info" id="dr-count-info"></span>' +
            '</div>' +
            '<div class="panel-body"><div class="resource-table-container"><p style="padding:20px;color:#888;">加载中...</p></div></div>' +
            '<div class="pagination" id="dr-pagination"></div>' +
            '</div>' +
            // Modal
            '<div class="modal-overlay resource-modal">' +
            '<div class="modal" style="max-width:650px;">' +
            '<div class="modal-header"><h3>编辑资源</h3><button class="modal-close-btn res-modal-close">&times;</button></div>' +
            '<div class="modal-body"><form id="resource-form">' +
            '<div class="form-group"><label>游戏 *</label>' +
            '<div class="game-select-container">' +
            '<input id="res-game-search" placeholder="搜索游戏名称..." autocomplete="off"><span id="res-game-title" style="display:none;font-size:0.85rem;color:#0f3460;font-weight:600;"></span>' +
            '<div class="game-select-dropdown" id="game-dropdown"></div>' +
            '</div></div>' +
            '<div class="form-row"><div class="form-group"><label>网盘 *</label>' +
            '<select name="provider" id="res-provider"><option value="baidu">百度网盘</option><option value="quark">夸克网盘</option><option value="alipan">阿里云盘</option><option value="115">115网盘</option></select></div>' +
            '<div class="form-group"><label>状态</label>' +
            '<select name="status" id="res-status"><option value="pending">待审核</option><option value="active" selected>正常</option><option value="disabled">已禁用</option><option value="invalid">已失效</option></select></div></div>' +
            '<div class="form-group"><label>资源标题</label><input name="title" id="res-title" placeholder="如：游戏本体v1.2"></div>' +
            '<div class="form-row"><div class="form-group"><label>原始URL</label><input name="origin_url" id="res-origin-url" placeholder="原始下载链接"></div>' +
            '<div class="form-group"><label>我的分享</label><input name="my_share_url" id="res-my-share-url" placeholder="我的网盘分享链接"></div></div>' +
            '<div class="form-row"><div class="form-group"><label>提取码</label><input name="extract_code" id="res-extract-code" placeholder="如：abcd"></div>' +
            '<div class="form-group"><label>显示排序</label><input name="display_order" id="res-display-order" type="number" value="0" min="0"></div></div>' +
            '<div class="form-group"><label>备注</label><textarea name="remark" id="res-remark" rows="3" placeholder="备注信息..."></textarea></div>' +
            '<input type="hidden" name="id" id="res-id" value="">' +
            '<input type="hidden" name="game_id" id="res-game-id" value="">' +
            '</form></div>' +
            '<div class="modal-footer"><button class="btn btn-outline res-modal-cancel">取消</button><button class="btn btn-primary res-modal-save">保存</button></div>' +
            '</div></div>';

        loadDownloadResources();
        bindDownloadResourceEvents();
    }

    async function loadDownloadResources() {
        var container = document.querySelector(".resource-table-container");
        if (!container) return;
        try {
            var s = downloadResourceState;
            var params = "page=" + s.page + "&page_size=" + s.pageSize;
            if (s.keyword) params += "&keyword=" + encodeURIComponent(s.keyword);
            if (s.provider) params += "&provider=" + encodeURIComponent(s.provider);
            if (s.status) params += "&status=" + encodeURIComponent(s.status);
            var res = await apiFetch("/api/admin/download-resources?" + params);
            var data = await res.json();
            if (data.code !== 0) throw new Error(data.message || "Failed");
            var items = data.data.items;
            var total = data.data.total;

            var info = document.getElementById("dr-count-info");
            if (info) info.textContent = "共 " + total + " 条";

            if (items.length === 0) {
                container.innerHTML = '<div class="empty-state"><p>暂无下载资源，点击右上角新增</p></div>';
            } else {
                var html = '<table><thead><tr><th>ID</th><th>游戏</th><th>网盘</th><th>标题</th><th>状态</th><th>提取码</th><th>排序</th><th>更新时间</th><th>操作</th></tr></thead><tbody>';
                items.forEach(function(r) {
                    html += '<tr>' +
                        '<td>' + r.id + '</td>' +
                        '<td>' + escHtml(r.game_title || ("ID:" + r.game_id)) + '</td>' +
                        '<td><span class="provider-tag provider-' + r.provider + '">' + providerLabel(r.provider) + '</span></td>' +
                        '<td>' + escHtml(r.title || "-") + '</td>' +
                        '<td><span class="badge badge-' + r.status + '">' + drStatusLabel(r.status) + '</span></td>' +
                        '<td>' + escHtml(r.extract_code || "-") + '</td>' +
                        '<td>' + (r.display_order != null ? r.display_order : 0) + '</td>' +
                        '<td>' + (r.updated_at || r.created_at || "").slice(0, 10) + '</td>' +
                        '<td><button class="btn btn-sm btn-outline dr-edit-btn" data-id="' + r.id + '">编辑</button> ' +
                        '<button class="btn btn-sm btn-danger dr-delete-btn" data-id="' + r.id + '" data-title="' + escHtml(r.provider + " - " + (r.game_title || "")) + '">删除</button></td>' +
                        '</tr>';
                });
                html += '</tbody></table>';
                container.innerHTML = html;
            }

            // Pagination
            var pg = document.getElementById("dr-pagination");
            if (pg) {
                var totalPages = Math.ceil(total / s.pageSize) || 1;
                var phtml = '<button' + (s.page <= 1 ? ' disabled' : '') + ' data-page="' + (s.page - 1) + '">上一页</button>';
                var start = Math.max(1, s.page - 2);
                var end = Math.min(totalPages, s.page + 2);
                for (var i = start; i <= end; i++) {
                    phtml += '<button class="' + (i === s.page ? 'active' : '') + '" data-page="' + i + '">' + i + '</button>';
                }
                phtml += '<button' + (s.page >= totalPages ? ' disabled' : '') + ' data-page="' + (s.page + 1) + '">下一页</button>';
                phtml += '<span class="page-info">第' + s.page + '/' + totalPages + ' 页</span>';
                pg.innerHTML = phtml;
                pg.querySelectorAll("button[data-page]").forEach(function(btn) {
                    btn.addEventListener("click", function() {
                        downloadResourceState.page = parseInt(btn.dataset.page);
                        loadDownloadResources();
                    });
                });
            }
        } catch (e) {
            if (e.message.indexOf("获取") === -1) container.innerHTML = '<div class="empty-state"><p>加载失败，请稍后重试</p></div>';
        }
    }

    function bindDownloadResourceEvents() {
        var keywordEl = document.getElementById("dr-keyword");
        if (keywordEl) keywordEl.addEventListener("input", debounce(function() {
            downloadResourceState.keyword = keywordEl.value.trim();
            downloadResourceState.page = 1;
            loadDownloadResources();
        }, 400));

        var provEl = document.getElementById("dr-provider-filter");
        if (provEl) provEl.addEventListener("change", function() {
            downloadResourceState.provider = provEl.value;
            downloadResourceState.page = 1;
            loadDownloadResources();
        });

        var statEl = document.getElementById("dr-status-filter");
        if (statEl) statEl.addEventListener("change", function() {
            downloadResourceState.status = statEl.value;
            downloadResourceState.page = 1;
            loadDownloadResources();
        });

        document.getElementById("add-resource-btn")?.addEventListener("click", openResourceModal);

        var tableContainer = document.querySelector(".resource-table-container");
        if (tableContainer) {
            tableContainer.addEventListener("click", function(e) {
                var editBtn = e.target.closest(".dr-edit-btn");
                var deleteBtn = e.target.closest(".dr-delete-btn");
                if (editBtn) editResource(parseInt(editBtn.dataset.id));
                if (deleteBtn) {
                    var id = deleteBtn.dataset.id;
                    var title = deleteBtn.dataset.title || ("ID: " + id);
                    if (confirm("确定删除下载资源 " + title + "吗？此操作不可恢复。")) deleteResource(parseInt(id));
                }
            });
        }

        document.querySelector(".res-modal-close")?.addEventListener("click", closeResourceModal);
        document.querySelector(".res-modal-cancel")?.addEventListener("click", closeResourceModal);
        document.querySelector(".resource-modal")?.addEventListener("click", function(e) {
            if (e.target === e.currentTarget) closeResourceModal();
        });
        document.querySelector(".res-modal-save")?.addEventListener("click", saveResource);

        var gameSearchEl = document.getElementById("res-game-search");
        if (gameSearchEl) {
            gameSearchEl.addEventListener("input", debounce(function() {
                var kw = gameSearchEl.value.trim();
                if (kw.length < 1) { document.getElementById("game-dropdown").classList.remove("active"); return; }
                searchGames(kw);
            }, 300));
            gameSearchEl.addEventListener("focus", function() {
                if (gameSearchEl.value.trim().length >= 1) {
                    searchGames(gameSearchEl.value.trim());
                }
            });
        }
        document.addEventListener("click", function(e) {
            if (!e.target.closest(".game-select-container")) {
                var dd = document.getElementById("game-dropdown");
                if (dd) dd.classList.remove("active");
            }
        });
    }

    async function searchGames(keyword) {
        var dd = document.getElementById("game-dropdown");
        if (!dd) return;
        try {
            var res = await apiFetch("/api/admin/download-resources-games?keyword=" + encodeURIComponent(keyword));
            var data = await res.json();
            var games = data.data || [];
            var html = "";
            games.forEach(function(g) {
                html += '<div class="game-option" data-game-id="' + g.id + '" data-game-title="' + escHtml(g.title) + '">' + escHtml(g.title) + ' (' + g.id + ')</div>';
            });
            if (games.length === 0) html = '<div class="game-option" style="color:#888;">未找到匹配游戏</div>';
            dd.innerHTML = html;
            dd.classList.add("active");

            dd.querySelectorAll(".game-option[data-game-id]").forEach(function(opt) {
                opt.addEventListener("click", function() {
                    document.getElementById("res-game-id").value = opt.dataset.gameId;
                    document.getElementById("res-game-search").value = opt.dataset.gameTitle;
                    document.getElementById("res-game-search").style.display = "none";
                    document.getElementById("res-game-title").textContent = opt.dataset.gameTitle;
                    document.getElementById("res-game-title").style.display = "";
                    dd.classList.remove("active");
                });
            });
        } catch (e) { dd.innerHTML = '<div class="game-option" style="color:#c62828;">加载失败</div>'; dd.classList.add("active"); }
    }

    function openResourceModal() {
        downloadResourceState.editingId = null;
        document.querySelector(".resource-modal .modal-header h3").textContent = "新增资源";
        document.getElementById("resource-form").reset();
        document.getElementById("res-id").value = "";
        document.getElementById("res-game-id").value = "";
        document.getElementById("res-game-search").value = "";
        document.getElementById("res-game-search").style.display = "";
        document.getElementById("res-game-title").style.display = "none";
        document.getElementById("res-game-title").textContent = "";
        document.getElementById("res-status").value = "active";
        document.getElementById("res-display-order").value = "0";
        document.getElementById("game-dropdown").classList.remove("active");
        document.querySelector(".resource-modal").classList.add("active");
    }

    async function editResource(id) {
        try {
            var res = await apiFetch("/api/admin/download-resources/" + id);
            var data = await res.json();
            if (data.code !== 0) { alert("获取资源失败"); return; }
            var r = data.data;
            downloadResourceState.editingId = r.id;
            document.querySelector(".resource-modal .modal-header h3").textContent = "编辑资源";
            document.getElementById("res-id").value = r.id;
            document.getElementById("res-game-id").value = r.game_id;
            document.getElementById("res-game-search").style.display = "none";
            document.getElementById("res-game-title").style.display = "";
            document.getElementById("res-game-title").textContent = r.game_title || ("ID:" + r.game_id);
            document.getElementById("res-provider").value = r.provider;
            document.getElementById("res-status").value = r.status;
            document.getElementById("res-title").value = r.title || "";
            document.getElementById("res-origin-url").value = r.origin_url || "";
            document.getElementById("res-my-share-url").value = r.my_share_url || "";
            document.getElementById("res-extract-code").value = r.extract_code || "";
            document.getElementById("res-display-order").value = r.display_order != null ? r.display_order : 0;
            document.getElementById("res-remark").value = r.remark || "";
            document.getElementById("game-dropdown").classList.remove("active");
            document.querySelector(".resource-modal").classList.add("active");
        } catch (e) { alert("加载失败: " + e.message); }
    }

    function closeResourceModal() {
        document.querySelector(".resource-modal").classList.remove("active");
        downloadResourceState.editingId = null;
    }

    async function saveResource() {
        var gameId = parseInt(document.getElementById("res-game-id").value);
        if (!gameId) { alert("请选择游戏"); return; }

        var payload = {
            game_id: gameId,
            provider: document.getElementById("res-provider").value,
            title: document.getElementById("res-title").value || "",
            origin_url: document.getElementById("res-origin-url").value || "",
            my_share_url: document.getElementById("res-my-share-url").value || "",
            extract_code: document.getElementById("res-extract-code").value || "",
            remark: document.getElementById("res-remark").value || "",
            display_order: parseInt(document.getElementById("res-display-order").value) || 0,
            status: document.getElementById("res-status").value,
        };

        try {
            var id = downloadResourceState.editingId;
            var url = id ? "/api/admin/download-resources/" + id : "/api/admin/download-resources";
            var method = id ? "PUT" : "POST";
            var res = await apiFetch(url, { method: method, body: payload });
            var data = await res.json();
            if (data.code === 0) {
                alert(id ? "更新成功" : "创建成功");
                closeResourceModal();
                await loadDownloadResources();
            } else {
                alert("操作失败: " + (data.detail || data.message || "未知错误"));
            }
        } catch (e) { alert("请求失败: " + e.message); }
    }

    async function deleteResource(id) {
        try {
            var res = await apiFetch("/api/admin/download-resources/" + id, { method: "DELETE" });
            var data = await res.json();
            if (data.code === 0) { await loadDownloadResources(); }
            else { alert("删除失败: " + (data.detail || data.message)); }
        } catch (e) { alert("删除失败: " + e.message); }
    }function renderSettings(body) {
        body.innerHTML =
            "<div class=\"panel\"><div class=\"panel-header\"><h3>系统设置</h3></div><div class=\"panel-body\" style=\"padding:20px;\">" +
            "<div class=\"form-group\"><label>站点名称</label><input value=\"小白游戏资源站\" disabled></div>" +
            "<div class=\"form-group\"><label>API 版本</label><input value=\"v1.0.0\" disabled></div>" +
            "<div class=\"form-group\"><label>数据库类型/label><input value=\"SQLite（可切换 MySQL/PostgreSQL）\" disabled></div>" +
            "<div class=\"form-group\"><label>采集程序状态/label><input value=\"未启用（预留接口已就绪）\" disabled></div>" +
            "<div class=\"form-group\"><label>资源中转状态/label><input value=\"未启用（预留接口已就绪）\" disabled></div>" +
            "<div class=\"form-group\"><label>AI 助手状态/label><input value=\"未启用（预留接口已就绪）\" disabled></div>" +
            "<p style=\"font-size:0.8rem;color:#888;margin-top:16px;\">以上设置为只读展示。后续可通过配置文件或环境变量进行修改、/p>" +
            "</div></div>";
    }

    // ==================== 占位页面 ====================
    function renderPlaceholder(body, menu) {
        if (!menu) return;
        body.innerHTML =
            "<div class=\"placeholder-page\"><div class=\"placeholder-icon\">&#x1F6A7;</div>" +
            "<h3>" + menu.label + " - 功能开发中</h3>" +
            "<p>此模块为预留功能，将在后续版本中实现、/p>" +
            "<p style=\"font-size:0.8rem;color:#bbb;margin-top:8px;\">相关 API 接口已预留，可直接对接外部程序、/p></div>";
    }

    // ==================== 启动 ====================
    async function init() {
        var authed = await checkAuth();
        if (!authed) return;

        var userEl = document.querySelector(".header-user");
        if (userEl) userEl.textContent = getUsername();

        initSidebar();
        renderPage(state.currentMenu);

        // 如果 URL hash 指定了页面        var hash = window.location.hash.replace("#", "");
        if (hash && MENUS.some(function(m) { return m.id === hash; })) {
            switchMenu(hash);
        }
    }

    document.addEventListener("DOMContentLoaded", init);
})();
