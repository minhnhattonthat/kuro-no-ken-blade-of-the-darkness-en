"""sctext.py: text codec for this game's strings (Shift-JIS + the engine's backslash escapes).

    from sctext import decode, encode
    text = decode(raw_bytes)                 # no terminator, no length
    assert encode(text) == raw_bytes

Encoding is plain cp932 (docs/re/text.md). Inside a string the renderer at 0x80051a78 (SLPS_010.30) treats
0x5c '\' as an escape when it stands at a character boundary: the next byte selects a handler from the table
at RAM 0x80010a10 (index = byte - 0x58, so only 0x58..0x79 are escapes):

    n  newline (y += 14)              f  end of page (top of the table: the default branch ends the box)
    h  half line (y += 7)             t  tab / small advance      c  colour / palette       e  end
    i  indent (number follows)        x  set x (number follows)   X Y  set x / y (number follows)
    u  (number follows)

`i x X Y u t c e` go through 0x800120f0, which parses a decimal number out of the string; the numbers are
copied verbatim here so the bytes stay identical. Everything that is not a valid escape, and every byte a
cp932 char cannot roundtrip through, is written as a `[NN]` / `[NNNN]` hex token instead, so decode -> encode
is byte-exact for any input (the extraction roundtrip test).

Escape letters that take a decimal argument: i x X Y u t c e (0x800120f0). `n f h` never do.
"""
import re

# escape byte -> (letter, takes_number)
ESCAPES = {
    0x6e: ("n", False), 0x66: ("f", False), 0x68: ("h", False),
    0x69: ("i", True), 0x78: ("x", True), 0x58: ("X", True), 0x59: ("Y", True),
    0x75: ("u", True), 0x74: ("t", True), 0x63: ("c", True), 0x65: ("e", True),
}
NUM = set("0123456789")
TOKEN = re.compile(r"\[([0-9A-Fa-f]{2}|[0-9A-Fa-f]{4})\]")


def _pair(data, i):
    """Length of the cp932 char at i (2), or 0 when the byte pair is not a valid SJIS char."""
    c = data[i]
    if not (0x81 <= c <= 0x9F or 0xE0 <= c <= 0xFC) or i + 1 >= len(data):
        return 0
    t = data[i + 1]
    if 0x40 <= t <= 0xFC and t != 0x7F:
        try:
            ch = data[i:i + 2].decode("cp932")
        except UnicodeDecodeError:
            return 0
        if len(ch) == 1 and ch.encode("cp932") == data[i:i + 2]:
            return 2
    return 0


def decode(data, nl=None):
    """bytes -> text (byte-exact inverse of encode). nl: a raw byte this format uses as a line break
    (MES strings break lines with 0x0d); it is written as \\n and encoded back to that byte."""
    out, i = [], 0
    while i < len(data):
        c = data[i]
        if nl is not None and c == nl:
            out.append("\\n")
            i += 1
            continue
        if c == 0x5C:                          # '\'
            if i + 1 < len(data) and data[i + 1] in ESCAPES:
                letter, takes = ESCAPES[data[i + 1]]
                i += 2
                if takes:
                    j = i
                    while j < len(data) and chr(data[j]) in NUM:
                        j += 1
                    out.append("\\" + letter + data[i:j].decode("ascii"))
                    i = j
                else:
                    out.append("\\" + letter)
                continue
            out.append("[5C]")
            i += 1
            continue
        n = _pair(data, i)
        if n:
            out.append(data[i:i + n].decode("cp932"))
            i += n
            continue
        if 0x20 <= c < 0x7F or c in (0x09, 0x0A, 0x0D):
            out.append("[%02X]" % c if c < 0x20 else chr(c))
            i += 1
            continue
        if 0xA1 <= c <= 0xDF:                  # half-width katakana
            out.append(bytes([c]).decode("cp932"))
            i += 1
            continue
        out.append("[%02X]" % c)
        i += 1
    return "".join(out)


def encode(text, nl=None):
    """text -> bytes (byte-exact inverse of decode); raises on a character cp932 cannot hold."""
    out, i = bytearray(), 0
    while i < len(text):
        m = TOKEN.match(text, i)
        if m:
            out += bytes.fromhex(m[1] if len(m[1]) % 2 == 0 else "0" + m[1])
            i = m.end()
            continue
        if nl is not None and text[i:i + 2] == "\\n":
            out.append(nl)
            i += 2
            continue
        if text[i] == "\\" and i + 1 < len(text) and text[i + 1] in {v[0] for v in ESCAPES.values()}:
            letter = text[i + 1]
            takes = next(v[1] for v in ESCAPES.values() if v[0] == letter)
            out.append(0x5C)
            out.append(next(k for k, v in ESCAPES.items() if v[0] == letter))
            i += 2
            if takes:
                j = i
                while j < len(text) and text[j] in NUM:
                    j += 1
                out += text[i:j].encode("ascii")
                i = j
            continue
        ch = text[i]
        try:
            b = ch.encode("cp932")
        except UnicodeEncodeError as e:
            raise ValueError(f"unencodable {ch!r} at {i} in {text!r}") from e
        if len(b) != 1 and decode(b) != ch:
            raise ValueError(f"non-roundtrip char {ch!r} at {i}")
        out += b
        i += 1
    return bytes(out)


def lines(text):
    """Number of drawn lines: the engine breaks on \\n and pages on \\f."""
    return text.count("\\n") + text.count("\\f") + (0 if text.endswith(("\\n", "\\f")) else 1)


def name_line(text):
    """True when this message is a speaker label: a bare short name closed by \\n, as the game stores them."""
    return text.endswith("\\n") and "「" not in text and "」" not in text and len(text) <= 16


if __name__ == "__main__":
    import sys
    for arg in sys.argv[1:] or ["\\n「ああ」\\f[09]カイエス"]:
        t = arg.encode().decode("unicode_escape")
        b = encode(t)
        print(repr(t), "->", b.hex(" "), "->", repr(decode(b)))
        assert decode(b) == t
