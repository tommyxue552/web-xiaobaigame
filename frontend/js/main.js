/**
 * 小白游戏资源站 - 前台主脚本
 * ================================
 * 负责游戏列表加载、筛选、分页、详情弹窗。
 */

(function () {
    "use strict";

    // ==================== 状态管理 ====================
    const state = {
        page: 1,
        pageSize: 20,
        total: 0,
        category: "",
        keyword: "",
        games: [],
    };

    // ==================== DOM 引用 ====================
    const $ = (sel) => document.querySelector(sel);
    const $$ = (sel) => document.querySelectorAll(sel);

    const gridEl = $(".game-grid");
    const paginationEl = $(".pagination");
    const modalOverlay = $(".modal-overlay");
    const modalBody = $(".modal .modal-body");
    const modalCover = $(".modal .modal-cover");
    const modalTitle = $(".modal .modal-title");
    const modalTags = $(".modal .modal-tags");
    const modalInfo = $(".modal .modal-info");
    const modalDesc = $(".modal .modal-desc");
    const modalActions = $(".modal .modal-actions");

    // ==================== API 调用 ====================
    async function fetchGames() {
        const params = new URLSearchParams({
            page: state.page,
            page_size: state.pageSize,
            category: state.category,
            keyword: state.keyword,
        });
        const res = await fetch(`/api/games?${params}`);
        if (!res.ok) throw new Error("请求失败");
        return res.json();
    }

    async function fetchGameDetail(id) {
        const res = await fetch(`/api/game/${id}`);
        if (!res.ok) throw new Error("请求失败");
        return res.json();
    }

    // ==================== 渲染 ====================

    function renderGameCards(games) {
        if (games.length === 0) {
            gridEl.innerHTML = `<p style="grid-column:1/-1;text-align:center;color:#999;padding:40px;">暂无游戏数据</p>`;
            return;
        }
        gridEl.innerHTML = games
            .map(
                (g) => `
            <div class="game-card" data-id="${g.id}">
                <img class="card-cover" src="${g.cover || "/frontend/images/placeholder.svg"}"
                     alt="${g.title}" loading="lazy"
                     onerror="this.src='/frontend/images/placeholder.svg'">
                <div class="card-body">
                    <div class="card-title">${escapeHtml(g.title)}</div>
                    <div class="card-meta">
                        <span>${escapeHtml(g.category || "未分类")}</span>
                        <span>${escapeHtml(g.system || "未知平台")}</span>
                    </div>
                </div>
            </div>`
            )
            .join("");
    }

    function renderPagination() {
        const totalPages = Math.ceil(state.total / state.pageSize);
        if (totalPages <= 1) {
            paginationEl.innerHTML = "";
            return;
        }
        paginationEl.innerHTML = `
            <button ${state.page <= 1 ? "disabled" : ""} data-action="prev">上一页</button>
            <span class="page-info">第 ${state.page} / ${totalPages} 页（共 ${state.total} 个）</span>
            <button ${state.page >= totalPages ? "disabled" : ""} data-action="next">下一页</button>
        `;
    }

    function showModal(game) {
        modalCover.src = game.cover || "/frontend/images/placeholder.svg";
        modalCover.onerror = () => { modalCover.src = "/frontend/images/placeholder.svg"; };
        modalTitle.textContent = game.title;
        modalTags.innerHTML = (game.tags || [])
            .map((t) => `<span>${escapeHtml(t)}</span>`)
            .join("");
        modalInfo.innerHTML = `
            <div class="info-row"><span class="info-label">平台</span><span>${escapeHtml(game.system || "-")}</span></div>
            <div class="info-row"><span class="info-label">语言</span><span>${escapeHtml(game.language || "-")}</span></div>
            <div class="info-row"><span class="info-label">大小</span><span>${escapeHtml(game.size || "-")}</span></div>
            <div class="info-row"><span class="info-label">版本</span><span>${escapeHtml(game.version || "-")}</span></div>
            <div class="info-row"><span class="info-label">发行商</span><span>${escapeHtml(game.publisher || "-")}</span></div>
            <div class="info-row"><span class="info-label">开发商</span><span>${escapeHtml(game.developer || "-")}</span></div>
            <div class="info-row"><span class="info-label">发布日期</span><span>${game.release_date || "-"}</span></div>
        `;
        modalDesc.textContent = game.description || "暂无描述";
        modalActions.innerHTML = `
            <button class="btn btn-primary download-btn" data-url="${escapeHtml(game.download_url || "")}"
                    data-title="${escapeHtml(game.title)}">下载游戏</button>
            <button class="btn btn-secondary modal-close-btn">关闭</button>
        `;
        modalOverlay.classList.add("active");
    }

    function closeModal() {
        modalOverlay.classList.remove("active");
    }

    // ==================== 下载逻辑 ====================

    function handleDownload(downloadUrl, title) {
        if (!downloadUrl) {
            alert("该游戏暂无下载链接");
            return;
        }
        // 判断设备类型
        const isMobile = /Android|iPhone|iPad|iPod|webOS/i.test(navigator.userAgent);
        if (isMobile) {
            // 移动端：直接跳转下载链接
            window.open(downloadUrl, "_blank");
        } else {
            // PC 端：跳转二维码页面
            const qrUrl = `/frontend/download.html?url=${encodeURIComponent(downloadUrl)}&title=${encodeURIComponent(title)}`;
            window.open(qrUrl, "_blank");
        }
    }

    // ==================== 事件绑定 ====================

    // 游戏卡片点击 → 详情弹窗
    gridEl.addEventListener("click", async (e) => {
        const card = e.target.closest(".game-card");
        if (!card) return;
        const id = card.dataset.id;
        try {
            const res = await fetchGameDetail(id);
            if (res.code === 0) {
                showModal(res.data);
            }
        } catch (err) {
            console.error("获取游戏详情失败:", err);
        }
    });

    // 弹窗内按钮事件
    modalOverlay.addEventListener("click", (e) => {
        if (e.target === modalOverlay) closeModal();
        if (e.target.classList.contains("modal-close-btn")) closeModal();
        if (e.target.classList.contains("download-btn")) {
            const url = e.target.dataset.url;
            const title = e.target.dataset.title;
            handleDownload(url, title);
        }
    });

    // 分页按钮
    paginationEl.addEventListener("click", (e) => {
        const btn = e.target.closest("button");
        if (!btn || btn.disabled) return;
        const action = btn.dataset.action;
        if (action === "prev") state.page--;
        if (action === "next") state.page++;
        loadGames();
    });

    // 筛选
    $("#category-filter")?.addEventListener("change", (e) => {
        state.category = e.target.value;
        state.page = 1;
        loadGames();
    });
    $("#keyword-input")?.addEventListener("input", debounce((e) => {
        state.keyword = e.target.value.trim();
        state.page = 1;
        loadGames();
    }, 400));

    // ==================== 主流程 ====================

    async function loadGames() {
        try {
            const res = await fetchGames();
            if (res.code === 0) {
                state.games = res.data.items;
                state.total = res.data.total;
                renderGameCards(state.games);
                renderPagination();
            }
        } catch (err) {
            console.error("加载游戏列表失败:", err);
            gridEl.innerHTML = `<p style="grid-column:1/-1;text-align:center;color:#999;padding:40px;">加载失败，请检查后端是否已启动</p>`;
        }
    }

    // ==================== 工具函数 ====================

    function escapeHtml(str) {
        const div = document.createElement("div");
        div.textContent = str;
        return div.innerHTML;
    }

    function debounce(fn, delay) {
        let timer;
        return function (...args) {
            clearTimeout(timer);
            timer = setTimeout(() => fn.apply(this, args), delay);
        };
    }

    // ==================== 初始化 ====================
    document.addEventListener("DOMContentLoaded", loadGames);
})();
