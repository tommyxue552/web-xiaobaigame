/**

 * 小白游戏资源站 - 首页脚本

 * ================================

 * 动态加载分类、最新游戏、热门游戏，支持搜索和详情弹窗。

 */

(function () {

    'use strict';



    const state = {

        activeCategory: '',

        keyword: '',

        categories: [],

    };



    const $ = (sel) => document.querySelector(sel);

    const $$ = (sel) => document.querySelectorAll(sel);



    // ==================== API ====================

    async function api(url) {

        const res = await fetch(url);

        if (!res.ok) throw new Error('请求失败');

        return res.json();

    }



    async function fetchCategories() {

        return api('/api/categories');

    }



    async function fetchGames(params) {

        const qs = new URLSearchParams(params);

        return api('/api/games?' + qs);

    }



    async function fetchGameDetail(id) {

        return api('/api/game/' + id);

    }



    // ==================== 渲染 ====================



    function renderCategoryTabs(categories) {

        const container = $("#category-tabs");

        let html = '<button class="category-tab active" data-category="">全部</button>';

        categories.forEach(function (c) {

            html += '<button class="category-tab" data-category="' + c.name + '">' + c.name + '</button>';

        });

        container.innerHTML = html;

    }



    function renderGameCards(games, containerId) {

        const container = document.getElementById(containerId);

        if (!container) return;

        if (!games || games.length === 0) {

            container.innerHTML = '<div class="empty-state"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="2" y="2" width="20" height="20" rx="3"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="m21 15-5-5L5 21"/></svg><p>暂无游戏数据</p></div>';

            return;

        }

        container.innerHTML = games.map(function (g) {

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



    function showGameDetail(game) {

        var modal = $(".modal-overlay");

        var cover = $(".modal-cover");

        var title = $(".modal-title");

        var tags = $(".modal-tags");

        var info = $(".modal-info");

        var desc = $(".modal-desc");

        var actions = $(".modal-actions");



        cover.src = game.cover || '';

        cover.onerror = function () { cover.style.display = 'none'; };

        cover.style.display = 'block';

        title.textContent = game.title;

        tags.innerHTML = (game.tags || []).map(function (t) {

            return '<span>' + esc(t) + '</span>';

        }).join('');

        info.innerHTML = ''

            + '<div class="info-item"><span class="info-label">平台</span><span class="info-value">' + esc(game.system || '-') + '</span></div>'

            + '<div class="info-item"><span class="info-label">语言</span><span class="info-value">' + esc(game.language || '-') + '</span></div>'

            + '<div class="info-item"><span class="info-label">大小</span><span class="info-value">' + esc(game.size || '-') + '</span></div>'

            + '<div class="info-item"><span class="info-label">版本</span><span class="info-value">' + esc(game.version || '-') + '</span></div>'

            + '<div class="info-item"><span class="info-label">发行商</span><span class="info-value">' + esc(game.publisher || '-') + '</span></div>'

            + '<div class="info-item"><span class="info-label">开发商</span><span class="info-value">' + esc(game.developer || '-') + '</span></div>';

        desc.textContent = game.description || '暂无描述';

        actions.innerHTML = ''

            + '<button class="btn btn-primary download-btn" data-url="' + esc(game.download_url || '') + '" data-title="' + esc(game.title) + '">下载游戏</button>'

            + '<button class="btn btn-secondary modal-close-btn">关闭</button>';

        modal.classList.add('active');

    }



    function closeModal() {

        $('.modal-overlay').classList.remove('active');

    }



    // ==================== 事件 ====================



    // 分类点击

    $("#category-tabs").addEventListener('click', function (e) {

        var tab = e.target.closest('.category-tab');

        if (!tab) return;

        state.activeCategory = tab.dataset.category;

        // 更新 active 样式

        ('.category-tab').forEach(function (t) { t.classList.remove('active'); });

        tab.classList.add('active');

        loadHomeGames();

    });



    // 游戏卡片点击 -> 跳转详情页

    document.addEventListener('click', function (e) {

        var card = e.target.closest('.game-card');

        if (!card) return;

        var slug = card.dataset.slug;
        var id = card.dataset.id;
        window.open(slug ? '/game/' + slug : '/game/' + id, '_blank');

    });



    // 弹窗关闭

    $(".modal-overlay").addEventListener('click', function (e) {

        if (e.target === this || e.target.classList.contains('modal-close-btn') || e.target.classList.contains('modal-close')) {

            closeModal();

        }

        if (e.target.classList.contains('download-btn')) {

            var url = e.target.dataset.url;

            if (!url) {

                alert('该游戏暂无下载链接');

                return;

            }

            var isMobile = /Android|iPhone|iPad|iPod|webOS/i.test(navigator.userAgent);

            if (isMobile) {

                window.open(url, '_blank');

            } else {

                window.open('/frontend/download.html?url=' + encodeURIComponent(url) + '&title=' + encodeURIComponent(e.target.dataset.title), '_blank');

            }

        }

    });



    // 搜索

    var keywordInput = $("#keyword-input");

    if (keywordInput) {

        keywordInput.addEventListener('input', debounce(function () {

            state.keyword = keywordInput.value.trim();

            loadHomeGames();

        }, 400));

    }



    // 移动端菜单

    var menuBtn = $(".mobile-menu-btn");

    if (menuBtn) {

        menuBtn.addEventListener('click', function () {

            $('.main-nav').classList.toggle('open');

        });

    }



    // ==================== 数据加载 ====================



    async function loadHomeGames() {

        var params = { page: 1, page_size: 8 };

        if (state.activeCategory) params.category = state.activeCategory;

        if (state.keyword) params.keyword = state.keyword;



        // 并行加载最新和热门

        var [latestRes, hotRes] = await Promise.all([

            fetchGames(Object.assign({}, params, { sort: 'latest' })),

            fetchGames(Object.assign({}, params, { sort: 'hot' })),

        ]);



        if (latestRes.code === 0) {

            renderGameCards(latestRes.data.games || latestRes.data.items, 'latest-grid');

        }

        if (hotRes.code === 0) {

            renderGameCards(hotRes.data.games || hotRes.data.items, 'hot-grid');

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

            // 加载分类

            var catRes = await fetchCategories();

            if (catRes.code === 0) {

                state.categories = catRes.data;

                renderCategoryTabs(catRes.data);

            }

            // 加载游戏

            await loadHomeGames();

        } catch (err) {

            console.error('初始化失败:', err);

        }

    }



    document.addEventListener('DOMContentLoaded', init);

})();

