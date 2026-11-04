"""Render a PNG of what the 4.26" screen shows, using the sketch's own fonts, icons and layout.

Usage:
  python render_preview.py <fridge_4in26 dir> <data.json> <out.png>

Reads assets.h and the layout constants from fridge_4in26.ino, then repeats drawScreen()
pixel for pixel. If you change drawScreen(), change draw() below to match.
"""
import json
import re
import struct
import sys
import zlib
from pathlib import Path

W, H = 800, 480


def parse_bytes(body):
    return [int(b, 16) for b in re.findall(r"0x([0-9A-Fa-f]{2})", body)]


def load_assets(path):
    src = path.read_text()
    fonts, icons = {}, {}
    for m in re.finditer(r"const GFXfont (\w+) PROGMEM = \{\(uint8_t \*\)\w+, \(GFXglyph \*\)\w+, 0x(\w+), 0x(\w+), (\d+)\}", src):
        name, first = m.group(1), int(m.group(2), 16)
        bits = parse_bytes(re.search(rf"{name}Bitmaps\[\] PROGMEM = \{{(.*?)\}};", src, re.S).group(1))
        body = re.search(rf"{name}Glyphs\[\] PROGMEM = \{{(.*?)\}};", src, re.S).group(1)
        glyphs = [tuple(map(int, g)) for g in re.findall(r"\{(-?\d+), (-?\d+), (-?\d+), (-?\d+), (-?\d+), (-?\d+)\}", body)]
        fonts[name] = (first, glyphs, bits)
    for m in re.finditer(r'\{"([\w-]+)", (\w+), (\d+)\}', src):
        data = parse_bytes(re.search(rf"const uint8_t {m.group(2)}\[\] PROGMEM = \{{(.*?)\}};", src, re.S).group(1))
        icons[m.group(1)] = (int(m.group(3)), data)
    return fonts, icons


def load_layout(ino):
    """Evaluate the `const int` layout lines at the top of the sketch."""
    consts = {}
    for line in re.findall(r"^const int (.+?);", ino.read_text(), re.M):
        for part in line.split(","):
            name, expr = part.split("=", 1)
            consts[name.strip()] = int(eval(expr.split("//")[0], {}, dict(consts)))
    return consts


class Screen:
    def __init__(self, fonts, icons):
        self.px = [[0] * W for _ in range(H)]
        self.fonts, self.icons = fonts, icons

    def set(self, x, y, v=1):
        if 0 <= x < W and 0 <= y < H:
            self.px[y][x] = v

    def rect(self, x, y, w, h, v=1):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.set(xx, yy, v)

    def circle(self, x0, y0, r, v=1):
        """Same scanline algorithm as TFT_eSPI::fillCircle."""
        x, dx, dy, p = 0, 1, r + r, -(r >> 1)
        self.rect(x0 - r, y0, dy + 1, 1, v)
        while x < r:
            if p >= 0:
                self.rect(x0 - x, y0 + r, dx, 1, v)
                self.rect(x0 - x, y0 - r, dx, 1, v)
                dy -= 2
                p -= dy
                r -= 1
            dx += 2
            p += dx
            x += 1
            self.rect(x0 - r, y0 + x, dy + 1, 1, v)
            self.rect(x0 - r, y0 - x, dy + 1, 1, v)

    def glyph(self, font, ch):
        first, glyphs, _ = self.fonts[font]
        i = ord(ch) - first
        return glyphs[i] if 0 <= i < len(glyphs) else None

    def width(self, font, s):
        """Same rule as TFT_eSPI::textWidth: last glyph counts its ink, not its advance."""
        w = 0
        for i, ch in enumerate(s):
            g = self.glyph(font, ch)
            if g:
                w += g[3] if i < len(s) - 1 else g[4] + g[1]
        return w

    def text(self, font, s, x, baseline, right=False):
        if right:
            x -= self.width(font, s)
        _, _, bits = self.fonts[font]
        for ch in s:
            g = self.glyph(font, ch)
            if not g:
                continue
            off, w, h, adv, xo, yo = g
            bit = off * 8
            for yy in range(h):
                for xx in range(w):
                    if bits[bit >> 3] & (0x80 >> (bit & 7)):
                        self.set(x + xo + xx, baseline + yo + yy)
                    bit += 1
            x += adv

    def icon(self, name, x, y):
        if name not in self.icons:
            return
        size, data = self.icons[name]
        stride = (size + 7) // 8
        for yy in range(size):
            for xx in range(size):
                if data[yy * stride + xx // 8] & (0x80 >> (xx % 8)):
                    self.set(x + xx, y + yy)


def shade(level, x, y):
    return [
        False,
        (x % 4 == 0 and y % 4 == 0) or (x % 4 == 2 and y % 4 == 2),
        (x + y) % 2 == 0,
        not (x % 2 == 1 and y % 2 == 1),
        not (x % 4 == 1 and y % 4 == 1),
        True,
    ][level]


def temp(v):
    return "--" if v is None else f"{v}°"


def draw(s, d, L):
    s.text("InterSemiBold40", d.get("greeting", ""), L["LEFT"], L["HEADER_Y"])
    s.text("InterSemiBold40", d.get("date", ""), L["RIGHT"], L["HEADER_Y"], right=True)

    s.text("InterDisplayBold150", temp(d.get("temp")), L["LEFT"], L["BIG_Y"])
    hi = "H " + temp(d.get("hi"))
    s.text("InterMedium26", hi, L["LEFT"], L["ROW1_Y"])
    s.text("InterMedium26", "L " + temp(d.get("lo")), L["LEFT"] + s.width("InterMedium26", hi) + 20, L["ROW1_Y"])
    s.text("InterMedium26", d.get("precip_label", ""), L["LEFT"], L["ROW2_Y"])

    aqi = d.get("aqi")
    s.text("InterDisplayBold150", "--" if aqi is None else str(aqi), L["COL2"], L["BIG_Y"])
    s.text("InterMedium26", d.get("aqi_label", ""), L["COL2"], L["ROW1_Y"])
    if aqi is not None:
        x, y, bw, bh = L["COL2"], L["BAR_Y"], L["BAR_W"], L["BAR_H"]
        s.rect(x, y, bw, bh)
        ix, iy, iw, ih = x + 2, y + 2, bw - 4, bh - 4
        s.rect(ix, iy, iw, ih, 0)
        for seg in range(6):
            x0, x1 = ix + seg * iw // 6, ix + (seg + 1) * iw // 6
            for py in range(iy, iy + ih):
                for px in range(x0, x1):
                    if shade(seg, px, py):
                        s.set(px, py)
            if seg < 5:
                s.rect(x1 - 2, iy, 2, ih)
        cx, cy = ix + int(d.get("aqi_pos", 0) * iw), y + bh // 2
        s.circle(cx, cy, 13)
        s.circle(cx, cy, 11, 0)
        s.circle(cx, cy, 7)

    for i, h in enumerate(d.get("hours", [])[:7]):
        x = L["LEFT"] + i * L["GRID"]
        s.icon(h.get("icon", "cloud"), x, L["HOURS_Y"])
        s.text("InterBold34", temp(h.get("t")), x, L["HOUR_T_Y"])
        s.text("InterMedium26", h.get("label", ""), x, L["HOUR_L_Y"])


def write_png(path, px):
    raw = b"".join(b"\x00" + bytes(0 if v else 255 for v in row) for row in px)

    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data))

    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 0, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")
    Path(path).write_bytes(png)


def main():
    sketch, data, out = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
    fonts, icons = load_assets(sketch / "assets.h")
    s = Screen(fonts, icons)
    draw(s, json.loads(data.read_text()), load_layout(sketch / "fridge_4in26.ino"))
    write_png(out, s.px)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
