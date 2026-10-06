"""Renders the "Seen Today" poster for the 13.3" Spectra 6 e-ink panel (1200x1600 portrait)."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

SIZE = (1200, 1600)
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
) -> Image.Image:
    now = now or datetime.now()
    t = text(lang)
    img = Image.new("RGB", SIZE, BLACK)
    d = ImageDraw.Draw(img)
    W, H = SIZE

    _center(d, 70, subtitle, font("italic", 38), WHITE)
    _center(d, 125, title.upper(), font("regular", 96), YELLOW, tracking=6)
    _center(d, 250, period, font("italic", 34), WHITE)
    d.line([(W / 2 - 120, 315), (W / 2 + 120, 315)], fill=YELLOW, width=3)

    shown = tiles[:max_tiles]
    if shown:
        _grid(img, d, shown, top=360, bottom=H - 150, t=t)
    else:
        _center(d, 760, t["empty"], font("italic", 64), WHITE)
        _center(d, 850, t["empty2"], font("italic", 40), WHITE)

    visits = sum(tile.visits for tile in tiles)
    footer = f"{len(tiles)} {t['species']} · {visits} {t['visits_total']}"
    if tiles:
        footer += f" · {t['last']} {datetime.fromtimestamp(max(tile.last_seen for tile in tiles)):%H:%M}"
    _center(d, H - 105, footer, font("regular", 32), WHITE)
    _center(d, H - 58, f"{t['updated']} {now:%H:%M}", font("italic", 24), WHITE)
    return img


def _grid(img: Image.Image, d: ImageDraw.ImageDraw, tiles: list[Tile], top: int, bottom: int, t: dict) -> None:
    n = len(tiles)
    cols = 1 if n == 1 else 2 if n <= 4 else 3
    rows = math.ceil(n / cols)
    gap = 40
    text_h = 110 if cols == 1 else 90
    cell_w = (SIZE[0] - 2 * MARGIN - (cols - 1) * gap) / cols
    cell_h = (bottom - top - (rows - 1) * gap) / rows
    side = int(min(cell_w, cell_h - text_h))
    # Rows are usually limited by width: centre the block vertically instead of spreading it.
    pitch = side + text_h + gap
    top += (bottom - top - (rows * pitch - gap)) / 2
    name_font = font("bold", 56 if cols == 1 else 40 if cols == 2 else 32)
    meta_font = font("italic", 34 if cols == 1 else 28 if cols == 2 else 24)

    for i, tile in enumerate(tiles):
        r, c = divmod(i, cols)
        # Centre a short last row.
        in_row = min(cols, n - r * cols)
        row_w = in_row * cell_w + (in_row - 1) * gap
        x0 = (SIZE[0] - row_w) / 2 + c * (cell_w + gap)
        y0 = top + r * pitch
        px = int(x0 + (cell_w - side) / 2)
        py = int(y0)

        d.rectangle([px - 4, py - 4, px + side + 3, py + side + 3], outline=WHITE, width=2)
        if tile.photo is not None:
            img.paste(ImageOps.fit(tile.photo.convert("RGB"), (side, side), Image.LANCZOS), (px, py))
        else:
            _center(d, py + side // 2 - 20, "?", font("italic", side // 3), WHITE, cx=px + side / 2)

        cx = x0 + cell_w / 2
        name = _fit(d, tile.name, name_font, cell_w)
        _center(d, py + side + 18, name, name_font, WHITE, cx=cx)
        meta = f"{tile.visits} {t['visit'] if tile.visits == 1 else t['visits']} · {datetime.fromtimestamp(tile.last_seen):%H:%M}"
        _center(d, py + side + 18 + name_font.size + 10, meta, meta_font, YELLOW, cx=cx)


def _center(d, y, text, f, fill, tracking: int = 0, cx: float | None = None) -> None:
    cx = SIZE[0] / 2 if cx is None else cx
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
