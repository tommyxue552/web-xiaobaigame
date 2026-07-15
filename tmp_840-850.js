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
