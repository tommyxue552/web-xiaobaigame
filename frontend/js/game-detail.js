/**
 * 小白游戏资源站 - 游戏详情页脚本
 * ================================
 * 支持内嵌数据（window.__GAME_DATA__）与 API 回退。
 * 支持 ?slug=xxx 和 ?id=xxx 参数。
 * 模块5：SEO 优化。
 */
(function () {
    'use strict';

    var state = {
        gameId: null,
        gameSlug: null,
        game: null,
        lightboxIdx: 0,
    };

    var $ = function (sel) { return document.querySelector(sel); };
    var $$ = function (sel) { return document.querySelectorAll(sel); };

    // ==================== 初始化 ====================

    function init() {
        // 优先使用内嵌数据
        if (window.__GAME_DATA__) {
            state.game = window.__GAME_DATA__;
            state.gameId = state.game.id;
            state.gameSlug = state.game.slug;
            renderAll();
            return;
        }

        // 从 URL 参数获取
        var params = new URLSearchParams(window.location.search);
        var slug = params.get('slug');
        var id = params.get('id');

        if (slug) {
            state.gameSlug = slug;
            loadGameBySlug(slug);
        } else if (id) {
            state.gameId = parseInt(id, 10);
            loadGameById(state.gameId);
        } else {
            showError('缺少游戏标识参数');
        }
    }

    async function loadGameBySlug(slug) {
        try {
            var res = await fetch('/api/game/slug/' + encodeURIComponent(slug));
            if (!res.ok) {
                showError('游戏不存在或未发布');
                return;
            }
            var data = await res.json();
            if (data.code !== 0) {
                showError(data.message || '加载失败');
                return;
            }
            state.game = data.data;
            state.gameId = state.game.id;
            state.gameSlug = state.game.slug;
            updatePageMeta(state.game);
            renderAll();
        } catch (err) {
            console.error('加载游戏详情失败:', err);
            showError('网络错误，请检查后端服务是否启动');
        }
    }

    async function loadGameById(id) {
        try {
            var res = await fetch('/api/game/' + id);
            if (!res.ok) {
                showError('游戏不存在或未发布');
                return;
            }
            var data = await res.json();
            if (data.code !== 0) {
                showError(data.message || '加载失败');
                return;
            }
            state.game = data.data;
            state.gameId = state.game.id;
            state.gameSlug = state.game.slug;
            updatePageMeta(state.game);
            renderAll();
        } catch (err) {
            console.error('加载游戏详情失败:', err);
            showError('网络错误，请检查后端服务是否启动');
        }
    }

    function updatePageMeta(g) {
        // 动态更新页面标题（在 JS 加载模式下）
        document.title = (g.seo_title || (g.title + ' - 小白游戏资源站'));
        var descEl = document.querySelector('meta[name="description"]');
        if (descEl) descEl.setAttribute('content', g.seo_description || (g.description || '').substring(0, 160));
        var kwEl = document.querySelector('meta[name="keywords"]');
        if (kwEl) kwEl.setAttribute('content', g.seo_keywords || (g.title + ',游戏下载,单机游戏' + (g.category ? ',' + g.category : '')));
    }

    function showError(msg) {
        var loading = $('#detail-loading');
        if (loading) {
            loading.innerHTML = '<div class="empty-state" style="padding:80px 20px"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg><p>' + esc(msg) + '</p></div>';
        }
    }

    // ==================== 渲染 ====================

    function renderAll() {
        var g = state.game;

        // 隐藏骨架，显示内容
        $('#detail-loading').style.display = 'none';
        $('#detail-content').style.display = 'block';

        // 面包屑
        document.title = (g.seo_title || (g.title + ' - 小白游戏资源站'));
        var bcTitle = $('#breadcrumb-title');
        if (bcTitle) bcTitle.textContent = g.title;

        // 封面
        var cover = $('#detail-cover');
        if (cover) {
            cover.src = g.cover || '';
            cover.alt = g.title;
            cover.onerror = function () {
                this.style.display = 'none';
            };
        }

        // 标题
        var titleEl = $('#detail-title');
        if (titleEl) titleEl.textContent = g.title;

        renderTags(g.tags);
        renderMetaGrid(g);
        renderScreenshots(g.images);
        renderDescription(g.description);
        renderDownloadBar(g);

        bindEvents();
    }

    function renderTags(tags) {
        var container = $('#detail-tags');
        if (!container) return;
        var list = tags || [];
        if (!Array.isArray(list) || list.length === 0) {
            container.style.display = 'none';
            return;
        }
        container.innerHTML = list.map(function (t) {
            return '<span>' + esc(t) + '</span>';
        }).join('');
    }

    function renderMetaGrid(g) {
        var el = $('#detail-meta-grid');
        if (!el) return;
        var fields = [
            { label: '游戏分类', value: g.category_name || g.category || '-' },
            { label: '游戏大小', value: g.size || '-' },
            { label: '版本', value: g.version || '-' },
            { label: '语言', value: g.language || '-' },
            { label: '运行平台', value: g.system || '-' },
            { label: '开发商', value: g.developer || '-' },
            { label: '发行商', value: g.publisher || '-' },
            { label: '发行日期', value: g.release_date || '-' },
            { label: '更新时间', value: formatDate(g.updated_at) },
            { label: '浏览次数', value: g.views != null ? g.views.toString() : '0' },
        ];
        el.innerHTML = fields.map(function (f) {
            return '<div class="meta-item"><span class="meta-label">' + esc(f.label) + '</span><span class="meta-value">' + esc(f.value) + '</span></div>';
        }).join('');
    }

    function renderScreenshots(images) {
        var section = $('#detail-screenshots-section');
        var gallery = $('#screenshots-gallery');
        if (!section || !gallery) return;
        var list = images || [];
        if (!Array.isArray(list)) list = [];

        if (list.length === 0) {
            section.style.display = 'none';
            return;
        }

        state.screenshots = list;
        gallery.innerHTML = list.map(function (url, idx) {
            return '<div class="screenshot-thumb" data-idx="' + idx + '">'
                + '<img src="' + esc(url) + '" alt="' + esc(state.game.title) + ' 截图 ' + (idx + 1) + '" loading="lazy" onerror="this.parentElement.style.display=\'none\'">'
                + '</div>';
        }).join('');
    }

    function renderDescription(desc) {
        var el = $('#detail-desc');
        if (el) el.textContent = desc || '暂无简介';
    }

    function renderDownloadBar(g) {
        var bar = $('#download-bar');
        if (!bar) return;
        bar.style.display = 'flex';
        var titleEl = $('#download-bar-title');
        var sizeEl = $('#download-bar-size');
        if (titleEl) titleEl.textContent = g.title;
        if (sizeEl) sizeEl.textContent = g.size || '';
    }

    // ==================== 事件绑定 ====================

    function bindEvents() {
        var menuBtn = $('.mobile-menu-btn');
        if (menuBtn) {
            menuBtn.addEventListener('click', function () {
                var nav = document.querySelector('.main-nav');
                if (nav) nav.classList.toggle('open');
            });
        }

        var downloadBtn = $('#download-bar-btn');
        if (downloadBtn) {
            downloadBtn.addEventListener('click', function () {
                handleDownload();
            });
        }

        var sg = $('#screenshots-gallery');
        if (sg) {
            sg.addEventListener('click', function (e) {
                var thumb = e.target.closest('.screenshot-thumb');
                if (!thumb) return;
                var idx = parseInt(thumb.dataset.idx, 10);
                openLightbox(idx);
            });
        }

        var lb = $('#screenshot-lightbox');
        if (lb) {
            lb.addEventListener('click', function (e) {
                if (e.target === this || e.target.classList.contains('lightbox-close')) {
                    closeLightbox();
                }
            });
        }

        var prevBtn = $('.lightbox-prev');
        var nextBtn = $('.lightbox-next');
        if (prevBtn) prevBtn.addEventListener('click', function (e) { e.stopPropagation(); navigateLightbox(-1); });
        if (nextBtn) nextBtn.addEventListener('click', function (e) { e.stopPropagation(); navigateLightbox(1); });

        document.addEventListener('keydown', function (e) {
            var activeLb = document.querySelector('.screenshot-lightbox.active');
            if (!activeLb) return;
            if (e.key === 'Escape') closeLightbox();
            if (e.key === 'ArrowLeft') navigateLightbox(-1);
            if (e.key === 'ArrowRight') navigateLightbox(1);
        });
    }

    // ==================== 下载逻辑 ====================

    function handleDownload() {
        var g = state.game;
        if (!g || !g.download_url) {
            alert('该游戏暂无下载链接');
            return;
        }

        var isMobile = /Android|iPhone|iPad|iPod|webOS|BlackBerry/i.test(navigator.userAgent);

        if (isMobile) {
            window.open(g.download_url, '_blank');
        } else {
            window.open('/download/' + state.gameId, '_blank');
        }
    }

    // ==================== 灯箱 ====================

    function openLightbox(idx) {
        var list = state.screenshots || [];
        if (list.length === 0) return;
        state.lightboxIdx = Math.max(0, Math.min(idx, list.length - 1));
        updateLightboxImage();
        var lb = $('#screenshot-lightbox');
        if (lb) lb.classList.add('active');
        document.body.style.overflow = 'hidden';
    }

    function closeLightbox() {
        var lb = $('#screenshot-lightbox');
        if (lb) lb.classList.remove('active');
        document.body.style.overflow = '';
    }

    function navigateLightbox(delta) {
        var list = state.screenshots || [];
        if (list.length === 0) return;
        state.lightboxIdx = (state.lightboxIdx + delta + list.length) % list.length;
        updateLightboxImage();
    }

    function updateLightboxImage() {
        var list = state.screenshots || [];
        if (list.length === 0) return;
        var img = $('#lightbox-img');
        if (img) {
            img.src = list[state.lightboxIdx] || '';
            img.alt = (state.game ? state.game.title : '') + ' 截图 ' + (state.lightboxIdx + 1);
        }
    }

    // ==================== 工具函数 ====================

    function esc(str) {
        if (str == null) return '';
        var div = document.createElement('div');
        div.textContent = String(str);
        return div.innerHTML;
    }

    function formatDate(dateStr) {
        if (!dateStr) return '-';
        var d = new Date(dateStr);
        if (isNaN(d.getTime())) return dateStr.substring(0, 10);
        return d.getFullYear() + '-' +
            String(d.getMonth() + 1).padStart(2, '0') + '-' +
            String(d.getDate()).padStart(2, '0');
    }

    // ==================== 启动 ====================
    document.addEventListener('DOMContentLoaded', init);
})();