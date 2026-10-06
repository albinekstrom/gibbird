"""Renders the "Seen Today" poster for Inky Spectra 6 e-ink panels (any size, portrait)."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

SIZE = (1200, 1600)  # 13.3" panel in portrait; the layout's reference size
MARGIN = 70

# Pure panel colours dither least, so text uses only these.
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)

# Rough look of the six Spectra inks, only for previews on a computer.
SPECTRA_PREVIEW = [(20, 20, 20), (235, 235, 228), (230, 200, 30), (170, 40, 40), (40, 60, 140), (50, 100, 60)]

_FONT_DIRS = [
    "/usr/share/fonts/truetype/dejavu",
    "/System/Library/Fonts/Supplemental",
    "/Library/Fonts",
]
_FONTS = {
    "regular": ["DejaVuSerif.ttf", "Georgia.ttf"],
    "bold": ["DejaVuSerif-Bold.ttf", "Georgia Bold.ttf"],
    "italic": ["DejaVuSerif-Italic.ttf", "Georgia Italic.ttf"],
}


TEXT = {
    "en": {
        "visit": "visit", "visits": "visits", "species": "species", "visits_total": "visits",
        "last": "last at", "updated": "updated", "empty": "No visitors yet",
        "empty2": "The feeder is open.", "week": "the last seven days",
        "offline": "Offline", "offline2": "can't reach the bird camera",
        "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
        "months": ["January", "February", "March", "April", "May", "June", "July",
                   "August", "September", "October", "November", "December"],
    },
    "sv": {
        "visit": "besök", "visits": "besök", "species": "arter", "visits_total": "besök",
        "last": "senast", "updated": "uppdaterad", "empty": "Inga besökare än",
        "empty2": "Fågelbordet är dukat.", "week": "de senaste sju dagarna",
        "offline": "Offline", "offline2": "når inte fågelkameran",
        "days": ["måndag", "tisdag", "onsdag", "torsdag", "fredag", "lördag", "söndag"],
        "months": ["januari", "februari", "mars", "april", "maj", "juni", "juli",
                   "augusti", "september", "oktober", "november", "december"],
    },
}


def text(lang: str) -> dict:
    """UI strings; add a language by adding an entry to TEXT."""
    return TEXT.get(lang, TEXT["en"])


def format_date(d: datetime, lang: str) -> str:
    t = text(lang)
    return f"{t['days'][d.weekday()]} {d.day} {t['months'][d.month - 1]}"


@lru_cache(maxsize=64)
def font(style: str, size: int) -> ImageFont.FreeTypeFont:
    for d in _FONT_DIRS:
        for name in _FONTS[style]:
            path = Path(d) / name
            if path.exists():
                return ImageFont.truetype(str(path), size)
    return ImageFont.load_default(size)


@dataclass
class Tile:
    name: str
    visits: int
    last_seen: float
    photo: Image.Image | None


def render_poster(
    tiles: list[Tile],
    title: str,
    subtitle: str,
    period: str,
    now: datetime | None = None,
    max_tiles: int = 9,
    lang: str = "en",
    size: tuple[int, int] = SIZE,
) -> Image.Image:
    """Draw the poster at `size` (portrait). The layout is designed at 1200 px wide and
    scaled; small panels get relatively bigger text and at most 4 tiles."""
    now = now or datetime.now()
    t = text(lang)
    W, H = size
    u = W / SIZE[0]
    k = u * (1.3 if u < 0.6 else 1.0)  # text/spacing scale

    def px(v: float) -> int:
        return max(1, round(v * k))

    if W < 800:
        max_tiles = min(max_tiles, 4)
    img = Image.new("RGB", size, BLACK)
    d = ImageDraw.Draw(img)
    cx = W / 2

    _center(d, px(70), subtitle, font("italic", px(38)), WHITE, cx)
    _center(d, px(125), title.upper(), font("regular", px(96)), YELLOW, cx, tracking=px(6))
    _center(d, px(250), period, font("italic", px(34)), WHITE, cx)
    d.line([(cx - px(120), px(315)), (cx + px(120), px(315))], fill=YELLOW, width=px(3))

    shown = tiles[:max_tiles]
    if shown:
        _grid(img, d, shown, top=px(360), bottom=H - px(150), t=t, px=px)
    else:
        _center(d, H * 0.45, t["empty"], font("italic", px(64)), WHITE, cx)
        _center(d, H * 0.45 + px(90), t["empty2"], font("italic", px(40)), WHITE, cx)

    visits = sum(tile.visits for tile in tiles)
    footer = f"{len(tiles)} {t['species']} · {visits} {t['visits_total']}"
    if tiles:
        footer += f" · {t['last']} {datetime.fromtimestamp(max(tile.last_seen for tile in tiles)):%H:%M}"
    _center(d, H - px(105), _fit(d, footer, font("regular", px(32)), W - 2 * px(MARGIN)), font("regular", px(32)), WHITE, cx)
    _center(d, H - px(58), f"{t['updated']} {now:%H:%M}", font("italic", px(24)), WHITE, cx)
    return img


def _grid(img, d, tiles: list[Tile], top: int, bottom: int, t: dict, px) -> None:
    W = img.width
    n = len(tiles)
    cols = 1 if n == 1 else 2 if n <= 4 else 3
    rows = math.ceil(n / cols)
    gap = px(40)
    text_h = px(110 if cols == 1 else 90)
    cell_w = (W - 2 * px(MARGIN) - (cols - 1) * gap) / cols
    cell_h = (bottom - top - (rows - 1) * gap) / rows
    side = int(min(cell_w, cell_h - text_h))
    # Rows are usually limited by width: centre the block vertically instead of spreading it.
    pitch = side + text_h + gap
    top += (bottom - top - (rows * pitch - gap)) / 2
    name_font = font("bold", px(56 if cols == 1 else 40 if cols == 2 else 32))
    meta_font = font("italic", px(34 if cols == 1 else 28 if cols == 2 else 24))
    frame_pad = px(4)

    for i, tile in enumerate(tiles):
        r, c = divmod(i, cols)
        # Centre a short last row.
        in_row = min(cols, n - r * cols)
        row_w = in_row * cell_w + (in_row - 1) * gap
        x0 = (W - row_w) / 2 + c * (cell_w + gap)
        y0 = top + r * pitch
        x = int(x0 + (cell_w - side) / 2)
        y = int(y0)

        d.rectangle([x - frame_pad, y - frame_pad, x + side + frame_pad - 1, y + side + frame_pad - 1],
                    outline=WHITE, width=px(2))
        if tile.photo is not None:
            img.paste(ImageOps.fit(tile.photo.convert("RGB"), (side, side), Image.LANCZOS), (x, y))
        else:
            _center(d, y + side // 2 - side // 6, "?", font("italic", side // 3), WHITE, x + side / 2)

        cx = x0 + cell_w / 2
        _center(d, y + side + px(18), _fit(d, tile.name, name_font, cell_w), name_font, WHITE, cx)
        meta = f"{tile.visits} {t['visit'] if tile.visits == 1 else t['visits']} · {datetime.fromtimestamp(tile.last_seen):%H:%M}"
        _center(d, y + side + px(28) + name_font.size, meta, meta_font, YELLOW, cx)


def _center(d, y, text, f, fill, cx: float, tracking: int = 0) -> None:
    if not tracking:
        d.text((cx, y), text, font=f, fill=fill, anchor="ma")
        return
    widths = [d.textlength(ch, font=f) for ch in text]
    x = cx - (sum(widths) + tracking * (len(text) - 1)) / 2
    for ch, w in zip(text, widths):
        d.text((x, y), ch, font=f, fill=fill)
        x += w + tracking


def _fit(d, text: str, f, max_w: float) -> str:
    if d.textlength(text, font=f) <= max_w:
        return text
    while text and d.textlength(text + "…", font=f) > max_w:
        text = text[:-1]
    return text.rstrip() + "…"


def simulate_eink(img: Image.Image) -> Image.Image:
    """Approximate how the 6-colour panel will dither the image (for previews only)."""
    pal = Image.new("P", (1, 1))
    flat = [v for rgb in SPECTRA_PREVIEW for v in rgb]
    pal.putpalette(flat + flat[:3] * (256 - len(SPECTRA_PREVIEW)))
    return img.convert("RGB").quantize(palette=pal, dither=Image.Dither.FLOYDSTEINBERG).convert("RGB")
