"""Turns camera frames into confirmed bird visits."""

from __future__ import annotations

import logging
import re
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import numpy as np
from PIL import Image

from .camera import Frame
from .classifier import Classifier, Prediction
from .config import CamConfig
from .motion import MotionDetector, square_crop
from .names import Species
from .store import Store

log = logging.getLogger(__name__)

# Write ongoing visits to the database at most this often (spares the SD card).
FLUSH_INTERVAL_S = 5.0


@dataclass
class _OpenVisit:
    id: int
    last_seen: float
    last_flush: float
    best_score: float
    photo: str


@dataclass(frozen=True)
class Sighting:
    species: Species
    score: float
    new_visit: bool


class BirdWatcher:
    def __init__(
        self,
        cfg: CamConfig,
        classifier: Classifier,
        region: dict[str, Species],
        store: Store,
        photos_dir: Path,
    ):
        self.cfg = cfg
        self.classifier = classifier
        self.region = region
        self.store = store
        self.photos_dir = photos_dir
        photos_dir.mkdir(parents=True, exist_ok=True)
        self.motion = MotionDetector(cfg.motion_threshold, cfg.motion_min_area, cfg.motion_max_area)
        self._recent: deque[str | None] = deque(maxlen=cfg.confirm_window)
        self._open: dict[str, _OpenVisit] = {}
        self._last_classify = float("-inf")

    def process(self, frame: Frame) -> Sighting | None:
        boxes = self.motion.update(frame.lores)
        if not boxes or frame.t - self._last_classify < self.cfg.classify_interval_s:
            return None
        self._last_classify = frame.t

        main = frame.main()
        hit: tuple[Species, float, np.ndarray] | None = None
        for box in boxes[:2]:
            crop = square_crop(main, box, self.cfg.crop_scale)
            pred = self.classifier.classify(crop, top_k=1)[0]
            species = self._accept(pred)
            if species:
                hit = (species, pred.score, crop)
                break
        self._recent.append(hit[0].sci if hit else None)
        if hit is None:
            return None

        species, score, crop = hit
        if self._recent.count(species.sci) < self.cfg.confirm_frames:
            return None
        return self._record(species, score, crop, frame.t)

    def _accept(self, pred: Prediction) -> Species | None:
        if pred.is_background or pred.score < self.cfg.min_score:
            return None
        species = self.region.get(pred.sci.lower())
        if species is None and not self.cfg.allowlist_only:
            species = Species(pred.sci, pred.common, "")
        if species is None:
            log.debug("ignoring %s (%.2f): not in region list", pred.sci, pred.score)
        return species

    def _record(self, species: Species, score: float, crop: np.ndarray, t: float) -> Sighting:
        visit = self._open.get(species.sci)
        if visit and t - visit.last_seen <= self.cfg.visit_gap_s:
            visit.last_seen = t
            if score > visit.best_score:
                visit.best_score = score
                self._save(crop, visit.photo)  # keep the most confident photo of the visit
            if t - visit.last_flush >= FLUSH_INTERVAL_S:
                self.store.extend_visit(visit.id, t, visit.best_score)
                visit.last_flush = t
            return Sighting(species, score, new_visit=False)

        if visit:  # close out the previous visit before starting a new one
            self.store.extend_visit(visit.id, visit.last_seen, visit.best_score)
        photo = f"{datetime.fromtimestamp(t):%Y%m%d-%H%M%S}-{_slug(species.sci)}.jpg"
        self._save(crop, photo)
        visit_id = self.store.open_visit(species.sci, t, score, photo)
        self._open[species.sci] = _OpenVisit(visit_id, t, t, score, photo)
        log.info("new visit: %s (%s) score %.2f", species.en, species.sci, score)
        return Sighting(species, score, new_visit=True)

    def _save(self, crop: np.ndarray, name: str) -> None:
        img = Image.fromarray(crop)
        img.thumbnail((640, 640))
        img.save(self.photos_dir / name, quality=88)


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
