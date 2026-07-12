import re

path = r"C:\Users\xueta\Documents\web-xiaobaigame\admin\js\main.js"

with open(path, "rb") as f:
    raw = f.read()

# Find all positions where a valid 2-byte UTF-8 continuation is followed by 0x3f
# Pattern: byte1 in [0xe0-0xef], byte2 in [0x80-0xbf], byte3 = 0x3f
corruptions = []
i = 0
while i < len(raw) - 2:
    b1 = raw[i]
    b2 = raw[i+1]
    b3 = raw[i+2]
    if 0xe0 <= b1 <= 0xef and 0x80 <= b2 <= 0xbf and b3 == 0x3f:
        # This is a corrupted 3-byte sequence
        # Get context
        start = max(0, i-10)
        end = min(len(raw), i+15)
        context = raw[start:end]
        corruptions.append((i, b1, b2, b3, context))
    i += 1

print(f"Found {len(corruptions)} corrupted UTF-8 sequences")
print()
for pos, b1, b2, b3, ctx in corruptions[:20]:
    # Decode context with error handling
    ctx_str = ctx.decode("utf-8", errors="replace")
    print(f"Byte {pos}: 0x{b1:02x} 0x{b2:02x} 0x{b3:02x} -> {ctx_str}")
