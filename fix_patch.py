
import sys, re, os
sys.stdout.reconfigure(encoding="utf-8")

# Read patch file
patch_path = r"C:\Users\xueta\Documents\web-xiaobaigame\patch_resource.js"
with open(patch_path, "r", encoding="utf-8") as f:
    data = f.read()

# Define replacements: list of (start_pos, length, replacement)
# Processed in reverse order to maintain positions
reps = []
for m in re.finditer(r"\?{2,}", data):
    reps.append((m.start(), m.end(), m.group()))

# Now assign correct Chinese for each position
mapping = {
    # Section header + panel titles
    28: chr(0x4e0b)+chr(0x8f7d)+chr(0x8d44)+chr(0x6e90)+chr(0x7ba1)+chr(0x7406),  # 下载资源管理
    575: chr(0x4e0b)+chr(0x8f7d)+chr(0x8d44)+chr(0x6e90)+chr(0x7ba1)+chr(0x7406),  # 下载资源管理
    # Provider labels (function)
    222: chr(0x767e)+chr(0x5ea6)+chr(0x7f51)+chr(0x76d8),  # 百度网盘
    237: chr(0x5938)+chr(0x514b)+chr(0x7f51)+chr(0x76d8),  # 夸克网盘
    253: chr(0x963f)+chr(0x91cc)+chr(0x4e91)+chr(0x76d8),  # 阿里云盘
    271: chr(0x7f51)+chr(0x76d8),  # 网盘
    # Status labels (function)
    350: chr(0x5f85)+chr(0x5ba1)+chr(0x6838),  # 待审核
    365: chr(0x6b63)+chr(0x5e38),  # 正常
    381: chr(0x5df2)+chr(0x7981)+chr(0x7528),  # 已禁用
    397: chr(0x5df2)+chr(0x5931)+chr(0x6548),  # 已失效
    # Add button
    642: chr(0x65b0)+chr(0x589e)+chr(0x8d44)+chr(0x6e90),  # 新增资源 (+ prefix)
}
print("Built mapping with", len(mapping), "entries")
print("First test:", mapping.get(28, "NOT FOUND"))

