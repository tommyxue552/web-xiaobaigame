path = r"C:\Users\xueta\Documents\web-xiaobaigame\admin\js\main.js"

with open(path, "rb") as f:
    raw = f.read()

corruptions = []
i = 0
while i < len(raw) - 2:
    b1 = raw[i]
    b2 = raw[i+1]
    b3 = raw[i+2]
    if 0xe0 <= b1 <= 0xef and 0x80 <= b2 <= 0xbf and b3 == 0x3f:
        start = max(0, i-15)
        end = min(len(raw), i+20)
        context = raw[start:end]
        corruptions.append((i, b1, b2, context))
    i += 1

print("Found", len(corruptions), "corrupted UTF-8 sequences")

# Show first 10 with hex context
for idx, (pos, b1, b2, ctx) in enumerate(corruptions[:10]):
    print()
    print("--- Corruption", idx+1, "at byte", pos, "---")
    print("Corrupted bytes: 0x{:02x} 0x{:02x} 0x3f".format(b1, b2))
    print("Context hex:", ctx.hex())
    # Show what the partial character would be if we added a 0x80 byte
    test = bytes([b1, b2, 0x80])
    print("Partial char (guess):", test.decode("utf-8", errors="replace"))
