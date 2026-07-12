    // ==================== 下载资源管理 ====================
    var downloadResourceState = { page: 1, pageSize: 20, keyword: "", provider: "", status: "", editingId: null };

    function providerLabel(p) { var m = { baidu: "百度网盘", quark: "夸克网盘", alipan: "阿里云盘", "115": "115网盘" }; return m[p] || p; }
    function drStatusLabel(s) { var m = { pending: "待审核", active: "正常", disabled: "已禁用", invalid: "已失效" }; return m[s] || s; }