    // ==================== ?????? ====================
    var downloadResourceState = { page: 1, pageSize: 20, keyword: "", provider: "", status: "", editingId: null };

    function providerLabel(p) { var m = { baidu: "????", quark: "????", alipan: "????", "115": "115??" }; return m[p] || p; }
    function drStatusLabel(s) { var m = { pending: "???", active: "??", disabled: "???", invalid: "??" }; return m[s] || s; }

    function renderResourceManagement(body) {
        body.innerHTML =
            '<div class="panel">' +
            '<div class="panel-header"><h3>??????</h3><button class="btn btn-primary" id="add-resource-btn">+ ??????</button></div>' +
            '<div class="toolbar">' +
            '<input type="text" class="search-input" id="dr-keyword" placeholder="??????...">' +
            '<select id="dr-provider-filter"><option value="">????</option><option value="baidu">????</option><option value="quark">????</option><option value="alipan">????</option><option value="115">115??</option></select>' +
            '<select id="dr-status-filter"><option value="">????</option><option value="pending">???</option><option value="active">??</option><option value="disabled">???</option><option value="invalid">??</option></select>' +
            '<span class="toolbar-info" id="dr-count-info"></span>' +
            '</div>' +
            '<div class="panel-body"><div class="resource-table-container"><p style="padding:20px;color:#888;">???...</p></div></div>' +
            '<div class="pagination" id="dr-pagination"></div>' +
            '</div>' +
            // Modal
            '<div class="modal-overlay resource-modal">' +
            '<div class="modal" style="max-width:650px;">' +
            '<div class="modal-header"><h3>????</h3><button class="modal-close-btn res-modal-close">&times;</button></div>' +
            '<div class="modal-body"><form id="resource-form">' +
            '<div class="form-group"><label>?? *</label>' +
            '<div class="game-select-container">' +
            '<input id="res-game-search" placeholder="????????..." autocomplete="off"><span id="res-game-title" style="display:none;font-size:0.85rem;color:#0f3460;font-weight:600;"></span>' +
            '<div class="game-select-dropdown" id="game-dropdown"></div>' +
            '</div></div>' +
            '<div class="form-row"><div class="form-group"><label>???? *</label>' +
            '<select name="provider" id="res-provider"><option value="baidu">????</option><option value="quark">????</option><option value="alipan">????</option><option value="115">115??</option></select></div>' +
            '<div class="form-group"><label>??</label>' +
            '<select name="status" id="res-status"><option value="pending">???</option><option value="active" selected>??</option><option value="disabled">???</option><option value="invalid">??</option></select></div></div>' +
            '<div class="form-group"><label>????</label><input name="title" id="res-title" placeholder="??????v1.2"></div>' +
            '<div class="form-row"><div class="form-group"><label>????URL</label><input name="origin_url" id="res-origin-url" placeholder="???????"></div>' +
            '<div class="form-group"><label>??????</label><input name="my_share_url" id="res-my-share-url" placeholder="????????"></div></div>' +
            '<div class="form-row"><div class="form-group"><label>???</label><input name="extract_code" id="res-extract-code" placeholder="??abcd"></div>' +
            '<div class="form-group"><label>????</label><input name="display_order" id="res-display-order" type="number" value="0" min="0"></div></div>' +
            '<div class="form-group"><label>??</label><textarea name="remark" id="res-remark" rows="3" placeholder="????..."></textarea></div>' +
            '<input type="hidden" name="id" id="res-id" value="">' +
            '<input type="hidden" name="game_id" id="res-game-id" value="">' +
            '</form></div>' +
            '<div class="modal-footer"><button class="btn btn-outline res-modal-cancel">??</button><button class="btn btn-primary res-modal-save">??</button></div>' +
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
            if (info) info.textContent = "? " + total + " ?";

            if (items.length === 0) {
                container.innerHTML = '<div class="empty-state"><p>???????????????????</p></div>';
            } else {
                var html = '<table><thead><tr><th>ID</th><th>??</th><th>??</th><th>??</th><th>??</th><th>???</th><th>??</th><th>????</th><th>??</th></tr></thead><tbody>';
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
                        '<td><button class="btn btn-sm btn-outline dr-edit-btn" data-id="' + r.id + '">??</button> ' +
                        '<button class="btn btn-sm btn-danger dr-delete-btn" data-id="' + r.id + '" data-title="' + escHtml(r.provider + " - " + (r.game_title || "")) + '">??</button></td>' +
                        '</tr>';
                });
                html += '</tbody></table>';
                container.innerHTML = html;
            }

            // Pagination
            var pg = document.getElementById("dr-pagination");
            if (pg) {
                var totalPages = Math.ceil(total / s.pageSize) || 1;
                var phtml = '<button' + (s.page <= 1 ? ' disabled' : '') + ' data-page="' + (s.page - 1) + '">???</button>';
                var start = Math.max(1, s.page - 2);
                var end = Math.min(totalPages, s.page + 2);
                for (var i = start; i <= end; i++) {
                    phtml += '<button class="' + (i === s.page ? 'active' : '') + '" data-page="' + i + '">' + i + '</button>';
                }
                phtml += '<button' + (s.page >= totalPages ? ' disabled' : '') + ' data-page="' + (s.page + 1) + '">???</button>';
                phtml += '<span class="page-info">?' + s.page + '/' + totalPages + ' ?</span>';
                pg.innerHTML = phtml;
                pg.querySelectorAll("button[data-page]").forEach(function(btn) {
                    btn.addEventListener("click", function() {
                        downloadResourceState.page = parseInt(btn.dataset.page);
                        loadDownloadResources();
                    });
                });
            }
        } catch (e) {
            if (e.message.indexOf("??") === -1) container.innerHTML = '<div class="empty-state"><p>???????????????</p></div>';
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
                    if (confirm("?????????" + title + "???????????")) deleteResource(parseInt(id));
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
            if (games.length === 0) html = '<div class="game-option" style="color:#888;">????????</div>';
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
        } catch (e) { dd.innerHTML = '<div class="game-option" style="color:#c62828;">????</div>'; dd.classList.add("active"); }
    }

    function openResourceModal() {
        downloadResourceState.editingId = null;
        document.querySelector(".resource-modal .modal-header h3").textContent = "??????";
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
            if (data.code !== 0) { alert("??????"); return; }
            var r = data.data;
            downloadResourceState.editingId = r.id;
            document.querySelector(".resource-modal .modal-header h3").textContent = "??????";
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
        } catch (e) { alert("????: " + e.message); }
    }

    function closeResourceModal() {
        document.querySelector(".resource-modal").classList.remove("active");
        downloadResourceState.editingId = null;
    }

    async function saveResource() {
        var gameId = parseInt(document.getElementById("res-game-id").value);
        if (!gameId) { alert("?????"); return; }

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
                alert(id ? "????" : "????");
                closeResourceModal();
                await loadDownloadResources();
            } else {
                alert("????: " + (data.detail || data.message || "????"));
            }
        } catch (e) { alert("????: " + e.message); }
    }

    async function deleteResource(id) {
        try {
            var res = await apiFetch("/api/admin/download-resources/" + id, { method: "DELETE" });
            var data = await res.json();
            if (data.code === 0) { await loadDownloadResources(); }
            else { alert("????: " + (data.detail || data.message)); }
        } catch (e) { alert("????: " + e.message); }
    }