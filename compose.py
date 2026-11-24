#!/usr/bin/env python3
"""compose.py — builds image.jpg for news-image-20261123.

A 38-story newspaper front page for Monday 23 November 2026, drawn fresh
with PIL (local build only; main.py is stdlib-only and only copies the
committed image). Flat vector illustration only: no photos, no recognisable
faces, no hands. Every word is renderer-typeset.

Typography (per ~/workspace/makefun/typography-study.md): Playfair Display
Black/Bold for the date and lead headlines; Archivo Narrow 600/700 for
cards, labels and ALL figure strips (tabular digits, x-height 0.526);
Newsreader SemiBold for decks and the DATE CHECK. Barlow SC is retired.
Size floors honoured where the 1024 canvas allows: lead headlines 44px,
card headlines 27px, figure strips 34px figures / 26px labels, DATE CHECK
and sources 22px. Two documented deviations: (1) the date is set at the
largest size that fits full-width in Playfair Black (76px — 110px would
need 1384px; measured); it is still the largest text on the page, as in
the winning entries. (2) Region-bar labels and UTC times are secondary
labels below the strip floor — the winners' grammar puts them there, and
a 26px region label cannot fit a 142px segment.

Layout (1024x1024): navy masthead band -> huge serif date -> count strip
-> numbers strip -> region bar -> UTC strip -> 3 large lead panels ->
2 rows of 6 cards -> dotted world map + 23 briefs (3 columns) -> boxed
DATE CHECK -> sources line.
"""
import hashlib
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "fonts")

W, H = 1024, 1024
CREAM = (247, 243, 232)
PAPER = (250, 247, 238)
NAVY = (14, 30, 58)
NAVY2 = (20, 42, 78)
RED = (168, 32, 26)
RED2 = (196, 48, 36)
INK = (22, 22, 22)
GREY = (90, 88, 80)
LGREY = (120, 118, 108)
RULE = (180, 172, 150)
TAN = (188, 166, 122)
MAPSEA = (214, 206, 182)
MAPLAND = (232, 222, 196)

REGION_COLORS = {
    "NORTH AMERICA": (46, 95, 163),
    "EUROPE": (31, 122, 109),
    "ASIA": (165, 95, 18),
    "MIDDLE EAST": (169, 50, 38),
    "AFRICA": (138, 109, 59),
    "SOUTH AMERICA": (108, 74, 138),
    "OCEANIA": (90, 90, 90),
}

TAG_COLORS = {
    "CONFIRMED": (31, 122, 60),
    "OFFICIAL": (46, 95, 163),
    "REPORTED": (46, 95, 163),
    "CLAIM": (150, 95, 5),
}


def font(name, size):
    return ImageFont.truetype(os.path.join(FONTS, name), size)


F_DATE = lambda s: font("PlayfairDisplay-Black.ttf", s)
F_HEAD = lambda s: font("PlayfairDisplay-Bold.ttf", s)
F_DECK = lambda s: font("Newsreader-Regular.ttf", s)
F_DECKB = lambda s: font("Newsreader-SemiBold.ttf", s)
F_AN = lambda s: font("archivo-narrow-v35-latin-700.ttf", s)
F_ANM = lambda s: font("archivo-narrow-v35-latin-600.ttf", s)

TRUNCATED = []


def text_w(draw, s, f):
    return draw.textlength(s, font=f)


def fit_lines(draw, text, f, max_w, max_lines, tag=""):
    """Greedy word-wrap; records a warning (never silently drops text)."""
    words = text.split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if draw.textlength(trial, font=f) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    if len(lines) > max_lines:
        TRUNCATED.append((tag, text, len(lines), max_lines))
        lines = lines[:max_lines]
    return lines


def draw_lines(draw, lines, x, y, f, fill, leading):
    for i, ln in enumerate(lines):
        draw.text((x, y + i * leading), ln, font=f, fill=fill)
    return y + len(lines) * leading


def center(draw, y, s, f, fill, cx=W // 2):
    w = draw.textlength(s, font=f)
    draw.text((cx - w / 2, y), s, font=f, fill=fill)
    return w


def chip(draw, x, y, s, f, fg, bg=None, pad_x=4, pad_y=2):
    w = draw.textlength(s, font=f) + 2 * pad_x
    h = f.size + 2 * pad_y
    if bg is not None:
        draw.rounded_rectangle([x, y, x + w, y + h], radius=2, fill=bg)
    draw.text((x + pad_x, y + pad_y - 1), s, font=f, fill=fg)
    return w


def tracked(draw, x, y, s, f, fill, tracking=0.06):
    """Draw all-caps text with letter tracking (em fraction per char)."""
    cx = x
    adv = f.size * tracking
    for ch in s:
        draw.text((cx, y), ch, font=f, fill=fill)
        cx += draw.textlength(ch, font=f) + adv
    return cx - x


# --- dotted world map -------------------------------------------------------
# Coarse land bitmap, 64 columns (lon -180..180) x 28 rows (lat 78..-58).
LAND = [
    "................................................................",
    "....XXXXXX......................................................",
    "...XXXXXXXXXX...........XXXXXXX..................................",
    "..XXXXXXXXXXXXXX.......XXXXXXXXX.........XXXXXXXX.................",
    "..XXXXXXXXXXXXXXXX....XXXXXXXXXX.......XXXXXXXXXXXXX.............",
    "...XXXXXXXXXXXXXXX.....XXXXXXXXX.......XXXXXXXXXXXXXXXX..........",
    "....XXXXXXXXXXXXX.......XXXXXXX.........XXXXXXXXXXXXXXXXXX.......",
    ".....XXXXXXXXXXX.........XXXXX..........XXXXXXXXXXXXXXXXX........",
    "......XXXXXXXXX...........XXX...........XXXXXXXXXXXXXXXX.........",
    ".......XXXXXXX.............X.............XXXXXXXXXXXXX...........",
    "........XXXXX.............................XXXXXXXXXX.............",
    ".........XXX...............................XXXXXXXX..............",
    "..........XX................................XXXXXX..............",
    "...........X.................................XXXX...............",
    "..............................................XX................",
    "..............................................XX................",
    ".............................................XXXX...............",
    "............................................XXXXXX..............",
    "...........................................XXXXXXXX.............",
    "............................................XXXXXX..............",
    ".............................................XXXX...............",
    "..............................................XX................",
    "................................................................",
    "................................................................",
    "................................................................",
    "................................................................",
    "................................................................",
    "................................................................",
]


def lonlat_to_xy(lon, lat, box):
    x0, y0, bw, bh = box
    x = x0 + (lon + 180.0) / 360.0 * bw
    y = y0 + (78.0 - lat) / 136.0 * bh
    return x, y


def draw_map(draw, box, pins):
    """pins: list of (num, lon, lat, dx, dy). Dark navy sea, tan land dots."""
    x0, y0, bw, bh = box
    draw.rectangle([x0, y0, x0 + bw, y0 + bh], fill=NAVY)
    cw, ch = bw / 64.0, bh / 28.0
    for r, row in enumerate(LAND):
        for c, ch_ in enumerate(row):
            if ch_ == "X":
                cx = x0 + c * cw + cw / 2
                cy = y0 + r * ch + ch / 2
                draw.ellipse([cx - 2.2, cy - 2.2, cx + 2.2, cy + 2.2],
                             fill=(216, 202, 164))
    ey = lonlat_to_xy(0, 0, box)[1]
    draw.line([x0, ey, x0 + bw, ey], fill=(90, 110, 150), width=1)
    for num, lon, lat, dx, dy in pins:
        px, py = lonlat_to_xy(lon, lat, box)
        px += dx
        py += dy
        draw.ellipse([px - 8, py - 8, px + 8, py + 8], fill=RED,
                     outline=(255, 255, 255), width=1)
        t = str(num)
        tw = draw.textlength(t, font=F_AN(9))
        draw.text((px - tw / 2, py - 6), t, font=F_AN(9), fill=(255, 255, 255))
    return box


# --- story data -------------------------------------------------------------
# Verified Mon 23 Nov 2026 (research: news23-analysis/research.md, >=2
# sources each). Field figures corrected where research proved otherwise:
# Nvidia +31.48% close (not +35% intraday); Kospi -3.3% close (not -5.8%
# as the day result); Bitcoin $61,327 close (not $63,000); Delta 1,600+
# DELAYED (202 cancelled, not 1,600+ cancelled); Sparta II under tow into
# St Petersburg (not still burning); Hormuz 3 tankers claimed (not 4);
# Riemann proof is Fri 20 / Sat 21 Nov -> DATE CHECK; EU 22nd sanctions
# are a PROPOSAL, not adopted; "sank" for the Merkury is Zelenskyy's CLAIM
# vs "heavily damaged" — print "capsized".
NUMBERS = [
    ("+31.5%", "NVIDIA"),
    ("$43.9bn", "ZSCALER"),
    ("153", "DRONES"),
    ("11", "DYMER"),
    ("24", "CIKANDE"),
    ("\u22123.3%", "KOSPI"),
]
REGIONS = [
    ("NORTH AMERICA", 11), ("EUROPE", 11), ("ASIA", 7),
    ("MIDDLE EAST", 5), ("AFRICA", 2), ("SOUTH AMERICA", 1), ("OCEANIA", 1),
]
TIMELINE = [
    ("02:40", "Vanuatu M6.5 quake"),
    ("07:00", "Brussels flights halted"),
    ("21:00", "S&P closes +4.7%"),
]

LEADS = [
    {
        "n": 1, "place": "SANTA CLARA, US", "beat": "MARKETS",
        "banner": "HUANG IS BACK",
        "head": "Nvidia brings Huang back",
        "deck": ("Board reinstates Jensen Huang as CEO, 11 days after he "
                 "quit. Shares close +31.5%."),
        "src": "Reuters \u00b7 AP", "tag": "CONFIRMED",
    },
    {
        "n": 2, "place": "BENGHAZI, LIBYA", "beat": "WAR AT SEA",
        "banner": "KYIV CLAIMS THE STRIKE",
        "head": "Kyiv claims corvette sunk",
        "deck": ("Zelenskyy: sea drones hit the corvette Merkury in "
                 "Benghazi; satellites show her capsized."),
        "src": "Reuters \u00b7 AP \u00b7 Al Jazeera", "tag": "CONFIRMED",
    },
    {
        "n": 3, "place": "ANTALYA, T\u00dcRKIYE", "beat": "CLIMATE",
        "banner": "NO FOSSIL FUELS",
        "head": "COP31 ends with no deal",
        "deck": ("Antalya talks close two days late, the first failed COP "
                 "since 2009. No fossil fuels in the text."),
        "src": "Reuters \u00b7 BBC", "tag": "CONFIRMED",
    },
]

# n, place, beat, banner, head (<=26 chars), deck (<=52 chars), src, tag
CARDS = [
    (4, "NEW YORK", "MARKETS", "REBOUND",
     "Wall Street roars back",
     "Wall St roars: S&P +4.7%, Nasdaq +6.5%.",
     "Reuters \u00b7 AP", "CONFIRMED"),
    (5, "AUSTIN", "TECH", "MEGA-DEAL",
     "CrowdStrike buys Zscaler",
     "All-stock; 1.135 shares a share; closes H2 FY2028.",
     "Reuters \u00b7 AP", "CONFIRMED"),
    (6, "STRASBOURG", "SANCTIONS", "PROPOSAL",
     "EU proposes sanctions",
     "Ban on ~60 banks, all off SWIFT; needs 27 votes.",
     "Reuters \u00b7 AFP", "OFFICIAL"),
    (7, "BRUSSELS", "NATO", "EMERGENCY",
     "NATO meets over Poland",
     "3 Kh-101s fell in Poland Friday; AWACS to deploy.",
     "Reuters \u00b7 AP", "CONFIRMED"),
    (8, "NEW DELHI", "AID", "NEPAL",
     "India gives Nepal aid",
     "$377m grant + $1.24bn credit for energy; 8 MoUs.",
     "Reuters \u00b7 ANI", "CONFIRMED"),
    (9, "BANTEN", "FIRE", "24 DEAD",
     "Cikande toll hits 24",
     "Fire Saturday night; 24 dead, ~30 still missing.",
     "Reuters \u00b7 AP", "CONFIRMED"),
    (10, "KYIV REGION", "WAR", "RESCUE",
     "Dymer toll climbs to 11",
     "Two survivors pulled out; 14 missing; toll 11.",
     "Reuters \u00b7 AP", "CONFIRMED"),
    (11, "SEOUL", "MARKETS", "ROUT",
     "Kospi dives in Asian rout",
     "\u22125.8% intraday, closes \u22123.3% at 4,708.",
     "Reuters \u00b7 Yonhap", "CONFIRMED"),
    (12, "HORMUZ", "WAR AT SEA", "CLAIM",
     "IRGC claims tankers hit",
     "IRGC claims 3 tankers hit mines; CENTCOM silent.",
     "Reuters \u00b7 AFP", "CLAIM"),
    (13, "ROSTOV", "ENERGY WAR", "HALTED",
     "Rostov refinery halts",
     "80+ drones; governor confirms halt.",
     "Reuters \u00b7 AP", "REPORTED"),
    (14, "SEOUL", "POLITICS", "NOMINEE",
     "First woman to lead NIS",
     "Kang Kum-sil nominated; hearings still to come.",
     "Yonhap \u00b7 Reuters", "OFFICIAL"),
    (15, "WASHINGTON", "POLITICS", "258 SEATS",
     "Democrats reach 258",
     "Hubbard beats Foxx by 330; she concedes.",
     "AP \u00b7 Reuters", "CONFIRMED"),
]

# n, region-word, text (kept short; 3-column briefs)
BRIEFS = [
    (16, "SKUBAL", "agrees $450M Mets deal"),
    (17, "TREASURY", "hits 30 Iran entities"),
    (18, "IRAN", "Trump leans to 2027 strikes"),
    (19, "KHARTOUM", "4 killed, UN hit"),
    (20, "LAHJ", "\u22656 killed in bus strike"),
    (21, "VANUATU", "M6.5 quake, 02:40 UTC"),
    (22, "BELGIUM", "strike grounds all flights"),
    (23, "ICJ", "14 nations back ruling"),
    (24, "HASINA", "arrest if she returns"),
    (25, "ALCARAZ", "wins first ATP Finals"),
    (26, "LIVERPOOL", "beats Man Utd 4\u20130"),
    (27, "SPARTA II", "towed into St Petersburg"),
    (28, "BRAZIL", "cleanup after supercell"),
    (29, "LISBON", "police clear Rossio camp"),
    (30, "SPACEX", "two states sue over Grok"),
    (31, "IRAN", "shows twin-missile launcher"),
    (32, "CREDIT", "Trump revives 10% cap"),
    (33, "MARKETS", "Bitcoin $61,327, gold $3,604"),
    (34, "TATA", "buys APL Apollo stake"),
    (35, "DENMARK", "expels Russian attach\u00e9"),
    (36, "WEST BANK", "settler arson near Ramallah"),
    (37, "DELTA", "delays 1,600+ flights"),
    (38, "GAZA", "\u22653 killed, incl. UNRWA aide"),
]

# num, lon, lat, dx, dy — pins for leads 1-3 + cards 4-15
PINS = [
    (1, -121.95, 37.35, 0, 0),       # Santa Clara
    (2, 20.07, 32.12, -16, 10),     # Benghazi
    (3, 30.71, 36.90, 2, 16),       # Antalya
    (4, -74.01, 40.71, 0, 0),       # New York
    (5, -97.74, 30.28, 0, 0),       # Austin
    (6, 7.75, 48.58, 2, -16),       # Strasbourg
    (7, 4.35, 50.85, -14, -12),     # Brussels
    (8, 77.21, 28.61, 10, -8),      # New Delhi
    (9, 106.15, -6.15, 0, 0),       # Cikande, Banten
    (10, 30.30, 50.78, -10, 12),    # Dymer
    (11, 126.98, 37.57, 0, 0),      # Seoul (Kospi)
    (12, 56.50, 26.60, 12, 8),      # Hormuz
    (13, 39.90, 47.77, 14, 2),      # Novoshakhtinsk
    (14, 126.98, 37.57, 16, 10),    # Seoul (NIS) — offset from pin 11
    (15, -77.04, 38.91, 16, -12),   # Washington DC
]

DATE_CHECK = (
    "DATE CHECK \u2014 Left out: Riemann (20 Nov) \u00b7 measles-free status "
    "(17 Nov) \u00b7 Cyrus wedding (21 Nov) \u00b7 FBI hack (20 Nov). Not yet: "
    "EU sanctions \u00b7 Iran strikes \u00b7 Shenzhen summit (26 Nov)."
)

SOURCES = ("SOURCES: REUTERS \u00b7 AP \u00b7 AFP \u00b7 BBC \u00b7 AL JAZEERA "
           "\u00b7 UN NEWS \u00b7 YONHAP \u00b7 ANI \u2014 MONDAY 23 NOVEMBER 2026")


# --- lead art (full scenes, flat vector, no faces) --------------------------
def lead_art(draw, idx, x0, y0, w, h):
    if idx == 0:
        # Nvidia: dark chip panel, candlesticks climbing, rising arrow.
        draw.rectangle([x0, y0, x0 + w, y0 + h], fill=(10, 26, 20))
        bars = [(0.06, 0.55, 0.62), (0.20, 0.48, 0.58), (0.34, 0.42, 0.52),
                (0.48, 0.34, 0.44), (0.62, 0.26, 0.38), (0.76, 0.14, 0.26)]
        for fx, ftop, fbot in bars:
            bx = x0 + fx * w
            col = (46, 180, 90)
            draw.rectangle([bx, y0 + ftop * h, bx + 12, y0 + fbot * h], fill=col)
            draw.line([bx + 6, y0 + ftop * h - 4, bx + 6, y0 + fbot * h + 4],
                      fill=col, width=2)
        pts = [(x0 + 0.05 * w, y0 + 0.62 * h), (x0 + 0.25 * w, y0 + 0.55 * h),
               (x0 + 0.45 * w, y0 + 0.44 * h), (x0 + 0.65 * w, y0 + 0.36 * h),
               (x0 + 0.88 * w, y0 + 0.18 * h)]
        draw.line(pts, fill=(120, 220, 150), width=3)
        draw.polygon([(x0 + 0.88 * w, y0 + 0.18 * h), (x0 + 0.88 * w - 12, y0 + 0.18 * h + 2),
                      (x0 + 0.88 * w - 2, y0 + 0.18 * h + 12)], fill=(120, 220, 150))
        draw.rectangle([x0 + 0.82 * w, y0 + 0.55 * h, x0 + 0.96 * w, y0 + 0.85 * h],
                       outline=(120, 220, 150), width=2)
        draw.rectangle([x0 + 0.85 * w, y0 + 0.62 * h, x0 + 0.93 * w, y0 + 0.78 * h],
                       fill=(120, 220, 150))
    elif idx == 1:
        # Benghazi: night harbour, capsized corvette, drone path, moon.
        draw.rectangle([x0, y0, x0 + w, y0 + h], fill=(24, 58, 96))
        draw.ellipse([x0 + 0.82 * w, y0 + 0.06 * h, x0 + 0.92 * w, y0 + 0.28 * h],
                     fill=(240, 230, 190))
        draw.rectangle([x0, y0 + 0.62 * h, x0 + w, y0 + h], fill=(30, 72, 116))
        # harbour silhouette
        draw.rectangle([x0, y0 + 0.52 * h, x0 + 0.18 * w, y0 + 0.62 * h], fill=(8, 20, 40))
        draw.rectangle([x0 + 0.20 * w, y0 + 0.46 * h, x0 + 0.26 * w, y0 + 0.62 * h],
                       fill=(8, 20, 40))
        # capsized corvette: dark hull, red keel up, tilted
        draw.polygon([(x0 + 0.38 * w, y0 + 0.66 * h), (x0 + 0.72 * w, y0 + 0.60 * h),
                      (x0 + 0.74 * w, y0 + 0.68 * h), (x0 + 0.40 * w, y0 + 0.74 * h)],
                     fill=(150, 155, 165))
        draw.polygon([(x0 + 0.40 * w, y0 + 0.64 * h), (x0 + 0.70 * w, y0 + 0.58 * h),
                      (x0 + 0.71 * w, y0 + 0.62 * h), (x0 + 0.41 * w, y0 + 0.68 * h)],
                     fill=(168, 32, 26))
        # drone dotted path
        for i in range(7):
            fx = 0.30 + i * 0.07
            fy = 0.30 - i * 0.015
            draw.ellipse([x0 + fx * w - 2, y0 + fy * h - 2, x0 + fx * w + 2, y0 + fy * h + 2],
                         fill=(240, 210, 120))
        draw.ellipse([x0 + 0.76 * w - 3, y0 + 0.20 * h - 3, x0 + 0.76 * w + 3, y0 + 0.20 * h + 3],
                     fill=(240, 210, 120))
    else:
        # COP31: dawn bands, skyline, sun, dome, table with delegates.
        for i, col in enumerate([(250, 200, 140), (244, 170, 120), (232, 140, 110),
                                 (220, 120, 100)]):
            draw.rectangle([x0, y0 + i * h / 4, x0 + w, y0 + (i + 1) * h / 4], fill=col)
        draw.ellipse([x0 + 0.44 * w, y0 + 0.05 * h, x0 + 0.56 * w, y0 + 0.30 * h],
                     fill=(255, 240, 200))
        draw.rectangle([x0, y0 + 0.42 * h, x0 + w, y0 + 0.50 * h], fill=(90, 60, 70))
        draw.polygon([(x0 + 0.10 * w, y0 + 0.50 * h), (x0 + 0.16 * w, y0 + 0.34 * h),
                      (x0 + 0.22 * w, y0 + 0.50 * h)], fill=(90, 60, 70))
        draw.ellipse([x0 + 0.70 * w, y0 + 0.30 * h, x0 + 0.84 * w, y0 + 0.50 * h],
                     fill=(120, 80, 90))
        # table + 5 delegates (backs, distinct colours) + plain document
        draw.rectangle([x0 + 0.08 * w, y0 + 0.72 * h, x0 + 0.92 * w, y0 + 0.80 * h],
                       fill=(70, 50, 55))
        for i, col in enumerate([(31, 122, 109), (169, 50, 38), (201, 123, 30),
                                 (46, 95, 163), (108, 74, 138)]):
            fx = 0.14 + i * 0.17
            draw.ellipse([x0 + fx * w, y0 + 0.54 * h, x0 + (fx + 0.09) * w, y0 + 0.72 * h],
                         fill=col)
        draw.rectangle([x0 + 0.42 * w, y0 + 0.60 * h, x0 + 0.58 * w, y0 + 0.71 * h],
                       fill=(250, 247, 238), outline=(120, 118, 108))


# --- card art (30px mini-scene strips) --------------------------------------
def card_art(draw, n, x0, y0, w, h):
    if n == 4:  # Wall Street: rising candles on dark green
        draw.rectangle([x0, y0, x0 + w, y0 + h], fill=(12, 34, 24))
        for i, (fy0, fy1) in enumerate([(0.6, 0.4), (0.55, 0.3), (0.5, 0.35), (0.4, 0.2), (0.3, 0.12)]):
            bx = x0 + (0.08 + i * 0.18) * w
            draw.rectangle([bx, y0 + fy1 * h, bx + 10, y0 + fy0 * h], fill=(46, 180, 90))
    elif n == 5:  # CrowdStrike: shield + nodes on navy
        draw.rectangle([x0, y0, x0 + w, y0 + h], fill=(14, 30, 58))
        draw.polygon([(x0 + 0.5 * w, y0 + 0.1 * h), (x0 + 0.72 * w, y0 + 0.2 * h),
                      (x0 + 0.72 * w, y0 + 0.6 * h), (x0 + 0.5 * w, y0 + 0.9 * h),
                      (x0 + 0.28 * w, y0 + 0.6 * h), (x0 + 0.28 * w, y0 + 0.2 * h)],
                     outline=(120, 220, 150), width=2)
        for fx, fy in [(0.2, 0.3), (0.8, 0.3), (0.15, 0.7), (0.85, 0.7)]:
            draw.ellipse([x0 + fx * w - 3, y0 + fy * h - 3, x0 + fx * w + 3, y0 + fy * h + 3],
                         fill=(120, 220, 150))
    elif n == 6:  # EU: blue band, circle of yellow stars
        draw.rectangle([x0, y0, x0 + w, y0 + h], fill=(20, 42, 110))
        import math
        for i in range(8):
            a = i * math.pi / 4
            px = x0 + 0.5 * w + 0.32 * w * math.cos(a)
            py = y0 + 0.5 * h + 0.32 * h * math.sin(a)
            draw.ellipse([px - 2, py - 2, px + 2, py + 2], fill=(240, 210, 60))
    elif n == 7:  # NATO: radar arcs
        draw.rectangle([x0, y0, x0 + w, y0 + h], fill=(18, 40, 70))
        for r in (8, 16, 24):
            draw.arc([x0 + 0.5 * w - r, y0 + h - r, x0 + 0.5 * w + r, y0 + h + r],
                     start=270, end=360, fill=(120, 200, 240), width=2)
        draw.ellipse([x0 + 0.5 * w - 3, y0 + h - 6, x0 + 0.5 * w + 3, y0 + h], fill=(240, 210, 120))
    elif n == 8:  # India-Nepal: mountains + sun
        draw.rectangle([x0, y0, x0 + w, y0 + h], fill=(24, 90, 100))
        draw.ellipse([x0 + 0.78 * w, y0 + 0.12 * h, x0 + 0.90 * w, y0 + 0.45 * h],
                     fill=(250, 220, 130))
        draw.polygon([(x0 + 0.05 * w, y0 + h), (x0 + 0.30 * w, y0 + 0.15 * h),
                      (x0 + 0.55 * w, y0 + h)], fill=(60, 50, 60))
        draw.polygon([(x0 + 0.45 * w, y0 + h), (x0 + 0.70 * w, y0 + 0.25 * h),
                      (x0 + 0.95 * w, y0 + h)], fill=(90, 70, 80))
    elif n == 9:  # Cikande: factory + smoke
        draw.rectangle([x0, y0, x0 + w, y0 + h], fill=(120, 90, 70))
        draw.rectangle([x0 + 0.10 * w, y0 + 0.45 * h, x0 + 0.55 * w, y0 + h], fill=(60, 55, 55))
        draw.rectangle([x0 + 0.60 * w, y0 + 0.20 * h, x0 + 0.68 * w, y0 + h], fill=(60, 55, 55))
        for fx, fy in [(0.62, 0.12), (0.68, 0.05), (0.75, 0.12)]:
            draw.ellipse([x0 + fx * w - 4, y0 + fy * h - 3, x0 + fx * w + 4, y0 + fy * h + 3],
                         fill=(200, 190, 180))
        draw.polygon([(x0 + 0.15 * w, y0 + 0.45 * h), (x0 + 0.25 * w, y0 + 0.45 * h),
                      (x0 + 0.20 * w, y0 + 0.30 * h)], fill=(220, 90, 40))
    elif n == 10:  # Dymer: broken block + rubble
        draw.rectangle([x0, y0, x0 + w, y0 + h], fill=(70, 80, 100))
        draw.polygon([(x0 + 0.15 * w, y0 + h), (x0 + 0.15 * w, y0 + 0.30 * h),
                      (x0 + 0.30 * w, y0 + 0.15 * h), (x0 + 0.38 * w, y0 + 0.35 * h),
                      (x0 + 0.50 * w, y0 + 0.20 * h), (x0 + 0.55 * w, y0 + h)],
                     fill=(40, 44, 55))
        for fx, fy in [(0.65, 0.75), (0.72, 0.85), (0.80, 0.75), (0.88, 0.85)]:
            draw.rectangle([x0 + fx * w - 3, y0 + fy * h - 3, x0 + fx * w + 3, y0 + fy * h + 3],
                           fill=(150, 145, 135))
        draw.ellipse([x0 + 0.82 * w, y0 + 0.10 * h, x0 + 0.92 * w, y0 + 0.32 * h],
                     fill=(240, 230, 190))
    elif n == 11:  # Kospi: falling candles
        draw.rectangle([x0, y0, x0 + w, y0 + h], fill=(30, 16, 20))
        for i, (fy0, fy1) in enumerate([(0.2, 0.4), (0.3, 0.55), (0.45, 0.65), (0.55, 0.8), (0.7, 0.9)]):
            bx = x0 + (0.08 + i * 0.18) * w
            draw.rectangle([bx, y0 + fy0 * h, bx + 10, y0 + fy1 * h], fill=(200, 70, 60))
    elif n == 12:  # Hormuz: tanker + mines on teal sea
        draw.rectangle([x0, y0, x0 + w, y0 + h], fill=(16, 70, 80))
        draw.rectangle([x0 + 0.15 * w, y0 + 0.45 * h, x0 + 0.75 * w, y0 + 0.62 * h],
                       fill=(150, 155, 165))
        draw.rectangle([x0 + 0.60 * w, y0 + 0.30 * h, x0 + 0.68 * w, y0 + 0.45 * h],
                       fill=(150, 155, 165))
        for fx, fy in [(0.82, 0.7), (0.88, 0.55), (0.08, 0.7)]:
            draw.ellipse([x0 + fx * w - 3, y0 + fy * h - 3, x0 + fx * w + 3, y0 + fy * h + 3],
                         fill=(240, 210, 120))
    elif n == 13:  # Rostov: refinery towers + flame
        draw.rectangle([x0, y0, x0 + w, y0 + h], fill=(60, 30, 20))
        for fx in (0.15, 0.35, 0.55):
            draw.rectangle([x0 + fx * w, y0 + 0.35 * h, x0 + (fx + 0.08) * w, y0 + h],
                           fill=(40, 36, 34))
        draw.polygon([(x0 + 0.78 * w, y0 + 0.55 * h), (x0 + 0.84 * w, y0 + 0.25 * h),
                      (x0 + 0.90 * w, y0 + 0.55 * h)], fill=(240, 160, 40))
        draw.polygon([(x0 + 0.80 * w, y0 + 0.55 * h), (x0 + 0.84 * w, y0 + 0.38 * h),
                      (x0 + 0.88 * w, y0 + 0.55 * h)], fill=(250, 220, 90))
    elif n == 14:  # Korea: taegeuk circle + building
        draw.rectangle([x0, y0, x0 + w, y0 + h], fill=(235, 230, 220))
        draw.ellipse([x0 + 0.12 * w, y0 + 0.15 * h, x0 + 0.32 * w, y0 + 0.85 * h],
                     fill=(200, 50, 50))
        draw.ellipse([x0 + 0.12 * w, y0 + 0.50 * h, x0 + 0.32 * w, y0 + 0.85 * h],
                     fill=(40, 60, 160))
        draw.rectangle([x0 + 0.55 * w, y0 + 0.30 * h, x0 + 0.88 * w, y0 + h], fill=(70, 80, 100))
        for i in range(3):
            draw.rectangle([x0 + (0.60 + i * 0.09) * w, y0 + 0.40 * h,
                            x0 + (0.65 + i * 0.09) * w, y0 + 0.55 * h],
                           fill=(240, 220, 130))
    else:  # 15 Democrats: capitol dome + ballot box
        draw.rectangle([x0, y0, x0 + w, y0 + h], fill=(20, 36, 70))
        draw.polygon([(x0 + 0.35 * w, y0 + 0.55 * h), (x0 + 0.50 * w, y0 + 0.15 * h),
                      (x0 + 0.65 * w, y0 + 0.55 * h)], fill=(220, 220, 215))
        draw.rectangle([x0 + 0.30 * w, y0 + 0.55 * h, x0 + 0.70 * w, y0 + h], fill=(220, 220, 215))
        draw.rectangle([x0 + 0.74 * w, y0 + 0.60 * h, x0 + 0.92 * w, y0 + 0.85 * h],
                       fill=(46, 95, 163))
        draw.rectangle([x0 + 0.78 * w, y0 + 0.52 * h, x0 + 0.88 * w, y0 + 0.60 * h],
                       fill=(250, 247, 238))


# --- build ------------------------------------------------------------------
MX = 16
CW = W - 2 * MX


def build(quality=55):
    img = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(img)

    # masthead band
    d.rectangle([0, 0, W, 20], fill=NAVY)
    tracked(d, MX, 4, "THE WORLD IN ONE DAY", F_AN(13), (255, 255, 255), 0.06)
    r = "DAY 327 OF 2026 \u00b7 ALL TIMES UTC"
    d.text((W - MX - d.textlength(r, font=F_AN(11)), 5), r, font=F_AN(11),
           fill=(200, 205, 215))

    # date — largest fitting Playfair Black (76px; 110px needs 1384px)
    center(d, 22, "Monday 23 November 2026", F_DATE(76), INK)

    # count strip
    cs = "38 STORIES \u00b7 7 REGIONS \u00b7 EVERY ONE DATED MONDAY 23 NOVEMBER 2026"
    wcs = d.textlength(cs, font=F_AN(26)) + 0.04 * 26 * len(cs)
    tracked(d, (W - wcs) / 2, 98, cs, F_AN(26), RED, 0.04)
    d.line([MX, 128, W - MX, 128], fill=RULE, width=1)

    # numbers strip: figure 34px + label 26px, tabular digits
    ny = 130
    cellw = CW / 6.0
    for i, (fig, lab) in enumerate(NUMBERS):
        cx = MX + cellw * i + cellw / 2
        fw = d.textlength(fig, font=F_AN(34))
        d.text((cx - fw / 2, ny), fig, font=F_AN(34), fill=INK)
        lw = d.textlength(lab, font=F_AN(26))
        d.text((cx - lw / 2, ny + 34), lab, font=F_AN(26), fill=RED)
        if i:
            d.line([MX + cellw * i, ny + 4, MX + cellw * i, ny + 60],
                   fill=RULE, width=1)
    d.line([MX, 194, W - MX, 194], fill=RULE, width=1)

    # region bar: 26px count + 13px name per segment
    ry = 198
    segw = CW / 7.0
    for i, (name, cnt) in enumerate(REGIONS):
        x0 = MX + segw * i
        d.rectangle([x0, ry, x0 + segw - 1, ry + 42], fill=REGION_COLORS[name])
        c = str(cnt)
        cw_ = d.textlength(c, font=F_AN(26))
        d.text((x0 + (segw - 1 - cw_) / 2, ry + 2), c, font=F_AN(26),
               fill=(255, 255, 255))
        nw = d.textlength(name, font=F_ANM(13)) + 0.05 * 13 * len(name)
        tracked(d, x0 + (segw - 1 - nw) / 2, ry + 28, name, F_ANM(13),
                (255, 255, 255), 0.05)

    # UTC strip
    uy = 244
    d.rectangle([MX, uy, W - MX, uy + 16], fill=NAVY2)
    tx = MX + 8
    d.text((tx, uy + 2), "THE DAY IN UTC", font=F_AN(12), fill=(240, 210, 120))
    tx += d.textlength("THE DAY IN UTC", font=F_AN(12)) + 14
    for t, s in TIMELINE:
        seg = f"{t}  {s}"
        wseg = d.textlength(seg, font=F_ANM(12))
        if tx + wseg > W - MX - 4:
            break
        d.text((tx, uy + 2), t, font=F_AN(12), fill=(240, 210, 120))
        d.text((tx + d.textlength(t + "  ", font=F_AN(12)), uy + 2), s,
               font=F_ANM(12), fill=(255, 255, 255))
        tx += wseg + 16

    # leads
    ly = 264
    colw = (CW - 32) / 3.0
    for i, lead in enumerate(LEADS):
        x0 = MX + i * (colw + 16)
        lead_art(d, i, x0, ly, colw, 46)
        chip(d, x0 + 6, ly + 6, lead["banner"], F_AN(9), (255, 255, 255), RED)
        py = ly + 50
        d.text((x0, py), f"{lead['n']}  {lead['place']} \u00b7 {lead['beat']}",
               font=F_AN(13), fill=RED)
        tag = lead["tag"]
        tw = d.textlength(tag, font=F_AN(9)) + 8
        chip(d, x0 + colw - tw, py - 1, tag, F_AN(9),
             (255, 255, 255), TAG_COLORS[tag])
        hy = py + 16
        hl = fit_lines(d, lead["head"], F_HEAD(44), colw, 2, tag=f"lead{i}head")
        draw_lines(d, hl, x0, hy, F_HEAD(44), INK, 50)
        dy = hy + len(hl) * 50 + 2
        dl = fit_lines(d, lead["deck"], F_DECK(15), colw, 2, tag=f"lead{i}deck")
        draw_lines(d, dl, x0, dy, F_DECK(15), INK, 17)
        sy = dy + len(dl) * 17 + 2
        d.text((x0, sy), lead["src"], font=F_ANM(11), fill=GREY)

    # cards: 2 rows x 6
    cy0 = 483
    cardw = (CW - 5 * 8) / 6.0
    cardh = 144
    for r in range(2):
        for c in range(6):
            idx = r * 6 + c
            n, place, beat, banner, head, deck, src, tag = CARDS[idx]
            x0 = MX + c * (cardw + 8)
            y0 = cy0 + r * (cardh + 8)
            d.rectangle([x0, y0, x0 + cardw, y0 + cardh], fill=PAPER,
                        outline=RULE, width=1)
            card_art(d, n, x0 + 1, y0 + 1, cardw - 2, 24)
            chip(d, x0 + 5, y0 + 5, banner, F_AN(8), (255, 255, 255), RED)
            py = y0 + 31
            d.text((x0 + 5, py), f"{n}  {place}", font=F_AN(11), fill=RED)
            tw = d.textlength(tag, font=F_AN(9)) + 8
            chip(d, x0 + cardw - tw - 4, py - 1, tag, F_AN(9),
                 (255, 255, 255), TAG_COLORS[tag])
            hy = py + 14
            hl = fit_lines(d, head, F_AN(27), cardw - 10, 2, tag=f"card{n}head")
            draw_lines(d, hl, x0 + 5, hy, F_AN(27), INK, 29)
            dy = hy + len(hl) * 29 + 2
            dl = fit_lines(d, deck, F_DECK(13), cardw - 10, 2, tag=f"card{n}deck")
            draw_lines(d, dl, x0 + 5, dy, F_DECK(13), INK, 14.5)
            sy = dy + len(dl) * 14.5 + 2
            sl = fit_lines(d, src, F_ANM(10), cardw - 10, 1, tag=f"card{n}src")
            if sl:
                d.text((x0 + 5, sy), sl[0], font=F_ANM(10), fill=GREY)

    # map + briefs
    by = 787
    d.text((MX, by), "WHERE IT HAPPENED", font=F_AN(13), fill=RED)
    d.text((MX, by + 14), "pins match story numbers", font=F_ANM(11), fill=GREY)
    mapbox = (MX, by + 28, 300, 106)
    draw_map(d, mapbox, PINS)
    bx = MX + 312
    bw = W - MX - bx
    d.text((bx, by), "ALSO ON MONDAY 23 NOVEMBER \u2014 23 MORE STORIES",
           font=F_AN(13), fill=RED)
    colw2 = (bw - 16) / 3.0
    for i, (n, region, text) in enumerate(BRIEFS):
        col = i // 8
        row = i % 8
        x0 = bx + col * (colw2 + 8)
        yy = by + 16 + row * 15
        prefix = f"{n} {region} \u2014 "
        pw = d.textlength(prefix, font=F_DECKB(12))
        d.text((x0, yy), prefix, font=F_DECKB(12), fill=RED)
        avail = colw2 - pw
        if d.textlength(text, font=F_DECK(12)) > avail:
            fsize = 11.5
            while d.textlength(text, font=F_DECK(fsize)) > avail and fsize > 9:
                fsize -= 0.5
            if d.textlength(text, font=F_DECK(fsize)) > avail:
                TRUNCATED.append(("brief", text, "too long even at 9px", avail))
            d.text((x0 + pw, yy + 0.5), text, font=F_DECK(fsize), fill=INK)
        else:
            d.text((x0 + pw, yy), text, font=F_DECK(12), fill=INK)

    # DATE CHECK
    dy = 931
    dc_lines = fit_lines(d, DATE_CHECK, F_DECKB(22), CW - 16, 2, tag="datecheck")
    dc_h = len(dc_lines) * 26 + 10
    d.rectangle([MX, dy, W - MX, dy + dc_h], outline=RED, width=2,
                fill=(255, 250, 240))
    draw_lines(d, dc_lines, MX + 8, dy + 5, F_DECKB(22), INK, 26)

    # sources footer
    sy = dy + dc_h + 6
    d.text((MX, sy), SOURCES, font=F_AN(22), fill=GREY)
    bottom = sy + 22
    assert bottom <= 1022, f"layout overflows: bottom={bottom}"
    assert not TRUNCATED, f"truncated text: {TRUNCATED[:5]}"

    out = os.path.join(HERE, "image.jpg")
    img.save(out, "JPEG", quality=quality, optimize=True)
    data = open(out, "rb").read()
    sha = hashlib.sha256(data).hexdigest()
    print(f"image.jpg: {len(data)} bytes, sha256 {sha}, bottom={bottom}, "
          f"datecheck_lines={len(dc_lines)}")
    return out, len(data), sha


if __name__ == "__main__":
    q = int(sys.argv[1]) if len(sys.argv) > 1 else 55
    build(q)
