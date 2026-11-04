"""Convert Inter fonts and Phosphor icons into 1-bit C arrays for the e-ink screen.

Usage:
  python make_assets.py <inter ttf dir> <Phosphor.ttf> <out assets.h> [preview.png]

<inter ttf dir> is extras/ttf from the Inter release zip (github.com/rsms/inter, v4.1);
Phosphor.ttf is src/regular/ in the npm package @phosphor-icons/web.

Needs: pip install freetype-py
Fonts become Adafruit GFX fonts (what Seeed_GFX's setFreeFont() takes); icons become
row-padded bitmaps for drawBitmap(). Letter spacing from the design is baked into each
glyph's advance width.
"""
import struct
import sys
import zlib
from pathlib import Path

import freetype

THRESHOLD = 128  # anti-aliased coverage at or above this becomes a black pixel

ASCII = "".join(chr(c) for c in range(0x20, 0x7F))

# (C name, file, pixel size, characters, extra px per glyph = CSS letter-spacing,
#  {stored code: source code} to place a glyph in a different slot)
FONTS = [
    ("InterDisplayBold150", "InterDisplay-Bold.ttf", 150, "-0123456789°", -6, {}),
    ("InterSemiBold40", "Inter-SemiBold.ttf", 40, ASCII, -1, {}),
    ("InterBold34", "Inter-Bold.ttf", 34, "-0123456789°", -1, {}),
    ("InterMedium26", "Inter-Medium.ttf", 26, ASCII + "°·", 0, {}),
]

# (name used by the server, Phosphor codepoint, pixel size)
ICONS = [
    ("sun", 0xE472, 40),
    ("moon-stars", 0xE58E, 40),
    ("cloud-sun", 0xE540, 40),
    ("cloud-moon", 0xE53E, 40),
    ("cloud", 0xE1AA, 40),
    ("cloud-fog", 0xE53C, 40),
    ("cloud-rain", 0xE1B4, 40),
    ("cloud-snow", 0xE1B8, 40),
    ("cloud-lightning", 0xE1B2, 40),
    ("drop", 0xE210, 18),
    ("snowflake", 0xE5AA, 18),
]


def render(face, char_code, hinted=False):
    """Return (rows of 0/1, left, top, advance) for one glyph.

    hinted=True snaps strokes to whole pixels (cleaner for small text);
    otherwise anti-aliased coverage is thresholded (truer shapes for large text).
    """
    if hinted:
        face.load_char(char_code, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_TARGET_MONO)
    else:
        face.load_char(char_code, freetype.FT_LOAD_RENDER)
    g = face.glyph
    bm = g.bitmap
    if hinted:
        rows = [[(bm.buffer[y * bm.pitch + x // 8] >> (7 - x % 8)) & 1 for x in range(bm.width)]
                for y in range(bm.rows)]
    else:
        rows = [[1 if bm.buffer[y * bm.pitch + x] >= THRESHOLD else 0 for x in range(bm.width)]
                for y in range(bm.rows)]
    return rows, g.bitmap_left, g.bitmap_top, round(g.advance.x / 64)


def trim(rows, left, top):
    """Drop empty rows/columns so the stored bitmap is as small as possible."""
    if not rows or not any(any(r) for r in rows):
        return [], left, top
    ys = [y for y, r in enumerate(rows) if any(r)]
    xs = [x for x in range(len(rows[0])) if any(r[x] for r in rows)]
    y0, y1, x0, x1 = ys[0], ys[-1], xs[0], xs[-1]
    return [r[x0:x1 + 1] for r in rows[y0:y1 + 1]], left + x0, top - y0


def pack_bits(rows, pad_rows):
    """MSB-first bit packing. GFX fonts pack continuously; drawBitmap pads each row to a byte."""
    out, acc, n = [], 0, 0
    for r in rows:
        for bit in r:
            acc = (acc << 1) | bit
            n += 1
            if n == 8:
                out.append(acc)
                acc, n = 0, 0
        if pad_rows and n:
            out.append(acc << (8 - n))
            acc, n = 0, 0
    if n:
        out.append(acc << (8 - n))
    return out


def c_bytes(data):
    lines = []
    for i in range(0, len(data), 16):
        lines.append("  " + ", ".join(f"0x{b:02X}" for b in data[i:i + 16]) + ",")
    return "\n".join(lines)


def make_font(name, path, px, chars, tracking, remap, sheet):
    face = freetype.Face(str(path))
    face.set_pixel_sizes(0, px)
    codes = sorted({ord(c) for c in chars})
    first, last = codes[0], codes[-1]
    bitmap, glyphs = [], []
    for code in range(first, last + 1):
        if code not in codes:
            glyphs.append((len(bitmap), 0, 0, 0, 0, 0))  # unused slot in the range
            continue
        rows, left, top, adv = render(face, remap.get(code, code), hinted=px <= 22)
        rows, left, top = trim(rows, left, top)
        h = len(rows)
        w = len(rows[0]) if h else 0
        assert w < 256 and h < 256 and -128 <= left < 128 and -128 <= -top < 128, (name, chr(code))
        glyphs.append((len(bitmap), w, h, max(0, adv + tracking), left, -top))
        bitmap += pack_bits(rows, pad_rows=False)
        if code != 0x20:
            sheet.append((rows, f"{name} {chr(code)}"))
    y_adv = round(face.size.height / 64)

    src = [f"const uint8_t {name}Bitmaps[] PROGMEM = {{\n{c_bytes(bitmap) or '  0x00,'}\n}};\n"]
    src.append(f"const GFXglyph {name}Glyphs[] PROGMEM = {{")
    for off, w, h, adv, x, y in glyphs:
        src.append(f"  {{{off}, {w}, {h}, {adv}, {x}, {y}}},")
    src.append("};\n")
    src.append(f"const GFXfont {name} PROGMEM = {{(uint8_t *){name}Bitmaps, (GFXglyph *){name}Glyphs, "
               f"0x{first:X}, 0x{last:X}, {y_adv}}};\n")
    return "\n".join(src), len(bitmap) + 7 * len(glyphs)


def make_icon(face, name, code, px, sheet):
    face.set_pixel_sizes(0, px)
    rows, _, _, _ = render(face, code)
    rows, _, _ = trim(rows, 0, 0)
    h, w = len(rows), len(rows[0])
    # Center the glyph in a px-by-px box, like the CSS icon box.
    box = [[0] * px for _ in range(px)]
    oy, ox = (px - h) // 2, (px - w) // 2
    for y in range(h):
        for x in range(w):
            if 0 <= y + oy < px and 0 <= x + ox < px:
                box[y + oy][x + ox] = rows[y][x]
    sheet.append((box, name))
    cname = "icon_" + name.replace("-", "_")
    data = pack_bits(box, pad_rows=True)
    return cname, f"const uint8_t {cname}[] PROGMEM = {{\n{c_bytes(data)}\n}};\n", len(data)


def write_png(path, sheet, scale=2, pad=6):
    """Write all glyphs and icons side by side so they can be checked by eye."""
    width = 1200
    x = y = pad
    line_h = 0
    placed = []
    for rows, _ in sheet:
        h = len(rows)
        w = len(rows[0]) if h else 0
        if x + w + pad > width // scale:
            x, y, line_h = pad, y + line_h + pad, 0
        placed.append((rows, x, y))
        x += w + pad
        line_h = max(line_h, h)
    height = (y + line_h + pad) * scale
    img = [[255] * width for _ in range(height)]
    for rows, px, py in placed:
        for yy, r in enumerate(rows):
            for xx, bit in enumerate(r):
                if bit:
                    for sy in range(scale):
                        for sx in range(scale):
                            img[(py + yy) * scale + sy][(px + xx) * scale + sx] = 0
    raw = b"".join(b"\x00" + bytes(r) for r in img)

    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data))

    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 0, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")
    Path(path).write_bytes(png)


def main():
    font_dir, phosphor, out = map(Path, sys.argv[1:4])
    preview = sys.argv[4] if len(sys.argv) > 4 else None
    sheet = []
    parts = ["// Generated by tools/make_assets.py. Do not edit by hand.",
             "// Fonts: Inter (SIL Open Font License). Icons: Phosphor (MIT).",
             "#pragma once", "#include <Arduino.h>", '#include "TFT_eSPI.h"', ""]
    total = 0
    for name, file, px, chars, tracking, remap in FONTS:
        src, size = make_font(name, font_dir / file, px, chars, tracking, remap, sheet)
        parts.append(src)
        total += size

    face = freetype.Face(str(phosphor))
    table = []
    for name, cp, px in ICONS:
        cname, src, size = make_icon(face, name, cp, px, sheet)
        parts.append(src)
        table.append(f'  {{"{name}", {cname}, {px}}},')
        total += size

    parts.append("struct Icon { const char *name; const uint8_t *bits; uint8_t size; };\n")
    parts.append("const Icon ICONS[] = {\n" + "\n".join(table) + "\n};\n")
    parts.append(f"const int ICON_COUNT = {len(ICONS)};")
    Path(out).write_text("\n".join(parts) + "\n")
    print(f"wrote {out}: about {total / 1024:.1f} KB of font and icon data")
    if preview:
        write_png(preview, sheet)
        print(f"wrote {preview}")


if __name__ == "__main__":
    main()
