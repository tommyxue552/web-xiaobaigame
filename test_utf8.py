import sys
sys.stdout.reconfigure(encoding='utf-8')

# Chinese strings using escape sequences
CN = {
    'download_resources': '\u4e0b\u8f7d\u8d44\u6e90\u7ba1\u7406',
    'baidu': '\u767e\u5ea6\u7f51\u76d8',
    'quark': '\u5938\u514b\u7f51\u76d8',
    'alipan': '\u963f\u91cc\u4e91\u76d8',
    'pan115': '115\u7f51\u76d8',
    'pending': '\u5f85\u5ba1\u6838',
    'active': '\u6b63\u5e38',
    'disabled': '\u5df2\u7981\u7528',
    'invalid': '\u5df2\u5931\u6548',
}
for k, v in CN.items():
    print(f'{k}: {v}')
print('OK')