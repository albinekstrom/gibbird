"""The bedroom frame: polls the camera Pi and redraws the e-ink panel when something changed."""

from __future__ import annotations

import hashlib
import io
import json
import logging
import time
from collections.abc import Callable
from datetime import datetime, timedelta
from urllib.error import URLError
from urllib.parse import quote
from urllib.request import urlopen

from PIL import Image

from .config import FrameConfig
from .display import Display
from .render import Tile, format_date, render_poster, text

log = logging.getLogger(__name__)


def http_get(url: str, timeout: float = 15) -> bytes:
    with urlopen(url, timeout=timeout) as resp:
        return resp.read()


def in_quiet_hours(now: datetime, quiet: tuple[int, int]) -> bool:
    start, end = quiet
    if start == end:
        return False
    if start < end:
        return start <= now.hour < end
    return now.hour >= start or now.hour < end


class FrameApp:
    def __init__(
        self,
        cfg: FrameConfig,
        display: Display,
        get: Callable[[str], bytes] = http_get,
        clock: Callable[[], datetime] = datetime.now,
    ):
        self.cfg = cfg
        self.display = display
        self.get = get
        self.clock = clock
        self._last_key: str | None = None
        self._last_push: datetime | None = None

    def tick(self) -> bool:
        """Check for news and refresh the panel if needed. Returns True if it refreshed."""
        now = self.clock()
        t = text(self.cfg.language)
        if self._last_push and in_quiet_hours(now, self.cfg.quiet_hours):
            return False

        try:
            data = self._summary(1)
            title, period = self.cfg.title, format_date(now, self.cfg.language)
            if not data["species"]:
                week = self._summary(7)
                if week["species"]:
                    data, title, period = week, self.cfg.title_recent, t["week"]
        except (URLError, OSError, ValueError) as e:
            log.warning("bird camera unreachable: %s", e)
            if self._last_push is None:
                poster = render_poster([], t["offline"], self.cfg.subtitle, t["offline2"], now, lang=self.cfg.language)
                self._push(poster, "offline", now)
                return True
            return False

        species = data["species"]
        key = hashlib.sha1(
            json.dumps([title, now.date().isoformat(), [(s["sci"], s["visits"]) for s in species]]).encode()
        ).hexdigest()
        if key == self._last_key:
            return False
        if self._last_push and now - self._last_push < timedelta(minutes=self.cfg.min_refresh_minutes):
            return False

        tiles = [
            Tile(self._name(s), s["visits"], s["last_seen"], self._photo(s["photo"]))
            for s in species[: self.cfg.max_tiles]
        ] + [Tile(self._name(s), s["visits"], s["last_seen"], None) for s in species[self.cfg.max_tiles :]]
        self._push(render_poster(tiles, title, self.cfg.subtitle, period, now, self.cfg.max_tiles, self.cfg.language), key, now)
        return True

    def run_forever(self) -> None:
        while True:
            try:
                self.tick()
            except Exception:
                log.exception("frame update failed")
            time.sleep(self.cfg.poll_seconds)

    def _push(self, img: Image.Image, key: str, now: datetime) -> None:
        self.display.show(img)
        self._last_key, self._last_push = key, now

    def _summary(self, days: int) -> dict:
        return json.loads(self.get(f"{self.cfg.server.rstrip('/')}/api/summary?days={days}"))

    def _photo(self, name: str) -> Image.Image | None:
        try:
            return Image.open(io.BytesIO(self.get(f"{self.cfg.server.rstrip('/')}/photos/{quote(name)}")))
        except Exception as e:
            log.warning("could not fetch photo %s: %s", name, e)
            return None

    def _name(self, s: dict) -> str:
        if self.cfg.names == "local" and s.get("local"):
            return s["local"]
        return s.get("en") or s["sci"]
