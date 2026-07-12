
import sys, re, os
sys.stdout.reconfigure(encoding="utf-8")

# ============================================================
# Triple-UTF-8 encode helper (to match main.js encoding)
# ============================================================
def t3(s):
    return s.encode("utf-8").decode("latin-1").encode("utf-8").decode("latin-1").encode("utf-8")

# ============================================================
# Step 1: Fix patch_resource.js by replacing ? with Chinese
# ============================================================
patch_path = r"C:\Users\xueta\Documents\web-xiaobaigame\patch_resource.js"
with open(patch_path, "r", encoding="utf-8") as f:
    data = f.read()

# Find all ? sequences
reps = [(m.start(), m.end()) for m in re.finditer(r"\?{2,}", data)]
print(f"Found {len(reps)} ? sequences to fix")

# Mapping: position -> replacement Chinese text
# Ordered by position for clarity
MAP = {
    # pos: replacement
    28: "下载资源管理",        # section comment
    222: "百度网盘",           # provider baidu in providerLabel
    237: "夸克网盘",           # provider quark
    253: "阿里云盘",           # provider alipan
    271: "网盘",              # provider 115 suffix
    350: "待审核",            # status pending
    365: "正常",              # status active
    381: "已禁用",            # status disabled
    397: "已失效",            # status invalid
    575: "下载资源管理",       # panel header h3
    642: "新增资源",           # add button text (+ prefix)
    787: "搜索游戏名称",       # search placeholder
    864: "全部网盘",           # all providers filter
    899: "百度网盘",           # baidu option in filter
    934: "夸克网盘",           # quark option
    970: "阿里云盘",           # alipan option
    1006: "网盘",             # 115 option suffix
    1090: "全部状态",          # all status filter
    1127: "待审核",           # pending option
    1162: "正常",             # active option
    1198: "已禁用",           # disabled option
    1234: "已失效",           # invalid option
    1462: "加载中",            # loading text
    1761: "编辑资源",          # modal header
    1954: "游戏",             # game label
    2076: "搜索游戏名称",      # game search placeholder
    2386: "网盘",             # provider label in form
    2481: "百度网盘",          # baidu option form
    2516: "夸克网盘",          # quark option form
    2552: "阿里云盘",          # alipan option form
    2588: "网盘",             # 115 option form
    2662: "状态",             # status label form
    2751: "待审核",           # pending form
    2795: "正常",             # active form
    2831: "已禁用",           # disabled form
    2867: "已失效",           # invalid form
    2947: "资源标题",          # title label
    3007: "如：游戏本体",      # title placeholder
    3095: "原始URL",           # origin url label (URL kept as-is)
    3168: "原始下载链接",      # origin url placeholder
    3231: "我的分享",          # my share label
    3307: "我的网盘分享链接",   # my share placeholder
    3399: "提取码",           # extract code label
    3472: "如：",             # extract code placeholder prefix
    3534: "显示排序",          # display order label
    3689: "备注",             # remark label
    3761: "备注信息",          # remark placeholder
    4057: "取消",             # cancel button
    4115: "保存",             # save button
    5286: "暂无下载资源，点击右上角新增",  # empty state
    5400: "游戏",             # th: game
    5411: "网盘",             # th: provider
    5422: "标题",             # th: title
    5433: "状态",             # th: status
    5444: "提取码",           # th: extract code
    5456: "排序",             # th: sort
    5467: "更新时间",          # th: update time
    5480: "操作",             # th: action
    6419: "编辑",             # edit button
    6607: "删除",             # delete button
    7073: "上一页",           # prev page
    7516: "下一页",           # next page
    8054: "获取",             # error check text
    8118: "加载失败，请稍后重试", # error state
    9766: "确定删除下载资源 ",  # confirm delete part 1
    9788: "吗？此操作不可恢复。", # confirm delete part 2
    11919: "未找到匹配游戏",    # no match
    12777: "加载失败",         # search error
    12992: "新增资源",         # modal title new
    13949: "获取资源失败",      # fetch error
    14138: "编辑资源",         # modal title edit
    15376: "加载失败",         # catch error
    15719: "请选择游戏",       # no game alert
    16813: "更新成功",         # update success
    16822: "创建成功",         # create success
    16959: "操作失败",         # operation error
    17002: "未知错误",         # unknown error
    17054: "请求失败",         # request error
    17373: "删除失败",         # delete error
    17446: "删除失败",         # delete catch error
}

# Replace from end to start to maintain positions
data_list = list(data)
for start, end in reversed(reps):
    repl = MAP.get(start, "")
    if len(repl) != (end - start):
        ctx = data[max(0,start-15):start]
        print(f"WARNING: pos={start} len_mismatch: ? count={end-start}, repl len={len(repl)}, ctx=...{ctx}...")
    # Replace
    data_list[start:end] = repl

fixed_js = "".join(data_list)
print(f"Fixed JS: {len(fixed_js)} chars")

# Save fixed JS for reference
fixed_path = r"C:\Users\xueta\Documents\web-xiaobaigame\fixed_section.js"
with open(fixed_path, "w", encoding="utf-8") as f:
    f.write(fixed_js)
print("Saved fixed JS")

# ============================================================
# Step 2: Patch main.js
# ============================================================
main_path = r"C:\Users\xueta\Documents\web-xiaobaigame\admin\js\main.js"
with open(main_path, "rb") as f:
    raw = f.read()

print(f"Original main.js: {len(raw)} bytes")

# Encode the fixed JS in triple-UTF-8 to match main.js encoding
encoded_js = t3(fixed_js)
print(f"Encoded JS: {len(encoded_js)} bytes")

# Find and replace menu label: "资源管理" -> "下载资源"
old_menu = t3("资源管理")
new_menu = t3("下载资源")
new_raw = raw.replace(old_menu, new_menu, 1)
print(f"Menu label replaced: {old_menu in raw} -> {new_menu in new_raw}")

# Find and replace the old resource management section
marker = b"===  " + t3("资源管理（下载链接）")
# Actually, let me find the function definition directly
fn_marker = b"function renderResourceManagement(body)"
fn_idx = new_raw.find(fn_marker)
print(f"renderResourceManagement at byte: {fn_idx}")

# Find the start of the section (go backwards to the // ==== comment)
sec_start = new_raw.rfind(b"// ===", 0, fn_idx)
if sec_start < 0:
    sec_start = new_raw.rfind(b"\n", 0, fn_idx) + 1
print(f"Section start: {sec_start}")

# Find the end of the section (look for next major section after the old code)
# The old section ends before the next "// ====" or "function renderSettings"
next_sec = new_raw.find(b"function renderSettings", fn_idx + 100)
if next_sec >= 0:
    sec_end = new_raw.rfind(b"\n", 0, next_sec) + 1
else:
    # Fallback: find next "// ===="
    sec_end = new_raw.find(b"// ===", fn_idx + 100)
    if sec_end < 0:
        sec_end = len(new_raw)
    else:
        sec_end = new_raw.rfind(b"\n", 0, sec_end) + 1
print(f"Section end: {sec_end}")
print(f"Old section length: {sec_end - sec_start} bytes")

# Build the new section with proper boundary markers
# Add a blank line before to separate from previous section
new_section = b"\r\n" + encoded_js
print(f"New section length: {len(new_section)} bytes")

# Replace
final_raw = new_raw[:sec_start] + new_section + new_raw[sec_end:]
print(f"Final main.js: {len(final_raw)} bytes (was {len(raw)})")

# Write back
with open(main_path, "wb") as f:
    f.write(final_raw)
print("main.js patched successfully!")

