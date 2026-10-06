"""Output targets for the poster: an e-ink panel (Pimoroni Inky or Waveshare), or a PNG."""

from __future__ import annotations

import importlib
import logging
from pathlib import Path
from typing import Protocol

from PIL import Image

from .render import simulate_eink

log = logging.getLogger(__name__)


class Display(Protocol):
    def show(self, img: Image.Image) -> None: ...


class InkyDisplay:
    def __init__(self, rotation: int = 90, saturation: float = 0.6):
        from inky.auto import auto

        self._inky = auto(ask_user=False, verbose=True)
        w, h = self._inky.resolution
        self.poster_size = (min(w, h), max(w, h))  # we always draw in portrait
        self.rotation = rotation
        self.saturation = saturation

    def show(self, img: Image.Image) -> None:
        w, h = self._inky.resolution
        if (img.width > img.height) != (w > h):
            img = img.rotate(self.rotation, expand=True)
        if img.size != (w, h):
            img = img.resize((w, h), Image.LANCZOS)
        try:
            self._inky.set_image(img, saturation=self.saturation)
        except TypeError:  # displays without a saturation option
            self._inky.set_image(img)
        log.info("refreshing e-ink panel (takes ~30 s)")
        self._inky.show()


class WaveshareDisplay:
    """Waveshare e-Paper HATs, through Waveshare's own driver (bundled in gibbird/vendor)."""

    def __init__(self, model: str = "epd7in3e", rotation: int = 90):
        driver = importlib.import_module(f"gibbird.vendor.waveshare_epd.{model}")
        self._epd = driver.EPD()
        w, h = self._epd.width, self._epd.height
        self.poster_size = (min(w, h), max(w, h))  # we always draw in portrait
        self.rotation = rotation

    def show(self, img: Image.Image) -> None:
        w, h = self._epd.width, self._epd.height
        if (img.width > img.height) != (w > h):
            img = img.rotate(self.rotation, expand=True)
        if img.size != (w, h):
            img = img.resize((w, h), Image.LANCZOS)
        log.info("refreshing e-ink panel (takes ~30 s)")
        self._epd.init()
        self._epd.display(self._epd.getbuffer(img))
        self._epd.sleep()  # power the panel down between refreshes, as Waveshare recommends


def make_display(kind: str, rotation: int = 90, saturation: float = 0.6) -> Display:
    """`kind` is "inky" or "waveshare:<driver>", e.g. "waveshare:epd7in3e"."""
    if kind == "inky":
        return InkyDisplay(rotation, saturation)
    if kind.startswith("waveshare:"):
        return WaveshareDisplay(kind.split(":", 1)[1], rotation)
    raise ValueError(f"unknown display {kind!r}: use 'inky' or 'waveshare:<driver>'")


class PreviewDisplay:
    def __init__(self, path: str | Path, simulate: bool = True):
        self.path = Path(path)
        self.simulate = simulate

    def show(self, img: Image.Image) -> None:
        (simulate_eink(img) if self.simulate else img).save(self.path)
        log.info("wrote preview %s", self.path)
