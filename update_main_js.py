# -*- coding: utf-8 -*-
import sys, re
sys.stdout.reconfigure(encoding='utf-8')

PATH = r"C:\Users\xueta\Documents\web-xiaobaigame\admin\js\main.js"
with open(PATH, "r", encoding="utf-8") as f:
    content = f.read()

changes = 0

# === 1. MENUS: add providers entry after resources ===
old = '{ id: "resources", label: "下载资源", icon: "\\u2193" },'
new = '{ id: "resources", label: "下载资源", icon: "\\u2193" },\n        { id: "providers", label: "下载渠道", icon: "\\u2693" },'
if old in content:
    content = content.replace(old, new)
    changes += 1
    print("1. MENUS: Added providers entry")

# === 2. renderPage switch: add providers case before settings ===
old = 'case "settings": renderSettings(body); break;'
new = 'case "providers": renderProviderManagement(body); break;\n        case "settings": renderSettings(body); break;'
if old in content:
    content = content.replace(old, new)
    changes += 1
    print("2. Switch: Added providers case")

# === 3. Replace hardcoded provider select ===
old = '\'<select name=\"provider\" id=\"res-provider\"><option value=\"baidu\">百度网盘</option><option value=\"quark\">夸克网盘</option><option value=\"alipan\">阿里云盘</option><option value=\"115\">115网盘</option></select></div>\' +'
new = '\'<select name=\"provider_id\" id=\"res-provider\"><option value=\"\">加载中...</option></select></div>\' +'
if old in content:
    content = content.replace(old, new)
    changes += 1
    print("3. Provider select: Made dynamic")

# === 4. Update editResource to use provider_id ===
old = 'document.getElementById(\"res-provider\").value = r.provider;'
new = 'document.getElementById(\"res-provider\").value = r.provider_id || \"\";'
if old in content:
    content = content.replace(old, new)
    changes += 1
    print("4. editResource: Use provider_id")

# === 5. Update saveResource to use provider_id ===
old = 'provider: document.getElementById(\"res-provider\").value,'
new = 'provider_id: parseInt(document.getElementById(\"res-provider\").value) || null,'
if old in content:
    content = content.replace(old, new)
    changes += 1
    print("5. saveResource: Use provider_id")

# === 6. Add loadProviderDropdown call in openResourceModal ===
old = 'function openResourceModal() {'
new = 'function openResourceModal() {\n        loadProviderDropdown();'
if old in content:
    content = content.replace(old, new)
    changes += 1
    print("6. openResourceModal: Added loadProviderDropdown()")

# === 7. Insert renderProviderManagement before renderSettings ===
# Find the insertion point
marker = '}function renderSettings(body) {'
if marker in content:
    provider_code = '''
    // ==================== 下载渠道管理 ====================
    var providerState = { items: [], total: 0, page: 1, pageSize: 20, keyword: "", status: "" };

    function providerStatusLabel(s) { var m = { active: "启用", disabled: "禁用" }; return m[s] || s; }

    function renderProviderManagement(body) {
        body.innerHTML =
            '<div class="panel">' +
            '<div class="panel-header"><h3>下载渠道</h3><button class="btn btn-primary" id="add-provider-btn">+ 新增渠道</button></div>' +
            '<div class="toolbar">' +
            '<input type="text" class="search-input" id="prov-keyword" placeholder="搜索名称或代码...">' +
            '<select id="prov-status-filter"><option value="">全部状态</option><option value="active">启用</option><option value="disabled">禁用</option></select>' +
            '<span class="toolbar-info" id="prov-count-info"></span>' +
            '</div>' +
            '<div class="panel-body"><div class="provider-table-container"><p style="padding:20px;color:#888;">加载中...</p></div></div>' +
            '<div class="pagination" id="prov-pagination"></div>' +
            '</div>' +
            '<div class="modal-overlay provider-modal">' +
            '<div class="modal" style="max-width:550px;">' +
            '<div class="modal-header"><h3>编辑渠道</h3><button class="modal-close-btn prov-modal-close">&times;</button></div>' +
            '<div class="modal-body"><form id="provider-form">' +
            '<div class="form-row"><div class="form-group"><label>渠道代码 *</label><input name="code" id="prov-code" required placeholder="例如：baidu"></div>' +
            '<div class="form-group"><label>渠道名称 *</label><input name="name" id="prov-name" required placeholder="例如：百度网盘"></div></div>' +
            '<div class="form-row"><div class="form-group"><label>状态</label>' +
            '<select name="status" id="prov-status"><option value="active">启用</option><option value="disabled">禁用</option></select></div>' +
            '<div class="form-group"><label>排序</label><input name="display_order" id="prov-display-order" type="number" value="0" min="0"></div></div>' +
            '<div class="form-group"><label>图标</label><input name="icon" id="prov-icon" placeholder="图标 URL 或 CSS class"></div>' +
            '<div class="form-group"><label>备注</label><textarea name="remark" id="prov-remark" rows="3" placeholder="备注信息..."></textarea></div>' +
            '<input type="hidden" name="id" id="prov-id" value="">' +
            '</form></div>' +
            '<div class="modal-footer"><button class="btn btn-outline prov-modal-cancel">取消</button><button class="btn btn-primary prov-modal-save">保存</button></div>' +
            '</div></div>';

        loadProviders();
        bindProviderEvents();
    }

    async function loadProviders() {
        var container = document.querySelector(".provider-table-container");
        if (!container) return;
        try {
            var s = providerState;
            var params = "page=" + s.page + "&page_size=" + s.pageSize;
            if (s.keyword) params += "&keyword=" + encodeURIComponent(s.keyword);
            if (s.status) params += "&status=" + encodeURIComponent(s.status);
            var res = await apiFetch("/api/admin/download-providers?" + params);
            var data = await res.json();
            if (data.code !== 0) throw new Error(data.message || "Failed");
            var items = data.data.items;
            var total = data.data.total;

            var info = document.getElementById("prov-count-info");
            if (info) info.textContent = "共" + total + " 条";

            if (items.length === 0) {
                container.innerHTML = '<div class="empty-state"><p>暂无渠道数据，点击右上角新增</p></div>';
            } else {
                var html = '<table><thead><tr><th>ID</th><th>代码</th><th>名称</th><th>状态</th><th>排序</th><th>使用数</th><th>更新时间</th><th>操作</th></tr></thead><tbody>';
                items.forEach(function(p) {
                    html += '<tr>' +
                        '<td>' + p.id + '</td>' +
                        '<td><code>' + escHtml(p.code) + '</code></td>' +
                        '<td>' + escHtml(p.name) + '</td>' +
                        '<td><span class="badge badge-' + p.status + '">' + providerStatusLabel(p.status) + '</span></td>' +
                        '<td>' + (p.display_order != null ? p.display_order : 0) + '</td>' +
                        '<td>' + (p.usage_count != null ? p.usage_count : 0) + '</td>' +
                        '<td>' + (p.updated_at || p.created_at || "").slice(0, 10) + '</td>' +
                        '<td><button class="btn btn-sm btn-outline prov-edit-btn" data-id="' + p.id + '">编辑</button> ' +
                        '<button class="btn btn-sm btn-danger prov-delete-btn" data-id="' + p.id + '" data-name="' + escHtml(p.name) + '" data-usage="' + (p.usage_count || 0) + '">删除</button></td>' +
                        '</tr>';
                });
                html += '</tbody></table>';
                container.innerHTML = html;
            }

            var pg = document.getElementById("prov-pagination");
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
                        providerState.page = parseInt(btn.dataset.page);
                        loadProviders();
                    });
                });
            }
        } catch (e) {
            if (e.message.indexOf("认证") === -1) container.innerHTML = '<div class="empty-state"><p>加载失败，请稍后重试</p></div>';
        }
    }

    function bindProviderEvents() {
        var keywordEl = document.getElementById("prov-keyword");
        if (keywordEl) keywordEl.addEventListener("input", debounce(function() {
            providerState.keyword = keywordEl.value.trim();
            providerState.page = 1;
            loadProviders();
        }, 400));

        var statusEl = document.getElementById("prov-status-filter");
        if (statusEl) statusEl.addEventListener("change", function() {
            providerState.status = statusEl.value;
            providerState.page = 1;
            loadProviders();
        });

        document.getElementById("add-provider-btn")?.addEventListener("click", openProviderModal);

        var tableContainer = document.querySelector(".provider-table-container");
        if (tableContainer) {
            tableContainer.addEventListener("click", function(e) {
                var editBtn = e.target.closest(".prov-edit-btn");
                var deleteBtn = e.target.closest(".prov-delete-btn");
                if (editBtn) editProvider(parseInt(editBtn.dataset.id));
                if (deleteBtn) {
                    var id = deleteBtn.dataset.id;
                    var name = deleteBtn.dataset.name || ("ID: " + id);
                    var usage = parseInt(deleteBtn.dataset.usage) || 0;
                    if (usage > 0) {
                        alert("渠道 \u201c" + name + "\u201d 正在被 " + usage + " 个下载资源使用，无法删除。");
                        return;
                    }
                    if (confirm("确定删除渠道 \u201c" + name + "\u201d 吗？此操作不可恢复。")) deleteProvider(parseInt(id));
                }
            });
        }

        document.querySelector(".prov-modal-close")?.addEventListener("click", closeProviderModal);
        document.querySelector(".prov-modal-cancel")?.addEventListener("click", closeProviderModal);
        document.querySelector(".provider-modal")?.addEventListener("click", function(e) {
            if (e.target === e.currentTarget) closeProviderModal();
        });
        document.querySelector(".prov-modal-save")?.addEventListener("click", saveProvider);
    }

    function openProviderModal() {
        providerState.editingId = null;
        document.querySelector(".provider-modal .modal-header h3").textContent = "新增渠道";
        document.getElementById("provider-form").reset();
        document.getElementById("prov-id").value = "";
        document.getElementById("prov-status").value = "active";
        document.getElementById("prov-display-order").value = "0";
        document.querySelector(".provider-modal").classList.add("active");
    }

    async function editProvider(id) {
        try {
            var res = await apiFetch("/api/admin/download-providers/" + id);
            var data = await res.json();
            if (data.code !== 0) { alert("获取渠道失败"); return; }
            var p = data.data;
            providerState.editingId = p.id;
            document.querySelector(".provider-modal .modal-header h3").textContent = "编辑渠道";
            document.getElementById("prov-id").value = p.id;
            document.getElementById("prov-code").value = p.code || "";
            document.getElementById("prov-name").value = p.name || "";
            document.getElementById("prov-status").value = p.status || "active";
            document.getElementById("prov-display-order").value = p.display_order != null ? p.display_order : 0;
            document.getElementById("prov-icon").value = p.icon || "";
            document.getElementById("prov-remark").value = p.remark || "";
            document.querySelector(".provider-modal").classList.add("active");
        } catch (e) { alert("加载失败: " + e.message); }
    }

    function closeProviderModal() {
        document.querySelector(".provider-modal").classList.remove("active");
        providerState.editingId = null;
    }

    async function saveProvider() {
        var code = document.getElementById("prov-code").value.trim();
        var name = document.getElementById("prov-name").value.trim();
        if (!code) { alert("请输入渠道代码"); return; }
        if (!name) { alert("请输入渠道名称"); return; }

        var payload = {
            code: code,
            name: name,
            icon: document.getElementById("prov-icon").value || "",
            status: document.getElementById("prov-status").value,
            display_order: parseInt(document.getElementById("prov-display-order").value) || 0,
            remark: document.getElementById("prov-remark").value || "",
        };

        try {
            var id = providerState.editingId;
            var url = id ? "/api/admin/download-providers/" + id : "/api/admin/download-providers";
            var method = id ? "PUT" : "POST";
            var res = await apiFetch(url, { method: method, body: payload });
            var data = await res.json();
            if (data.code === 0) {
                alert(id ? "更新成功" : "创建成功");
                closeProviderModal();
                await loadProviders();
                loadProviderDropdown();
            } else {
                alert("操作失败: " + (data.detail || data.message || "未知错误"));
            }
        } catch (e) { alert("请求失败: " + e.message); }
    }

    async function deleteProvider(id) {
        try {
            var res = await apiFetch("/api/admin/download-providers/" + id, { method: "DELETE" });
            var data = await res.json();
            if (data.code === 0) { await loadProviders(); loadProviderDropdown(); }
            else { alert("删除失败: " + (data.detail || data.message)); }
        } catch (e) { alert("删除失败: " + e.message); }
    }

    // ==================== 动态加载提供商下拉 ====================
    async function loadProviderDropdown() {
        var sel = document.getElementById("res-provider");
        if (!sel) return;
        try {
            var res = await apiFetch("/api/admin/download-providers/active");
            var data = await res.json();
            var providers = (data.code === 0 && data.data) ? data.data : [];
            var html = '<option value="">请选择渠道</option>';
            providers.forEach(function(p) {
                html += '<option value="' + p.id + '">' + escHtml(p.name) + '</option>';
            });
            sel.innerHTML = html;
        } catch (e) {
            sel.innerHTML = '<option value="">加载失败</option>';
        }
    }
'''
    content = content.replace(marker, provider_code + '\n    function renderSettings(body) {')
    changes += 1
    print(f"7. Inserted renderProviderManagement ({len(provider_code)} chars)")

print(f"\nTotal changes: {changes}")
with open(PATH, "w", encoding="utf-8") as f:
    f.write(content)
print("main.js written successfully")
