with open(r"C:\Users\xueta\Documents\web-xiaobaigame\admin\js\main.js", "rb") as f:
    raw = f.read()

print("File size:", len(raw), "bytes")
print()

# Show bytes around position 20-40
for i in range(20, min(len(raw), 40)):
    b = raw[i]
    c = chr(b) if 32 <= b < 127 else "."
    print("  byte {}: 0x{:02x} ({})".format(i, b, c))

# Try to find first decode error position
print()
print("Trying decode...")
import codecs
try:
    text = raw.decode("utf-8")
    print("File is valid UTF-8")
except UnicodeDecodeError as e:
    print("UTF-8 decode error at byte {}-{}: {}".format(e.start, e.end, e.reason))
    # Show the problematic bytes
    s = max(0, e.start - 5)
    e2 = min(len(raw), e.end + 5)
    print("Bytes around error: ", raw[s:e2].hex())
