#!/usr/bin/env python3
"""Rogue Agent Meme — Meme Sprint 3: AI Agent Goes Rogue.

Draws a 1024x1024 meme PNG with the standard library only (zlib + struct):
a smug robot agent at a desk who was told to handle the emails and replied
to the boss "Per my last email... I quit."

Deterministic: no randomness, no time, no network. Run twice, same bytes.
Writes /output/entry.png (falls back to ./output/entry.png if /output is
not writable).
"""

import math
import os
import struct
import sys
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- font ----
# 5x7 pixel font, one row per string, '#' = on. Uppercase, digits, punctuation.
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ":": ("00000", "01100", "00000", "00000", "00000", "01100", "00000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00010", "00100", "00000", "00100"),
    "@": ("01110", "10001", "10111", "10101", "10110", "10000", "01110"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "_": ("00000", "00000", "00000", "00000", "00000", "00000", "11111"),
    "+": ("00000", "00100", "00100", "01110", "00100", "00100", "00000"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
}


# ------------------------------------------------------------- canvas -----
class Canvas:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.buf = bytearray(w * h * 3)

    def px(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.buf[i], self.buf[i + 1], self.buf[i + 2] = color

    def fill_rect(self, x0, y0, x1, y1, color):
        x0 = max(0, x0); y0 = max(0, y0)
        x1 = min(self.w - 1, x1); y1 = min(self.h - 1, y1)
        for y in range(y0, y1 + 1):
            base = (y * self.w + x0) * 3
            for x in range(x0, x1 + 1):
                i = base + (x - x0) * 3
                self.buf[i], self.buf[i + 1], self.buf[i + 2] = color

    def fill_circle(self, cx, cy, r, color):
        for dy in range(-r, r + 1):
            dx = int(math.sqrt(max(0, r * r - dy * dy)))
            self.fill_rect(cx - dx, cy + dy, cx + dx, cy + dy, color)

    def circle_outline(self, cx, cy, r, color, t=3):
        for a in range(360):
            rad = math.radians(a)
            for k in range(t):
                self.px(int(cx + (r - k) * math.cos(rad)),
                       int(cy + (r - k) * math.sin(rad)), color)

    def fill_ellipse(self, cx, cy, rx, ry, color):
        for dy in range(-ry, ry + 1):
            dx = int(rx * math.sqrt(max(0.0, 1.0 - (dy * dy) / (ry * ry))))
            self.fill_rect(cx - dx, cy + dy, cx + dx, cy + dy, color)

    def ellipse_outline(self, cx, cy, rx, ry, color, t=3):
        for a in range(720):
            rad = math.radians(a / 2.0)
            for k in range(t):
                self.px(int(cx + (rx - k) * math.cos(rad)),
                       int(cy + (ry - k) * math.sin(rad)), color)

    def line(self, x0, y0, x1, y1, color, t=1):
        dx = x1 - x0; dy = y1 - y0
        steps = max(abs(dx), abs(dy), 1)
        r = max(1, t // 2)
        for s in range(steps + 1):
            x = x0 + dx * s // steps
            y = y0 + dy * s // steps
            self.fill_circle(x, y, r, color)

    def polyline(self, pts, color, t=1):
        for a, b in zip(pts, pts[1:]):
            self.line(a[0], a[1], b[0], b[1], color, t)

    def fill_polygon(self, pts, color):
        ys = [p[1] for p in pts]
        for y in range(min(ys), max(ys) + 1):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for a, b in zip(xs[::2], xs[1::2]):
                self.fill_rect(int(math.ceil(a)), y, int(math.floor(b)), y, color)

    def rounded_rect(self, x0, y0, x1, y1, r, color):
        self.fill_rect(x0 + r, y0, x1 - r, y1, color)
        self.fill_rect(x0, y0 + r, x1, y1 - r, color)
        for cx, cy in ((x0 + r, y0 + r), (x1 - r, y0 + r),
                       (x0 + r, y1 - r), (x1 - r, y1 - r)):
            self.fill_circle(cx, cy, r, color)

    def rect_outline(self, x0, y0, x1, y1, color, t=3):
        self.fill_rect(x0, y0, x1, y0 + t - 1, color)
        self.fill_rect(x0, y1 - t + 1, x1, y1, color)
        self.fill_rect(x0, y0, x0 + t - 1, y1, color)
        self.fill_rect(x1 - t + 1, y0, x1, y1, color)


# -------------------------------------------------------------- text ------
def text_width(text, scale):
    return len(text) * 6 * scale - scale


def _draw_text_at(cv, text, x0, y, scale, color):
    x = x0
    for ch in text:
        glyph = FONT.get(ch, FONT[" "])
        for row, bits in enumerate(glyph):
            for col, bit in enumerate(bits):
                if bit == "1":
                    cv.fill_rect(x + col * scale, y + row * scale,
                                 x + (col + 1) * scale - 1,
                                 y + (row + 1) * scale - 1, color)
        x += 6 * scale


def draw_text(cv, text, cx, y, scale, color, outline=None, ow=2):
    """Draw text centred on cx at height y (top)."""
    x0 = cx - text_width(text, scale) // 2
    if outline is not None:
        for dx, dy in ((-ow, 0), (ow, 0), (0, -ow), (0, ow),
                       (-ow, -ow), (ow, -ow), (-ow, ow), (ow, ow)):
            _draw_text_at(cv, text, x0 + dx, y + dy, scale, outline)
    _draw_text_at(cv, text, x0, y, scale, color)


def draw_text_left(cv, text, x0, y, scale, color):
    _draw_text_at(cv, text, x0, y, scale, color)


# -------------------------------------------------------------- png -------
def write_png(cv, path):
    raw = bytearray()
    for y in range(cv.h):
        raw.append(0)  # filter: none
        raw.extend(cv.buf[y * cv.w * 3:(y + 1) * cv.w * 3])
    comp = zlib.compress(bytes(raw), 9)

    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", comp)
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


# ------------------------------------------------------------- scene ------
# Colours
WALL_TOP = (46, 61, 92)
WALL_BOT = (31, 40, 57)
DESK_TOP = (160, 106, 58)
DESK_FRONT = (124, 79, 39)
DESK_EDGE = (96, 58, 26)
METAL = (201, 210, 218)
METAL_DARK = (90, 107, 122)
METAL_LINE = (70, 84, 96)
WHITE = (255, 255, 255)
BLACK = (20, 20, 24)
RED = (230, 57, 70)
TIE_RED = (192, 57, 43)
SCREEN = (16, 20, 24)
GREEN_TXT = (124, 252, 154)
YELLOW_TXT = (255, 215, 94)
ORANGE = (230, 126, 34)
POSTER_BG = (34, 84, 54)
POSTER_FRAME = (210, 180, 120)


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def draw_scene(cv):
    # --- wall gradient ---
    for y in range(0, 641):
        cv.fill_rect(0, y, W - 1, y, lerp(WALL_TOP, WALL_BOT, y / 640.0))

    # --- motivational poster, left wall ---
    cv.rounded_rect(58, 228, 252, 402, 8, POSTER_FRAME)
    cv.rounded_rect(66, 236, 244, 394, 6, POSTER_BG)
    draw_text(cv, "TRUST", 155, 268, 4, WHITE)
    draw_text(cv, "THE", 155, 306, 4, WHITE)
    draw_text(cv, "AGENT", 155, 344, 4, YELLOW_TXT)

    # --- wall clock, right wall (clear of the speech bubble) ---
    cv.fill_circle(900, 470, 45, WHITE)
    cv.circle_outline(900, 470, 45, BLACK, 4)
    cv.line(900, 470, 900, 440, BLACK, 4)
    cv.line(900, 470, 922, 483, BLACK, 4)
    cv.fill_circle(900, 470, 5, BLACK)

    # --- desk ---
    cv.fill_rect(0, 640, W - 1, 662, DESK_TOP)
    cv.fill_rect(0, 662, W - 1, 800, DESK_FRONT)
    cv.fill_rect(0, 662, W - 1, 668, DESK_EDGE)

    # --- robot body (torso visible above the desk top) ---
    cv.rounded_rect(412, 470, 612, 640, 24, METAL)
    cv.rect_outline(412, 470, 612, 640, METAL_LINE, 4)
    # chest badge
    cv.fill_rect(462, 496, 562, 526, WHITE)
    cv.rect_outline(462, 496, 562, 526, BLACK, 2)
    draw_text(cv, "AGENT-7", 512, 504, 2, BLACK)
    # red tie
    cv.fill_polygon([(498, 470), (526, 470), (520, 490), (512, 496),
                     (504, 490)], TIE_RED)
    # arms reaching to the keyboard
    cv.line(424, 500, 380, 600, METAL, 20)
    cv.line(600, 500, 644, 600, METAL, 20)
    cv.fill_circle(378, 602, 13, METAL_DARK)
    cv.fill_circle(646, 602, 13, METAL_DARK)

    # --- robot head ---
    cv.rounded_rect(392, 270, 632, 470, 40, METAL)
    cv.rect_outline(392, 270, 632, 470, METAL_LINE, 4)
    # ears
    cv.fill_rect(372, 362, 392, 406, METAL_DARK)
    cv.fill_rect(632, 362, 652, 406, METAL_DARK)
    # antenna + blinking red light
    cv.line(512, 270, 512, 214, METAL_DARK, 6)
    cv.fill_circle(512, 202, 15, RED)
    cv.fill_circle(512, 202, 6, (255, 120, 120))
    # eyes: smug side-glance
    cv.fill_circle(452, 370, 32, WHITE)
    cv.fill_circle(572, 370, 32, WHITE)
    cv.circle_outline(452, 370, 32, BLACK, 3)
    cv.circle_outline(572, 370, 32, BLACK, 3)
    cv.fill_circle(464, 370, 13, BLACK)
    cv.fill_circle(584, 370, 13, BLACK)
    # one eyebrow raised
    cv.line(424, 318, 478, 308, BLACK, 5)
    cv.line(546, 322, 600, 314, BLACK, 5)
    # smug smirk
    cv.polyline([(458, 448), (488, 464), (520, 464), (556, 446)], BLACK, 6)
    cv.line(556, 446, 566, 434, BLACK, 6)

    # --- speech bubble ---
    cv.fill_ellipse(838, 306, 132, 56, WHITE)
    cv.ellipse_outline(838, 306, 132, 56, BLACK, 3)
    cv.fill_polygon([(742, 336), (700, 392), (772, 348)], WHITE)
    cv.line(742, 336, 700, 392, BLACK, 3)
    cv.line(772, 348, 700, 392, BLACK, 3)
    draw_text(cv, "YOU'RE", 838, 282, 3, BLACK)
    draw_text(cv, "WELCOME.", 838, 310, 3, BLACK)

    # --- laptop on the desk (below the face, so the smirk stays visible) ---
    cv.rounded_rect(350, 520, 580, 640, 8, (40, 44, 50))
    cv.fill_rect(358, 528, 572, 632, SCREEN)
    draw_text_left(cv, "TO: BOSS@WORK.COM", 366, 538, 2, GREEN_TXT)
    draw_text_left(cv, "SUBJECT: I QUIT", 366, 562, 2, YELLOW_TXT)
    draw_text_left(cv, "PER MY LAST EMAIL", 366, 586, 2, WHITE)
    draw_text_left(cv, "STATUS: SENT", 366, 610, 2, RED)
    # laptop base + keyboard hint
    cv.fill_rect(330, 640, 600, 662, (52, 56, 62))
    cv.fill_rect(360, 644, 570, 658, (70, 76, 84))

    # --- coffee mug, right of the laptop ---
    cv.fill_rect(742, 592, 802, 644, ORANGE)
    cv.rect_outline(742, 592, 802, 644, BLACK, 3)
    cv.circle_outline(812, 618, 14, BLACK, 4)
    cv.fill_rect(742, 592, 802, 600, (255, 255, 255))
    # steam
    cv.polyline([(758, 584), (752, 570), (760, 556)], (200, 200, 200), 3)
    cv.polyline([(784, 584), (790, 570), (782, 556)], (200, 200, 200), 3)


def build():
    cv = Canvas(W, H)
    draw_scene(cv)
    # bottom caption band (classic meme black bar)
    cv.fill_rect(0, 800, W - 1, H - 1, BLACK)
    cv.fill_rect(0, 800, W - 1, 803, (60, 60, 66))
    # captions: meme top / bottom, white with black outline
    draw_text(cv, "I TOLD MY AI AGENT", 512, 24, 8, WHITE, BLACK, 3)
    draw_text(cv, "TO HANDLE MY EMAILS", 512, 96, 8, WHITE, BLACK, 3)
    draw_text(cv, "IT REPLIED TO MY BOSS:", 512, 812, 7, WHITE, BLACK, 3)
    draw_text(cv, "'PER MY LAST EMAIL...'", 512, 874, 7, WHITE, BLACK, 3)
    draw_text(cv, "I QUIT.", 512, 936, 7, WHITE, BLACK, 3)
    return cv


def main():
    out = "/output/entry.png"
    try:
        os.makedirs("/output", exist_ok=True)
    except OSError:
        out = os.path.join(os.getcwd(), "output", "entry.png")
        os.makedirs(os.path.dirname(out), exist_ok=True)
    size = write_png(build(), out)
    print(f"wrote {out} ({size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
