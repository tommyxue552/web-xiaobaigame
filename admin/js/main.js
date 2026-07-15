/**
 * С����Ϸ��Դվ- ��̨����ű�
 * ================================
 * ������Ϸ��Դ�������Ǳ��̡���Ϸ�������������ģ�顣 * ����API �����Я��JWT ��֤���ơ� */

(function () {
    "use strict";

    // ==================== DOM ���� ====================
    const $ = (sel) => document.querySelector(sel);
    const $$ = (sel) => document.querySelectorAll(sel);

    // ==================== Auth ���� ====================
    function getToken() { return localStorage.getItem("admin_token"); }
    function getUsername() { return localStorage.getItem("admin_username") || "����Ա"; }
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
        if (res.status === 401) { clearAuth(); window.location.href = "/admin/login.html"; throw new Error("��֤�ѹ���"); }
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

    // ==================== �������� ====================
    var MENUS = [
        { id: "dashboard", label: "仪表盘", icon: "\u25A0" },
        { id: "games", label: "游戏管理", icon: "\u25B6" },
        { id: "categories", label: "分类管理", icon: "\u25CB" },
        { id: "resources", label: "下载资源", icon: "\u2193" },
        { id: "tags", label: "标签管理", icon: "\u2605" },
        { id: "dlstats", label: "下载统计", icon: "\u21C5" },
        { id: "crawler", label: "采集管理", icon: "\u21C4", hidden: true },
        { id: "transfer", label: "资源中转", icon: "\u21C5", hidden: true },
        { id: "ai", label: "AI助手", icon: "\u2699", hidden: true },
        { id: "settings", label: "系统设置", icon: "\u2630" },
    ];
    // ==================== ״̬====================
    var state = {
        currentMenu: "dashboard",
        games: { items: [], total: 0, page: 1, pageSize: 20 },
        gameFilter: { keyword: "", publishStatus: "", category: "" },
        categories: [],
    };

    // ==================== ���ߺ��� ====================
    function escHtml(str) {
        if (!str) return "";
        var div = document.createElement("div");
        div.textContent = str;
        return div.innerHTML;
    }
    function statusLabel(s) { var m = { published: "�ѷ���", draft: "�ݸ�", hidden: "����" }; return m[s] || s; }
    function transferLabel(s) { var m = { pending: "����ת", transferring: "��ת��", completed: "�����", failed: "ʧ��" }; return m[s] || s; }
    function debounce(fn, delay) { var t; return function() { var ctx=this, a=arguments; clearTimeout(t); t=setTimeout(function(){fn.apply(ctx,a)},delay); }; }

    // ==================== �������� ====================
    function initSidebar() {
        var nav = $(".sidebar-nav");
        var html = ""; var inHidden = false;
        MENUS.forEach(function(m) {
            if (m.hidden && !inHidden) { html += "<div class=\"nav-divider\">��չ���ܣ���������</div>"; inHidden = true; }
            html += "<div class=\"nav-item " + (m.hidden ? "hidden-menu" : "") + (m.id === state.currentMenu ? " active" : "") + "\" data-menu=\"" + m.id + "\"><span class=\"nav-icon\">" + m.icon + "</span><span>" + m.label + "</span></div>";
        });
        nav.innerHTML = html;
        nav.addEventListener("click", function(e) {
            var item = e.target.closest(".nav-item"); if (!item) return;
            switchMenu(item.dataset.menu);
        });
        var footer = $(".sidebar-footer");
        if (footer) {
            footer.innerHTML = "<span>" + escHtml(getUsername()) + "</span> | <span class=\"logout-link\" id=\"logout-btn\">�˳�/span>";
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

    // ==================== ҳ��·�� ====================
    function renderPage(menuId) {
        var body = $(".main-body");
        switch (menuId) {
        case "dashboard": renderDashboard(body); break;
        case "games": renderGameManagement(body); break;
        case "categories": renderCategoryManagement(body); break;
        case "resources": renderResourceManagement(body); break;
    case "dlstats": renderDownloadStats(body); break;`n        case "tags": renderTagManagement(body); break;`n        case "settings": renderSettings(body); break;
        default: renderPlaceholder(body, MENUS.find(function(m){return m.id===menuId;})); break;
        }
    }

    // ==================== �Ǳ���====================
    async function renderDashboard(body) {
        body.innerHTML = "<div style=\"padding:40px;text-align:center;color:#888;\">������..</div>";
        try {
            var res = await apiFetch("/api/admin/stats");
            var data = await res.json();
            if (data.code !== 0) throw new Error("��ȡͳ������ʧ��");
            var stats = data.data;
            var publishRate = stats.total_games > 0 ? Math.round(stats.published_games / stats.total_games * 100) : 0;
            body.innerHTML =
                ""<div class=\"stats-grid\">" +
                "<div class=\"stat-card stat-total\"><div class=\"stat-icon\">&#x1F3AE;</div><div class=\"stat-info\"><div class=\"stat-label\">��Ϸ����</div><div class=\"stat-value\">" + stats.total_games + "</div><div class=\"stat-sub\">ȫ����Ϸ��Դ</div></div></div>" +
                "<div class=\"stat-card stat-published\"><div class=\"stat-icon\">&#x2705;</div><div class=\"stat-info\"><div class=\"stat-label\">�ѷ���</div><div class=\"stat-value\">" + stats.published_games + "</div><div class=\"stat-sub\">������ " + publishRate + "%</div></div></div>" +
                "<div class=\"stat-card stat-draft\"><div class=\"stat-icon\">&#x1F4DD;</div><div class=\"stat-info\"><div class=\"stat-label\">�ݸ�</div><div class=\"stat-value\">" + stats.draft_games + "</div><div class=\"stat-sub\">���༭����</div></div></div>" +
                "<div class=\"stat-card stat-category\"><div class=\"stat-icon\">&#x1F4C2;</div><div class=\"stat-info\"><div class=\"stat-label\">��������</div><div class=\"stat-value\">" + stats.category_count + "</div><div class=\"stat-sub\">��Ϸ����</div></div></div>" +
                "</div>" +
                "class=\"panel\">" +
                "<div class=\"panel-header\"><h3>�����ӵ���Ϸ</h3></div>" +
                "<ul class=\"recent-list\">" +
                (stats.recent_games.length === 0
                    ? "<li style=\"justify-content:center;color:#888;\">������Ϸ����</li>"
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
                "<div class=\"panel-header\"><h3>ϵͳ״̬</h3></div>" +
                "<div class=\"panel-body\" style=\"padding:20px;\">" +
                "<div style=\"display:flex;gap:20px;flex-wrap:wrap;\">" +
                "<div><span style=\"color:#888;font-size:0.85rem;\">API �汾</span><br><span style=\"font-weight:600;\">v1.0.0</span></div>" +
                "<div><span style=\"color:#888;font-size:0.85rem;\">���ݿ�</span><br><span style=\"font-weight:600;\">SQLite<</span></div>" +
                "<div><span style=\"color:#888;font-size:0.85rem;\">�ɼ�����<</span><br><span style=\"font-weight:600;color:#f57f17;\">������</span></div>" +
                "<div><span style=\"color:#888;font-size:0.85rem;\">��Դ��ת<</span><br><span style=\"font-weight:600;color:#f57f17;\">������</span></div>" +
                "<div><span style=\"color:#888;font-size:0.85rem;\">AI ����<</span><br><span style=\"font-weight:600;color:#f57f17;\">������</span></div>" +
                "</div></div></div>";
        } catch (e) {
            body.innerHTML = "<div class=\"empty-state\"><p>����ͳ��ʧ��: " + escHtml(e.message) + "</p></div>";
        }
    }

    // ==================== ��Ϸ���� ====================
    function renderGameManagement(body) {
        body.innerHTML =
            "<div class=\"panel\">" +
            "<div class=\"panel-header\"><h3>��Ϸ�б�</h3><button class=\"btn btn-primary\" id=\"add-game-btn\">+ �����Ϸ</button></div>" +
            "<div class=\"toolbar\">" +
            "<input type=\"text\" class=\"search-input\" id=\"game-search\" placeholder=\"������Ϸ����...\">" +
            "<select id=\"game-status-filter\"><option value=\"\">ȫ��״̬/option><option value=\"published\">�ѷ���/option><option value=\"draft\">�ݸ�</option><option value=\"hidden\">����</option></select>" +
            "<select id=\"game-category-filter\"><option value=\"\">ȫ������</option></select>" +
            "<span class=\"toolbar-info\" id=\"game-count-info\"></span>" +
            "</div>" +
            "<div class=\"panel-body\"><div class=\"game-table-container\"><p style=\"padding:20px;color:#888;\">������..</p></div></div>" +
            "<div class=\"pagination\" id=\"game-pagination\"></div>" +
            "</div>" +
            // ��Ϸ����
            "<div class=\"modal-overlay game-modal\">" +
            "<div class=\"modal\">" +
            "<div class=\"modal-header\"><h3>�����Ϸ</h3><button class=\"modal-close-btn\">&times;</button></div>" +
            "<div class=\"modal-body\"><form id=\"game-form\">" +
            "<div class=\"form-row\"><div class=\"form-group\"><label>��Ϸ���� *</label><input name=\"title\" required placeholder=\"������Ϸ����\"></div>" +
            "<div class=\"form-group\"><label>URL ��ʶ *</label><input name=\"slug\" required placeholder=\"��grand-theft-auto-v\"></div></div>" +
            "<div class=\"form-row\"><div class=\"form-group\"><label>����ͼƬ URL</label><input name=\"cover\" placeholder=\"https://...\"></div>" +
            "<div class=\"form-group\"><label>����</label><select name=\"category\" id=\"game-category-select\"><option value=\"\">��ѡ�����</option></select></div></div>" +
            "<div class=\"form-row\"><div class=\"form-group\"><label>����ƽ̨</label><input name=\"system\" placeholder=\"��Windows/Mac/Linux\"></div>" +
            "<div class=\"form-group\"><label>����</label><input name=\"language\" placeholder=\"������/Ӣ��\"></div></div>" +
            "<div class=\"form-row\"><div class=\"form-group\"><label>�ļ���С</label><input name=\"size\" placeholder=\"��50GB\"></div>" +
            "<div class=\"form-group\"><label>�汾��/label><input name=\"version\" placeholder=\"��v1.2.3\"></div></div>" +
            "<div class=\"form-row\"><div class=\"form-group\"><label>������/label><input name=\"publisher\"></div>" +
            "<div class=\"form-group\"><label>������</label><input name=\"developer\"></div></div>" +
            "<div class=\"form-row\"><div class=\"form-group\"><label>��������</label><input name=\"release_date\" type=\"date\"></div>" +
            "<div class=\"form-group\"><label>����״̬/label><select name=\"publish_status\"><option value=\"draft\">�ݸ�</option><option value=\"published\">�ѷ���/option><option value=\"hidden\">����</option></select></div></div>" +
            "<div class=\"form-group\"><label>标签</label><div id=\"tag-checkboxes\" class=\"tag-checkboxes\" style=\"display:flex;flex-wrap:wrap;gap:8px;padding:8px;border:1px solid #333;border-radius:4px;min-height:36px;max-height:150px;overflow-y:auto;\"><span style=\"color:#888;\">加载中...</span></div></div>" +
            "<div class=\"form-row\"><div class=\"form-group\"><label>��������</label><input name=\"download_url\" placeholder=\"https://...\"></div>" +
            "<div class=\"form-group\"><label>ԭʼ��Դ URL</label><input name=\"original_url\" placeholder=\"https://...\"></div></div>" +
            "<div class=\"form-row\"><div class=\"form-group\"><label>��ת״̬/label><select name=\"transfer_status\"><option value=\"pending\">����ת/option><option value=\"transferring\">��ת��/option><option value=\"completed\">�����/option><option value=\"failed\">ʧ��</option></select></div>" +
            "<div class=\"form-group\"><label>�ɼ���Դ</label><input name=\"crawler_source\" placeholder=\"��steam\"></div></div>" +
            "<div class=\"form-group\"><label>��Ϸ����</label><textarea name=\"description\" rows=\"4\" placeholder=\"������Ϸ���..\"></textarea></div>" +
            "<input type=\"hidden\" name=\"id\" value=\"\">" +
            "</form></div>" +
            "<div class=\"modal-footer\"><button class=\"btn btn-outline modal-cancel-btn\">ȡ��</button><button class=\"btn btn-primary modal-save-btn\">����</button></div>" +
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
                if (sel) sel.innerHTML = "<option value=\"\">��ѡ�����</option>" + opts;
                var fil = document.getElementById("game-category-filter");
                if (fil) fil.innerHTML = "<option value=\"\">ȫ������</option>" + opts;
            }
        } catch (e) { console.error("���ط���ʧ��:", e); }
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
                if (info) info.textContent = "��" + data.data.total + " ��";
            }
        } catch (e) { if (e.message.indexOf("��֤") === -1) container.innerHTML = "<div class=\"empty-state\"><p>����ʧ�ܣ���ȷ�Ϻ�˷��������/p></div>"; }
    }

    function renderGameTable() {
        var container = $(".game-table-container");
        var games = state.games.items;
        if (games.length === 0) { container.innerHTML = "<div class=\"empty-state\"><p>������Ϸ���ݣ�����������Ϸ����ʼ/p></div>"; return; }
        var html = "<table><thead><tr><th>ID</th><th>����</th><th>����</th><th>����</th><th>��С</th><th>����״̬/th><th>����</th><th>����ʱ��</th><th>����</th></tr></thead><tbody>";
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
                "<td><button class=\"btn btn-sm btn-outline edit-btn\" data-id=\"" + g.id + "\">�༭</button> " +
                "<button class=\"btn btn-sm btn-danger delete-btn\" data-id=\"" + g.id + "\" data-title=\"" + escHtml(g.title) + "\">ɾ��</button></td>" +
                "</tr>";
        });
        html += "</tbody></table>";
        container.innerHTML = html;
    }

    function renderGamePagination() {
        var pg = document.getElementById("game-pagination");
        if (!pg) return;
        var totalPages = Math.ceil(state.games.total / state.games.pageSize) || 1;
        var html = "<button " + (state.games.page <= 1 ? "disabled" : "") + " data-page=\"" + (state.games.page - 1) + "\">��һҳ/button>";
        var start = Math.max(1, state.games.page - 2);
        var end = Math.min(totalPages, state.games.page + 2);
        for (var i = start; i <= end; i++) {
            html += "<button class=\"" + (i === state.games.page ? "active" : "") + "\" data-page=\"" + i + "\">" + i + "</button>";
        }
        html += "<button " + (state.games.page >= totalPages ? "disabled" : "") + " data-page=\"" + (state.games.page + 1) + "\">��һҳ/button>";
        html += "<span class=\"page-info\">��" + state.games.page + "/" + totalPages + " ҳ/span>";
        pg.innerHTML = html;
        pg.querySelectorAll("button[data-page]").forEach(function(btn) {
            btn.addEventListener("click", function() { state.games.page = parseInt(btn.dataset.page); loadGameTable(); });
        });
    }

    function bindGameEvents() {
        document.getElementById("add-game-btn")?.addEventListener("click", function() {
            resetGameForm();
            $(".game-modal .modal-header h3").textContent = "�����Ϸ";
            $(".game-modal").classList.add("active");
            loadCategoriesForSelects();
            loadTagCheckboxes();
        });
        $(".modal-close-btn")?.addEventListener("click", closeGameModal);
        $(".modal-cancel-btn")?.addEventListener("click", closeGameModal);
        $(".game-modal")?.addEventListener("click", function(e) { if (e.target === e.currentTarget) closeGameModal(); });
        $(".modal-save-btn")?.addEventListener("click", saveGame);

        $(".game-table-container")?.addEventListener("click", function(e) {
            var editBtn = e.target.closest(".edit-btn");
            var deleteBtn = e.target.closest(".delete-btn");
            if (editBtn) { var g = state.games.items.find(function(x) { return x.id == editBtn.dataset.id; }); if (g) openEditModal(g); }
            if (deleteBtn) { var id = deleteBtn.dataset.id; var t = deleteBtn.dataset.title || ("ID: " + id); if (confirm("ȷ��ɾ����Ϸ��" + t + "���𣿴˲������ɻָ�")) deleteGame(id); }
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
        var tagIds = []; var cbs = document.querySelectorAll("#game-form input[name=tag_ids]:checked"); cbs.forEach(function(cb) { tagIds.push(parseInt(cb.value)); });
        var payload = {
            title: fd.get("title"), slug: fd.get("slug"), cover: fd.get("cover") || "",
            images: [], description: fd.get("description") || "",
            system: fd.get("system") || "", language: fd.get("language") || "",
            size: fd.get("size") || "", version: fd.get("version") || "",
            publisher: fd.get("publisher") || "", developer: fd.get("developer") || "",
            release_date: fd.get("release_date") || null,
            category: fd.get("category") || "", tag_ids: tagIds,
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
            if (data.code === 0) { alert(id ? "���³ɹ�" : "�����ɹ�"); closeGameModal(); await loadGameTable(); }
            else { alert("����ʧ��: " + (data.detail || data.message || "δ֪����")); }
        } catch (e) { alert("����ʧ��: " + e.message); }
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
        loadTagCheckboxes(game.tag_ids || []);        form.querySelector("[name=download_url]").value = game.download_url;
        form.querySelector("[name=original_url]").value = game.original_url;
        form.querySelector("[name=transfer_status]").value = game.transfer_status || "pending";
        form.querySelector("[name=crawler_source]").value = game.crawler_source || "";
        form.querySelector("[name=seo_title]").value = game.seo_title || "";
        form.querySelector("[name=seo_description]").value = game.seo_description || "";
        form.querySelector("[name=seo_keywords]").value = game.seo_keywords || "";
        form.querySelector("[name=description]").value = game.description;
        $(".game-modal .modal-header h3").textContent = "�༭��Ϸ";
        $(".game-modal").classList.add("active");
        loadCategoriesForSelects();
    }

    async function deleteGame(id) {
        try {
            var res = await apiFetch("/api/admin/game/" + id, { method: "DELETE" });
            var data = await res.json();
            if (data.code === 0) { await loadGameTable(); }
            else { alert("ɾ��ʧ��: " + (data.detail || data.message)); }
        } catch (e) { alert("����ʧ��: " + e.message); }
    }

    // ==================== ������� ====================
    async function renderCategoryManagement(body) {
        body.innerHTML =
            "<div class=\"panel\">" +
            "<div class=\"panel-header\"><h3>�������</h3><button class=\"btn btn-primary\" id=\"add-category-btn\">+ ��ӷ���</button></div>" +
            "<div class=\"panel-body\"><div class=\"category-table-container\"><p style=\"padding:20px;color:#888;\">������..</p></div></div>" +
            "</div>" +
            "<div class=\"modal-overlay category-modal\">" +
            "<div class=\"modal\">" +
            "<div class=\"modal-header\"><h3>��ӷ���</h3><button class=\"modal-close-btn cat-modal-close\">&times;</button></div>" +
            "<div class=\"modal-body\"><form id=\"category-form\">" +
            "<div class=\"form-group\"><label>�������� *</label><input name=\"cat_name\" required placeholder=\"�����������\"></div>" +
            "<div class=\"form-group\"><label>URL ��ʶ *</label><input name=\"cat_slug\" required placeholder=\"��action\"></div>" +
            "<input type=\"hidden\" name=\"cat_id\" value=\"\">" +
            "</form></div>" +
            "<div class=\"modal-footer\"><button class=\"btn btn-outline cat-modal-cancel\">ȡ��</button><button class=\"btn btn-primary cat-modal-save\">����</button></div>" +
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
        } catch (e) { container.innerHTML = "<div class=\"empty-state\"><p>����ʧ��</p></div>"; }
    }

    function renderCategoryTable(container) {
        var cats = state.categories;
        if (cats.length === 0) { container.innerHTML = "<div class=\"empty-state\"><p>���޷��࣬�������ӷ��ࡹ��ʼ/p></div>"; return; }
        var html = "<table><thead><tr><th>ID</th><th>��������</th><th>URL ��ʶ</th><th>��Ϸ����</th><th>����</th></tr></thead><tbody>";
        cats.forEach(function(c) {
            html += "<tr><td>" + c.id + "</td><td>" + escHtml(c.name) + "</td><td>" + escHtml(c.slug) + "</td><td>" + c.game_count + "</td>" +
                "<td><button class=\"btn btn-sm btn-outline cat-edit-btn\" data-id=\"" + c.id + "\">�༭</button> " +
                "<button class=\"btn btn-sm btn-danger cat-delete-btn\" data-id=\"" + c.id + "\" data-name=\"" + escHtml(c.name) + "\">ɾ��</button></td></tr>";
        });
        html += "</tbody></table>";
        container.innerHTML = html;
    }

    function bindCategoryEvents() {
        document.getElementById("add-category-btn")?.addEventListener("click", function() {
            $("#category-form").reset(); $("#category-form [name=cat_id]").value = "";
            $(".category-modal .modal-header h3").textContent = "��ӷ���";
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
                    $(".category-modal .modal-header h3").textContent = "�༭����";
                    $(".category-modal").classList.add("active");
                }
            }
            if (deleteBtn) {
                var id = deleteBtn.dataset.id, name = deleteBtn.dataset.name;
                if (confirm("ȷ��ɾ�����ࡸ" + name + "����")) {
                    apiFetch("/api/admin/category/" + id, { method: "DELETE" }).then(function(res) { return res.json(); }).then(function(data) {
                        if (data.code === 0) { loadCategoryTable(); loadCategoriesForSelects(); }
                        else { alert("ɾ��ʧ��: " + (data.detail || data.message)); }
                    }).catch(function(e) { alert("����ʧ��: " + e.message); });
                }
            }
        });
    }

    async function saveCategory() {
        var form = $("#category-form");
        var fd = new FormData(form);
        var id = fd.get("cat_id"), name = fd.get("cat_name"), slug = fd.get("cat_slug");
        if (!name || !slug) { alert("����д�������ƺ� URL ��ʶ"); return; }
        try {
            var url, method, body;
            if (id) { url = "/api/admin/category/" + id; method = "PUT"; } else { url = "/api/admin/category"; method = "POST"; }
            body = { name: name, slug: slug };
            var res = await apiFetch(url, { method: method, body: body });
            var data = await res.json();
            if (data.code === 0) { alert(id ? "���³ɹ�" : "�����ɹ�"); $(".category-modal").classList.remove("active"); await loadCategoryTable(); await loadCategoriesForSelects(); }
            else { alert("����ʧ��: " + (data.detail || data.message)); }
        } catch (e) { alert("����ʧ��: " + e.message); }
    }

        // ==================== ������Դ���� ====================
    var downloadResourceState = { page: 1, pageSize: 20, keyword: "", provider: "", status: "", editingId: null };

    function providerLabel(p, label) { if (label) return label; var m = { baidu: "百度网盘", quark: "夸克网盘", alipan: "阿里云盘", "115": "115网盘", xunlei: "迅雷云盘", uc: "UC网盘", mobile: "中国移动云盘", tianyi: "天翼云盘" }; return m[p] || p; }
    function drStatusLabel(s) { var m = { pending: "�����", active: "����", disabled: "�ѽ���", invalid: "��ʧЧ" }; return m[s] || s; }

    function renderResourceManagement(body) {
        body.innerHTML =
            '<div class="panel">' +
            '<div class="panel-header"><h3>������Դ����</h3><button class="btn btn-primary" id="add-resource-btn">+ ������Դ</button></div>' +
            '<div class="toolbar">' +
            '<input type="text" class="search-input" id="dr-keyword" placeholder="������Ϸ����...">' +
            '<select id="dr-provider-filter"><option value="">ȫ������</option><option value="baidu">�ٶ�����</option><option value="quark">�������</option><option value="alipan">��������</option><option value="115">115����</option></select>' +
            '<select id="dr-status-filter"><option value="">ȫ��״̬</option><option value="pending">�����</option><option value="active">����</option><option value="disabled">�ѽ���</option><option value="invalid">��ʧЧ</option></select>' +
            '<span class="toolbar-info" id="dr-count-info"></span>' +
            '</div>' +
            '<div class="panel-body"><div class="resource-table-container"><p style="padding:20px;color:#888;">������...</p></div></div>' +
            '<div class="pagination" id="dr-pagination"></div>' +
            '</div>' +
            // Modal
            '<div class="modal-overlay resource-modal">' +
            '<div class="modal" style="max-width:650px;">' +
            '<div class="modal-header"><h3>�༭��Դ</h3><button class="modal-close-btn res-modal-close">&times;</button></div>' +
            '<div class="modal-body"><form id="resource-form">' +
            '<div class="form-group"><label>��Ϸ *</label>' +
            '<div class="game-select-container">' +
            '<input id="res-game-search" placeholder="������Ϸ����..." autocomplete="off"><span id="res-game-title" style="display:none;font-size:0.85rem;color:#0f3460;font-weight:600;"></span>' +
            '<div class="game-select-dropdown" id="game-dropdown"></div>' +
            '</div></div>' +
            '<div class="form-row"><div class="form-group"><label>���� *</label>' +
            '<select name="provider" id="res-provider"><option value="baidu">�ٶ�����</option><option value="quark">�������</option><option value="alipan">��������</option><option value="115">115����</option></select></div>' +
            '<div class="form-group"><label>״̬</label>' +
            '<select name="status" id="res-status"><option value="pending">�����</option><option value="active" selected>����</option><option value="disabled">�ѽ���</option><option value="invalid">��ʧЧ</option></select></div></div>' +
            '<div class="form-group"><label>��Դ����</label><input name="title" id="res-title" placeholder="�磺��Ϸ����v1.2"></div>' +
            '<div class="form-row"><div class="form-group"><label>ԭʼURL</label><input name="origin_url" id="res-origin-url" placeholder="ԭʼ��������"></div>' +
            '<div class="form-group"><label>�ҵķ���</label><input name="my_share_url" id="res-my-share-url" placeholder="�ҵ����̷�������"></div></div>' +
            '<div class="form-row"><div class="form-group"><label>��ȡ��</label><input name="extract_code" id="res-extract-code" placeholder="�磺abcd"></div>' +
            '<div class="form-group"><label>��ʾ����</label><input name="display_order" id="res-display-order" type="number" value="0" min="0"></div></div>' +
            '<div class="form-group"><label>��ע</label><textarea name="remark" id="res-remark" rows="3" placeholder="��ע��Ϣ..."></textarea></div>' +
            '<input type="hidden" name="id" id="res-id" value="">' +
            '<input type="hidden" name="game_id" id="res-game-id" value="">' +
            '</form></div>' +
            '<div class="modal-footer"><button class="btn btn-outline res-modal-cancel">ȡ��</button><button class="btn btn-primary res-modal-save">����</button></div>' +
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
            if (info) info.textContent = "�� " + total + " ��";

            if (items.length === 0) {
                container.innerHTML = '<div class="empty-state"><p>����������Դ��������Ͻ�����</p></div>';
            } else {
                var html = '<table><thead><tr><th>ID</th><th>游戏</th><th>网盘</th><th>资源</th><th>优先级</th><th>默认</th><th>成功</th><th>失败</th><th>状态</th><th>更新时间</th><th>操作</th></tr></thead><tbody>';
                items.forEach(function(r) {
                    html += '<tr>' +
                        '<td>' + r.id + '</td>' +
                        '<td>' + escHtml(r.game_title || ("ID:" + r.game_id)) + '</td>' +
                        '<td><span class="provider-tag provider-' + (r.provider || "") + '">' + providerLabel(r.provider, r.provider_label) + '</span></td>' +
                        '<td>' + escHtml(r.title || "-") + '</td>' +
                        '<td><input type="number" class="dr-priority-input" data-id="' + r.id + '" value="' + (r.priority != null ? r.priority : 100) + '" min="0" max="10000" style="width:60px;" title="修改优先级"></td>' +
                        '<td>' + (r.is_primary ? '<span class="badge badge-active" style="cursor:pointer;" onclick="togglePrimary(' + r.id + ',false)" title="点击取消默认">是</span>' : '<span class="badge badge-disabled" style="cursor:pointer;" onclick="togglePrimary(' + r.id + ',true)" title="点击设为默认">否</span>') + '</td>' +
                        '<td>' + (r.success_count || 0) + '</td>' +
                        '<td>' + (r.fail_count || 0) + '</td>' +
                        '<td><span class="badge badge-' + r.status + '">' + drStatusLabel(r.status) + '</span></td>' +
                        '<td>' + (r.updated_at || r.created_at || "").slice(0, 10) + '</td>' +
                        '<td><button class="btn btn-sm btn-outline dr-edit-btn" data-id="' + r.id + '">编辑</button> ' +
                        '<button class="btn btn-sm btn-danger dr-delete-btn" data-id="' + r.id + '" data-title="' + escHtml(r.provider + " - " + (r.game_title || "")) + '">删除</button></td>' +
                        '</tr>';
                });html += '</tbody></table>';
                container.innerHTML = html;
            }

            // Pagination
            var pg = document.getElementById("dr-pagination");
            if (pg) {
                var totalPages = Math.ceil(total / s.pageSize) || 1;
                var phtml = '<button' + (s.page <= 1 ? ' disabled' : '') + ' data-page="' + (s.page - 1) + '">��һҳ</button>';
                var start = Math.max(1, s.page - 2);
                var end = Math.min(totalPages, s.page + 2);
                for (var i = start; i <= end; i++) {
                    phtml += '<button class="' + (i === s.page ? 'active' : '') + '" data-page="' + i + '">' + i + '</button>';
                }
                phtml += '<button' + (s.page >= totalPages ? ' disabled' : '') + ' data-page="' + (s.page + 1) + '">��һҳ</button>';
                phtml += '<span class="page-info">��' + s.page + '/' + totalPages + ' ҳ</span>';
                pg.innerHTML = phtml;
                pg.querySelectorAll("button[data-page]").forEach(function(btn) {
                    btn.addEventListener("click", function() {
                        downloadResourceState.page = parseInt(btn.dataset.page);
                        loadDownloadResources();
                    });
                });
            }
        } catch (e) {
            if (e.message.indexOf("��ȡ") === -1) container.innerHTML = '<div class="empty-state"><p>����ʧ�ܣ����Ժ�����</p></div>';
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
                    if (confirm("ȷ��ɾ��������Դ " + title + "�𣿴˲������ɻָ���")) deleteResource(parseInt(id));
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
            if (games.length === 0) html = '<div class="game-option" style="color:#888;">δ�ҵ�ƥ����Ϸ</div>';
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
        } catch (e) { dd.innerHTML = '<div class="game-option" style="color:#c62828;">����ʧ��</div>'; dd.classList.add("active"); }
    }

    
    // 模块7.8: 优先级内联编辑
    (function() {
        var tc = document.querySelector(".resource-table-container");
        if (tc) {
            tc.addEventListener("change", function(e) {
                var input = e.target.closest(".dr-priority-input");
                if (input) {
                    var id = parseInt(input.dataset.id);
                    var priority = parseInt(input.value);
                    if (isNaN(priority) || priority < 0 || priority > 10000) {
                        alert("优先级需在 0-10000 之间");
                        return;
                    }
                    updateResourcePriority(id, priority);
                }
            });
        }
    })();

    // Expose togglePrimary globally
    window.togglePrimary = async function(resourceId, isPrimary) {
        try {
            var res = await apiFetch("/api/admin/download-resource/" + resourceId + "/primary", {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ is_primary: isPrimary })
            });
            var data = await res.json();
            if (data.code === 0) {
                loadDownloadResources();
            } else {
                alert(data.message || "操作失败");
            }
        } catch (e) {
            console.error(e);
            alert("网络错误");
        }
    };

function openResourceModal() {
        downloadResourceState.editingId = null;
        document.querySelector(".resource-modal .modal-header h3").textContent = "������Դ";
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
            if (data.code !== 0) { alert("��ȡ��Դʧ��"); return; }
            var r = data.data;
            downloadResourceState.editingId = r.id;
            document.querySelector(".resource-modal .modal-header h3").textContent = "�༭��Դ";
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
        } catch (e) { alert("����ʧ��: " + e.message); }
    }

    async function updateResourcePriority(resourceId, priority) {
    try {
        var res = await apiFetch("/api/admin/download-resource/" + resourceId + "/priority", {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ priority: priority })
        });
        var data = await res.json();
        if (data.code !== 0) {
            console.error("Priority update failed:", data.message);
        }
    } catch (e) {
        console.error(e);
    }
}

function closeResourceModal() {
        document.querySelector(".resource-modal").classList.remove("active");
        downloadResourceState.editingId = null;
    }

    async function saveResource() {
        var gameId = parseInt(document.getElementById("res-game-id").value);
        if (!gameId) { alert("��ѡ����Ϸ"); return; }

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
                alert(id ? "���³ɹ�" : "�����ɹ�");
                closeResourceModal();
                await loadDownloadResources();
            } else {
                alert("����ʧ��: " + (data.detail || data.message || "δ֪����"));
            }
        } catch (e) { alert("����ʧ��: " + e.message); }
    }

    async function deleteResource(id) {
        try {
            var res = await apiFetch("/api/admin/download-resources/" + id, { method: "DELETE" });
            var data = await res.json();
            if (data.code === 0) { await loadDownloadResources(); }
            else { alert("ɾ��ʧ��: " + (data.detail || data.message)); }
        } catch (e) { alert("ɾ��ʧ��: " + e.message); }
    }function renderSettings(body) {
        body.innerHTML =
            "<div class=\"panel\"><div class=\"panel-header\"><h3>ϵͳ����</h3></div><div class=\"panel-body\" style=\"padding:20px;\">" +
            "<div class=\"form-group\"><label>վ������</label><input value=\"С����Ϸ��Դվ\" disabled></div>" +
            "<div class=\"form-group\"><label>API �汾</label><input value=\"v1.0.0\" disabled></div>" +
            "<div class=\"form-group\"><label>���ݿ�����/label><input value=\"SQLite�����л� MySQL/PostgreSQL��\" disabled></div>" +
            "<div class=\"form-group\"><label>�ɼ�����״̬/label><input value=\"δ���ã�Ԥ��ӿ��Ѿ�����\" disabled></div>" +
            "<div class=\"form-group\"><label>��Դ��ת״̬/label><input value=\"δ���ã�Ԥ��ӿ��Ѿ�����\" disabled></div>" +
            "<div class=\"form-group\"><label>AI ����״̬/label><input value=\"δ���ã�Ԥ��ӿ��Ѿ�����\" disabled></div>" +
            "<p style=\"font-size:0.8rem;color:#888;margin-top:16px;\">��������Ϊֻ��չʾ��������ͨ�������ļ��򻷾����������޸ġ�/p>" +
            "</div></div>";
    }

    // ==================== ռλҳ�� ====================

    // ==================== 标签管理 ====================
            async function loadTagCheckboxes(selectedTagIds) {
        var container = document.getElementById("tag-checkboxes");
        if (!container) return;
        selectedTagIds = selectedTagIds || [];
        try {
            var res = await apiFetch("/api/admin/tags/active");
            var data = await res.json();
            if (data.code !== 0) { container.innerHTML = "<span style=\"color:#888;\">加载失败</span>"; return; }
            var tags = data.data;
            container.innerHTML = tags.map(function(t) {
                var checked = selectedTagIds.indexOf(t.id) !== -1 ? " checked" : "";
                return "<label><input type=\"checkbox\" name=\"tag_ids\" value=\"" + t.id + "\"" + checked + "> " + escHtml(t.name) + "</label>";
            }).join("");
        } catch (e) {
            container.innerHTML = "<span style=\"color:#888;\">加载失败</span>";
        }
    }

    function renderTagManagement(body) {
        body.innerHTML = "<div style=\"padding:40px;text-align:center;color:#888;\">加载中...</div>";
        loadTagTable(body);
    }

    async function loadTagTable(container) {
        try {
            var res = await apiFetch("/api/admin/tags");
            var data = await res.json();
            if (data.code !== 0) throw new Error(data.message || "失败");
            var tags = data.data;
            if (!container) container = document.querySelector(".main-body");
            var rows = tags.map(function(t) {
                var statusClass = t.is_active ? "badge-published" : "badge-draft";
                var statusText = t.is_active ? "启用" : "禁用";
                return "<tr>" +
                    "<td>" + t.id + "</td>" +
                    "<td>" + escHtml(t.name) + "</td>" +
                    "<td>" + escHtml(t.slug) + "</td>" +
                    "<td>" + t.game_count + "</td>" +
                    "<td>" + t.sort_order + "</td>" +
                    "<td><span class=\"badge " + statusClass + "\">" + statusText + "</span></td>" +
                    "<td>" +
                    "<button class=\"btn btn-sm\" onclick=\"editTag(" + t.id + ")\" title=\"编辑\">&#x270F;</button>" +
                    "<button class=\"btn btn-sm btn-danger\" onclick=\"deleteTag(" + t.id + ")\" title=\"删除\">&#x2715;</button>" +
                    "</td>" +
                    "</tr>";
            }).join("");
            container.innerHTML =
                "<div class=\"panel\">" +
                "<div class=\"panel-header\"><h3>标签管理</h3><button class=\"btn btn-primary\" onclick=\"showTagForm()\">+ 新增标签</button></div>" +
                "<div class=\"panel-body\" style=\"padding:0;\">" +
                "<table class=\"data-table\">" +
                "<thead><tr>" +
                "<th>ID</th><th>标签名称</th><th>Slug</th><th>游戏数</th><th>排序</th><th>状态</th><th>操作</th>" +
                "</tr></thead>" +
                "<tbody>" + (rows || "<tr><td colspan=\"7\" style=\"text-align:center;color:#888;\">????</td></tr>") + "</tbody>" +
                "</table></div></div>";
        } catch (e) {
            if (!container) container = document.querySelector(".main-body");
            container.innerHTML = "<div class=\"empty-state\"><p>失败: " + escHtml(e.message) + "</p></div>";
        }
    }

    function showTagForm(id) {
        var isEdit = !!id;
        var title = isEdit ? "编辑标签" : "新增标签";
        var html = "<div class=\"modal\">" +
            "<div class=\"modal-header\"><h3>" + title + "</h3><button class=\"modal-close-btn\" onclick=\"closeModal()\">&times;</button></div>" +
            "<div class=\"modal-body\"><form id=\"tag-form\">" +
            "<input type=\"hidden\" name=\"id\" value=\"" + (id || "") + "\">" +
            "<div class=\"form-row\">" +
            "<div class=\"form-group\"><label>标签名称 *</label><input name=\"name\" required placeholder=\"标签名称\"></div>" +
            "<div class=\"form-group\"><label>Slug *</label><input name=\"slug\" required placeholder=\"tag-slug\"></div>" +
            "</div>" +
            "<div class=\"form-group\"><label>描述</label><textarea name=\"description\" rows=\"3\" placeholder=\"描述\"></textarea></div>" +
            "<div class=\"form-row\">" +
            "<div class=\"form-group\"><label>SEO标题</label><input name=\"seo_title\" maxlength=\"255\"></div>" +
            "<div class=\"form-group\"><label>SEO关键词</label><input name=\"seo_keywords\" maxlength=\"500\"></div>" +
            "</div>" +
            "<div class=\"form-group\"><label>SEO描述</label><textarea name=\"seo_description\" rows=\"2\" maxlength=\"500\"></textarea></div>" +
            "<div class=\"form-row\">" +
            "<div class=\"form-group\"><label>排序</label><input name=\"sort_order\" type=\"number\" value=\"0\"></div>" +
            "<div class=\"form-group\"><label>状态</label><select name=\"is_active\"><option value=\"1\">启用</option><option value=\"0\">禁用</option></select></div>" +
            "</div>" +
            "<div class=\"form-actions\">" +
            "<button type=\"button\" class=\"btn\" onclick=\"closeModal()\">取消</button>" +
            "<button type=\"submit\" class=\"btn btn-primary\">保存</button>" +
            "</div>" +
            "</form></div></div>";
        showModal(html);
        if (isEdit) {
            loadTagData(id);
        }
        document.getElementById("tag-form").addEventListener("submit", function(e) {
            e.preventDefault();
            saveTag();
        });
    }

    async function loadTagData(id) {
        try {
            var res = await apiFetch("/api/admin/tags/" + id);
            var data = await res.json();
            if (data.code !== 0) return;
            var t = data.data;
            var form = document.getElementById("tag-form");
            form.querySelector("[name=name]").value = t.name || "";
            form.querySelector("[name=slug]").value = t.slug || "";
            form.querySelector("[name=description]").value = t.description || "";
            form.querySelector("[name=seo_title]").value = t.seo_title || "";
            form.querySelector("[name=seo_description]").value = t.seo_description || "";
            form.querySelector("[name=seo_keywords]").value = t.seo_keywords || "";
            form.querySelector("[name=sort_order]").value = t.sort_order || 0;
            form.querySelector("[name=is_active]").value = t.is_active ? "1" : "0";
        } catch (e) {}
    }

    async function saveTag() {
        var form = document.getElementById("tag-form");
        var fd = new FormData(form);
        var id = fd.get("id");
        var payload = {
            name: fd.get("name"),
            slug: fd.get("slug"),
            description: fd.get("description") || "",
            seo_title: fd.get("seo_title") || "",
            seo_description: fd.get("seo_description") || "",
            seo_keywords: fd.get("seo_keywords") || "",
            sort_order: parseInt(fd.get("sort_order")) || 0,
            is_active: fd.get("is_active") === "1",
        };
        try {
            var url = id ? "/api/admin/tags/" + id : "/api/admin/tags";
            var method = id ? "PUT" : "POST";
            var res = await apiFetch(url, { method: method, body: payload });
            var data = await res.json();
            if (data.code === 0) {
                alert(id ? "编辑成功" : "新增成功");
                closeModal();
                await loadTagTable();
            } else {
                alert("失败: " + (data.detail || data.message || "未知错误"));
            }
        } catch (e) {
            alert("失败: " + e.message);
        }
    }

    async function deleteTag(id) {
        if (!confirm("确定删除该标签吗？")) return;
        try {
            var res = await apiFetch("/api/admin/tags/" + id, { method: "DELETE" });
            var data = await res.json();
            if (data.code === 0) {
                alert("删除成功");
                await loadTagTable();
            } else {
                alert("失败: " + (data.detail || data.message || "未知错误"));
            }
        } catch (e) {
            alert("失败: " + e.message);
        }
    }

    function editTag(id) {
        showTagForm(id);
    }

    function renderPlaceholder(body, menu) {
        if (!menu) return;
        body.innerHTML =
            "<div class=\"placeholder-page\"><div class=\"placeholder-icon\">&#x1F6A7;</div>" +
            "<h3>" + menu.label + " - ���ܿ�����</h3>" +
            "<p>��ģ��ΪԤ����ܣ����ں����汾��ʵ�֡�/p>" +
            "<p style=\"font-size:0.8rem;color:#bbb;margin-top:8px;\">��� API �ӿ���Ԥ�����ֱ�ӶԽ��ⲿ����/p></div>";
    }

    // ==================== ��� ====================
    async function init() {
        var authed = await checkAuth();
        if (!authed) return;

        var userEl = document.querySelector(".header-user");
        if (userEl) userEl.textContent = getUsername();

        initSidebar();
        renderPage(state.currentMenu);

        // ��� URL hash ָ����ҳ��        var hash = window.location.hash.replace("#", "");
        if (hash && MENUS.some(function(m) { return m.id === hash; })) {
            switchMenu(hash);
        }
    }

    document.addEventListener("DOMContentLoaded", init);
})();

