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
    }
    function renderProviderManagement(body) {
        body.innerHTML = "<div style=\"padding:40px;text-align:center;color:#888;">加载中...</div>";
        loadProviderTable(body);
    }

    async function loadProviderTable(container) {
        try {
            var res = await apiFetch("/api/admin/download-providers");
            var data = await res.json();
            if (data.code !== 0) throw new Error(data.message || "失败");
            var providers = data.data.items || data.data;
            if (!container) container = document.querySelector(".main-body");
            var rows = providers.map(function(p) {
                var statusClass = p.is_active ? "badge-published" : "badge-draft";
                var statusText = p.is_active ? "启用" : "禁用";
                return "<tr>" +
