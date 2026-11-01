"""sjstr.py: list SJIS runs (>= 2 double-byte chars) in a file; linear scan, no regex backtracking.

    python -X utf8 tools/sjstr.py FILE [BASE_HEX]   # prints offset+BASE, byte length, text
"""
import sys
b = open(sys.argv[1], 'rb').read()
base = int(sys.argv[2], 16) if len(sys.argv) > 2 else 0
minlen = 4
i = 0; n = 0
while i < len(b):
    j = i; sj = 0
    while j < len(b):
        c = b[j]
        if (0x81 <= c <= 0x9f or 0xe0 <= c <= 0xef) and j + 1 < len(b) and 0x40 <= b[j+1] <= 0xfc and b[j+1] != 0x7f:
            j += 2; sj += 1
        elif 0x20 <= c < 0x7f or c in (0x0a, 0x0d):
            j += 1
        else:
            break
    if sj >= 2 and j - i >= minlen:
        print(f"{base + i:08x} {j-i:4d} {b[i:j].decode('cp932', 'replace')}")
        n += 1
        i = j
    else:
        i = max(j, i + 1)
print("total", n, file=sys.stderr)
