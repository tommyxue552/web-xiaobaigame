
import sys
sys.stdout.reconfigure(encoding="utf-8")
CN = {
    "baidu": "百度网盘",
    "quark": "夸克网盘",
    "alipan": "阿里云盘",
}
for k, v in CN.items():
    print(k, "=", v)
print("OK:", len(CN))

