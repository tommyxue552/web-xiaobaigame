/**
 * 小白游戏资源站 - 游戏详情页脚本
 * ================================
 * 加载游戏完整信息、截图画廊、下载按钮（PC 二维码 / 手机直跳）。
 */
(function () {
    'use strict';

    var state = {
        gameId: null,
        game: null,
        lightboxIdx: 0,
    };

    var $ = function (sel) { return document.querySelector(sel); };
    var $$ = function (sel) { return document.querySelectorAll(sel); };

    // ==================== 初始化 ====================

    function init() {
        var params = new URLSearchParams(window.location.search);
        var id = parseInt(params.get('id'), 10);
        if (!id) {
            showError('缺少游戏 ID 参数');
            return;
        }
        state.gameId = id;
        loadGame();
    }

    async function loadGame() {
        try {
            var res = await fetch('/api/game/' + state.gameId);
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
            renderAll();
        } catch (err) {
            console.error('加载游戏详情失败:', err);
            showError('网络错误，请检查后端服务是否启动');
        }
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

        // 页面标题
        document.title = g.title + ' - 小白游戏资源站';
        $('#breadcrumb-title').textContent = g.title;

        // 封面
        var cover = $('#detail-cover');
        cover.src = g.cover || '';
        cover.alt = g.title;
        cover.onerror = function () {
            this.style.display = 'none';
        };

        // 标题 + 标签
        $('#detail-title').textContent = g.title;
        renderTags(g.tags);
        renderMetaGrid(g);
        renderScreenshots(g.images);
        renderDescription(g.description);
        renderDownloadBar(g);

        // 绑定事件
        bindEvents();
    }

    function renderTags(tags) {
        var container = $('#detail-tags');
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
        ];
        $('#detail-meta-grid').innerHTML = fields.map(function (f) {
            return '<div class="meta-item"><span class="meta-label">' + esc(f.label) + '</span><span class="meta-value">' + esc(f.value) + '</span></div>';
        }).join('');
    }

    function renderScreenshots(images) {
        var section = $('#detail-screenshots-section');
        var gallery = $('#screenshots-gallery');
        var list = images || [];
        if (!Array.isArray(list)) list = [];

        if (list.length === 0) {
            section.style.display = 'none';
            return;
        }

        state.screenshots = list;
        gallery.innerHTML = list.map(function (url, idx) {
            return '<div class="screenshot-thumb" data-idx="' + idx + '">'
                + '<img src="' + esc(url) + '" alt="截图 ' + (idx + 1) + '" loading="lazy" onerror="this.parentElement.style.display=\'none\'">'
                + '</div>';
        }).join('');
    }

    function renderDescription(desc) {
        var el = $('#detail-desc');
        el.textContent = desc || '暂无简介';
    }

    function renderDownloadBar(g) {
        var bar = $('#download-bar');
        bar.style.display = 'flex';
        $('#download-bar-title').textContent = g.title;
        $('#download-bar-size').textContent = g.size || '';
    }

    // ==================== 事件绑定 ====================

    function bindEvents() {
        // 移动端菜单
        var menuBtn = $('.mobile-menu-btn');
        if (menuBtn) {
            menuBtn.addEventListener('click', function () {
                document.querySelector('.main-nav').classList.toggle('open');
            });
        }

        // 下载按钮
        $('#download-bar-btn').addEventListener('click', function () {
            handleDownload();
        });

        // 截图点击 → 灯箱
        $('#screenshots-gallery').addEventListener('click', function (e) {
            var thumb = e.target.closest('.screenshot-thumb');
            if (!thumb) return;
            var idx = parseInt(thumb.dataset.idx, 10);
            openLightbox(idx);
        });

        // 灯箱关闭
        $('#screenshot-lightbox').addEventListener('click', function (e) {
            if (e.target === this || e.target.classList.contains('lightbox-close')) {
                closeLightbox();
            }
        });

        // 灯箱切换
        $('.lightbox-prev').addEventListener('click', function (e) {
            e.stopPropagation();
            navigateLightbox(-1);
        });
        $('.lightbox-next').addEventListener('click', function (e) {
            e.stopPropagation();
            navigateLightbox(1);
        });

        // 键盘控制灯箱
        document.addEventListener('keydown', function (e) {
            if (!document.querySelector('.screenshot-lightbox.active')) return;
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
            // 手机端：直接跳转下载链接
            window.open(g.download_url, '_blank');
        } else {
            // PC 端：跳转到下载页面（二维码）
            window.open('/download/' + state.gameId, '_blank');
        }
    }

    // ==================== 灯箱 ====================

    function openLightbox(idx) {
        var list = state.screenshots || [];
        if (list.length === 0) return;
        state.lightboxIdx = Math.max(0, Math.min(idx, list.length - 1));
        updateLightboxImage();
        $('#screenshot-lightbox').classList.add('active');
        document.body.style.overflow = 'hidden';
    }

    function closeLightbox() {
        $('#screenshot-lightbox').classList.remove('active');
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
        img.src = list[state.lightboxIdx] || '';
        img.alt = '截图 ' + (state.lightboxIdx + 1);
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