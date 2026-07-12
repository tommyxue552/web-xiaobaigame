    // ==================== ?????? ====================
    var downloadResourceState = { page: 1, pageSize: 20, keyword: "", provider: "", status: "", editingId: null };

    function providerLabel(p) { var m = { baidu: "????", quark: "????", alipan: "????", "115": "115??" }; return m[p] || p; }
    function drStatusLabel(s) { var m = { pending: "???", active: "??", disabled: "???", invalid: "???" }; return m[s] || s; }