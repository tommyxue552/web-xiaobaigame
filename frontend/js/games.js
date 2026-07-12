/**
 * 小白游戏资源站 - 游戏列表页脚本
 * ================================
 * 分页浏览、分类筛选、搜索、详情弹窗。
 */
(function () {
    'use strict';

    var state = {
        page: 1,
        pageSize: 20,
        total: 0,
        category: '',
        keyword: '',
        games: [],
    };

    var $ = function (sel) { return document.querySelector(sel); };

    // ==================== API ====================
    async function api(url) {
        var res = await fetch(url);
        if (!res.ok) throw new Error('请求失败');
        return res.json();
    }

    async function fetchCategories() {
        return api('/api/categories');
    }

    async function fetchGames() {
        var qs = new URLSearchParams({
            page: state.page,
            page_size: state.pageSize,
            category: state.category,
            keyword: state.keyword,
        });
        return api('/api/games?' + qs);
    }

    async function fetchGameDetail(id) {
        return api('/api/game/' + id);
    }

    // ==================== 渲染 ====================

    function renderCategories(categories) {
        var sel = #category-filter;
        categories.forEach(function (c) {
            var opt = document.createElement('option');
            opt.value = c.name;
            opt.textContent = c.name;
            sel.appendChild(opt);
        });
    }

    function renderGameCards(games) {
        var grid = #game-grid;
        if (!games || games.length === 0) {
            grid.innerHTML = '<div class="empty-state"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="2" y="2" width="20" height="20" rx="3"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="m21 15-5-5L5 21"/></svg><p>暂无游戏数据</p></div>';
            return;
        }
        grid.innerHTML = games.map(function (g) {
            var coverHtml = g.cover
                ? '<img class="card-cover" src="' + g.cover + '" alt="' + esc(g.title) + '" loading="lazy" onerror="this.style.display=\'none\';this.nextElementSibling.style.display=\'flex\';">'
                : '';
            var placeholderHtml = g.cover
                ? '<div class="card-cover-placeholder" style="display:none"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="2" y="2" width="20" height="20" rx="3"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="m21 15-5-5L5 21"/></svg></div>'
                : '<div class="card-cover-placeholder"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="2" y="2" width="20" height="20" rx="3"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="m21 15-5-5L5 21"/></svg></div>';
            var catName = g.category_name || g.category || '未分类';
            return '<div class="game-card" data-id="' + g.id + '" data-slug="' + esc(g.slug || '') + '">'
                + coverHtml + placeholderHtml
                + '<div class="card-body">'
                + '<div class="card-title">' + esc(g.title) + '</div>'
                + '<div class="card-meta">'
                + '<span class="meta-category">' + esc(catName) + '</span>'
                + (g.size ? '<span>' + esc(g.size) + '</span>' : '')
                + '</div>'
                + '</div></div>';
        }).join('');
    }

    function renderPagination() {
        var container = #pagination;
        var totalPages = Math.ceil(state.total / state.pageSize);
        if (totalPages <= 1) {
            container.innerHTML = '';
            return;
        }
        var html = '<button ' + (state.page <= 1 ? 'disabled' : '') + ' data-action="prev">上一页</button>';

        // 页码按钮
        var startPage = Math.max(1, state.page - 2);
        var endPage = Math.min(totalPages, state.page + 2);
        for (var i = startPage; i <= endPage; i++) {
            html += '<span class="page-num' + (i === state.page ? ' active' : '') + '" data-page="' + i + '">' + i + '</span>';
        }

        html += '<button ' + (state.page >= totalPages ? 'disabled' : '') + ' data-action="next">下一页</button>';
        html += '<span class="page-info">共 ' + state.total + ' 个游戏</span>';
        container.innerHTML = html;
    }

    function updateResultCount() {
        #result-count.textContent = '共 ' + state.total + ' 个游戏';
    }

    function showGameDetail(game) {
        var modal = .modal-overlay;
        .modal-cover.src = game.cover || '';
        .modal-cover.onerror = function () { this.style.display = 'none'; };
        .modal-cover.style.display = 'block';
        .modal-title.textContent = game.title;
        .modal-tags.innerHTML = (game.tags || []).map(function (t) {
            return '<span>' + esc(t) + '</span>';
        }).join('');
        .modal-info.innerHTML = ''
            + '<div class="info-item"><span class="info-label">平台</span><span class="info-value">' + esc(game.system || '-') + '</span></div>'
            + '<div class="info-item"><span class="info-label">语言</span><span class="info-value">' + esc(game.language || '-') + '</span></div>'
            + '<div class="info-item"><span class="info-label">大小</span><span class="info-value">' + esc(game.size || '-') + '</span></div>'
            + '<div class="info-item"><span class="info-label">版本</span><span class="info-value">' + esc(game.version || '-') + '</span></div>'
            + '<div class="info-item"><span class="info-label">发行商</span><span class="info-value">' + esc(game.publisher || '-') + '</span></div>'
            + '<div class="info-item"><span class="info-label">开发商</span><span class="info-value">' + esc(game.developer || '-') + '</span></div>';
        .modal-desc.textContent = game.description || '暂无描述';
        .modal-actions.innerHTML = ''
            + '<button class="btn btn-primary download-btn" data-url="' + esc(game.download_url || '') + '" data-title="' + esc(game.title) + '">下载游戏</button>'
            + '<button class="btn btn-secondary modal-close-btn">关闭</button>';
        modal.classList.add('active');
    }

    function closeModal() {
        .modal-overlay.classList.remove('active');
    }

    // ==================== 事件 ====================

    #game-grid.addEventListener('click', function (e) {
        var card = e.target.closest('.game-card');
        if (!card) return;
        var slug = card.dataset.slug;
        var id = card.dataset.id;
        window.open(slug ? '/game/' + slug : '/game/' + id, '_blank');
    });

    .modal-overlay.addEventListener('click', function (e) {
        if (e.target === this || e.target.classList.contains('modal-close-btn') || e.target.classList.contains('modal-close')) {
            closeModal();
        }
        if (e.target.classList.contains('download-btn')) {
            var url = e.target.dataset.url;
            if (!url) { alert('该游戏暂无下载链接'); return; }
            var isMobile = /Android|iPhone|iPad|iPod|webOS/i.test(navigator.userAgent);
            if (isMobile) {
                window.open(url, '_blank');
            } else {
                window.open('/frontend/download.html?url=' + encodeURIComponent(url) + '&title=' + encodeURIComponent(e.target.dataset.title), '_blank');
            }
        }
    });

    #pagination.addEventListener('click', function (e) {
        var btn = e.target.closest('button');
        if (btn && !btn.disabled) {
            if (btn.dataset.action === 'prev') state.page--;
            if (btn.dataset.action === 'next') state.page++;
            loadGames();
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
        var pageNum = e.target.closest('.page-num');
        if (pageNum) {
            state.page = parseInt(pageNum.dataset.page);
            loadGames();
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
    });

    #category-filter.addEventListener('change', function () {
        state.category = this.value;
        state.page = 1;
        loadGames();
    });

    #keyword-input.addEventListener('input', debounce(function () {
        state.keyword = this.value.trim();
        state.page = 1;
        loadGames();
    }, 400));

    // 移动端菜单
    var menuBtn = .mobile-menu-btn;
    if (menuBtn) {
        menuBtn.addEventListener('click', function () {
            document.querySelector('.main-nav').classList.toggle('open');
        });
    }

    // ==================== 数据加载 ====================

    async function loadGames() {
        try {
            var res = await fetchGames();
            if (res.code === 0) {
                var data = res.data;
                state.games = data.games || data.items;
                state.total = data.total;
                renderGameCards(state.games);
                renderPagination();
                updateResultCount();
            }
        } catch (err) {
            console.error('加载失败:', err);
            #game-grid.innerHTML = '<div class="empty-state"><p>加载失败，请检查后端服务是否启动</p></div>';
        }
    }

    // ==================== 工具函数 ====================

    function esc(str) {
        if (!str) return '';
        var div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    function debounce(fn, delay) {
        var timer;
        return function () {
            var ctx = this, args = arguments;
            clearTimeout(timer);
            timer = setTimeout(function () { fn.apply(ctx, args); }, delay);
        };
    }

    // ==================== 初始化 ====================

    async function init() {
        try {
            var catRes = await fetchCategories();
            if (catRes.code === 0) {
                renderCategories(catRes.data);
            }
        } catch (e) { /* 分类加载失败不阻塞 */ }
        loadGames();
    }

    document.addEventListener('DOMContentLoaded', init);
})();
