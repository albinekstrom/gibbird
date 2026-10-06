"""Detection zones and the camera's calibration to a real-world plane.

Image points are normalised (0..1 of width/height). World points are centimetres on
one flat reference surface, e.g. the balcony floor or the face of the railing.
With at least 4 image <-> world point pairs we fit a homography, which lets us
store zones in centimetres (they survive the camera being nudged: just redo the
reference points) and estimate how big a moving thing really is.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path

import cv2
import numpy as np

from .motion import Box

Point = tuple[float, float]


@dataclass
class Calibration:
    image_points: list[Point] = field(default_factory=list)
    world_points: list[Point] = field(default_factory=list)
    # Polygons; in world cm when zones_space == "world", else normalised image coords.
    zones: list[list[Point]] = field(default_factory=list)
    zones_space: str = "image"
    # Moving things outside this size range (on the reference plane) are not birds.
    min_size_cm: float = 6.0
    max_size_cm: float = 80.0

    def __post_init__(self):
        if len(self.image_points) != len(self.world_points):
            raise ValueError("need the same number of image and world points")
        if self.zones_space not in ("image", "world"):
            raise ValueError("zones_space must be 'image' or 'world'")
        for poly in self.zones:
            if len(poly) < 3:
                raise ValueError("a zone needs at least 3 corners")
        self._H = self._H_inv = None
        if len(self.image_points) >= 4:
            H, _ = cv2.findHomography(
                np.float64(self.image_points), np.float64(self.world_points), 0
            )
            if H is None or abs(np.linalg.det(H)) < 1e-12:
                raise ValueError("reference points are degenerate (e.g. 3 in a line)")
            self._H, self._H_inv = H, np.linalg.inv(H)

    # --- geometry -------------------------------------------------------------

    @property
    def calibrated(self) -> bool:
        return self._H is not None

    def to_world(self, pts) -> np.ndarray:
        return _apply(self._H, pts)

    def to_image(self, pts) -> np.ndarray:
        return _apply(self._H_inv, pts)

    def zones_image(self) -> list[np.ndarray]:
        """Zones as normalised image polygons (whatever space they are stored in)."""
        if self.zones_space == "image":
            return [np.float64(z) for z in self.zones]
        if not self.calibrated:
            return []
        return [self.to_image(z) for z in self.zones]

    def zones_usable(self) -> bool:
        return bool(self.zones) and (self.zones_space == "image" or self.calibrated)

    def reprojection_error_cm(self) -> float | None:
        """Mean distance between measured and fitted world points (needs 5+ points)."""
        if not self.calibrated or len(self.image_points) < 5:
            return None
        fitted = self.to_world(self.image_points)
        return float(np.mean(np.linalg.norm(fitted - np.float64(self.world_points), axis=1)))

    def zone_areas_m2(self) -> list[float] | None:
        if not self.calibrated:
            return None
        polys = self.zones if self.zones_space == "world" else [self.to_world(z) for z in self.zones]
        return [abs(cv2.contourArea(np.float32(p))) / 10_000 for p in polys]

    def size_cm(self, box: Box) -> float | None:
        """Width of a box measured along its bottom edge, where a bird stands."""
        if not self.calibrated:
            return None
        x, y, w, h = box
        a, b = self.to_world([(x, y + h), (x + w, y + h)])
        return float(np.linalg.norm(a - b))

    def accepts(self, box: Box) -> tuple[bool, str]:
        x, y, w, h = box
        anchor = (x + w / 2, y + h)  # bottom centre: where a perched bird touches the surface
        if self.zones_usable():
            if self.zones_space == "world":
                p, polys = tuple(self.to_world([anchor])[0]), self.zones
            else:
                p, polys = anchor, self.zones
            if not any(cv2.pointPolygonTest(np.float32(z), p, False) >= 0 for z in polys):
                return False, "outside zones"
        size = self.size_cm(box)
        if size is not None and not (self.min_size_cm <= size <= self.max_size_cm):
            return False, f"size {size:.0f} cm"
        return True, ""

    def motion_mask(self, shape: tuple[int, int]) -> np.ndarray | None:
        """uint8 mask (255 inside zones) for a frame of `shape` (h, w), or None for no zones."""
        polys = self.zones_image() if self.zones_usable() else []
        if not polys:
            return None
        h, w = shape
        mask = np.zeros((h, w), np.uint8)
        cv2.fillPoly(mask, [np.int32(np.round(p * [w, h])) for p in polys], 255)
        return mask

    def grid_lines(self, step_cm: float = 50) -> list[list[Point]]:
        """World grid over the reference points' extent, as normalised image polylines."""
        if not self.calibrated:
            return []
        wp = np.float64(self.world_points)
        (x0, y0), (x1, y1) = wp.min(axis=0), wp.max(axis=0)
        lines = []
        for x in np.arange(math.floor(x0 / step_cm) * step_cm, x1 + step_cm / 2, step_cm):
            lines.append([(x, y) for y in np.linspace(y0, y1, 20)])
        for y in np.arange(math.floor(y0 / step_cm) * step_cm, y1 + step_cm / 2, step_cm):
            lines.append([(x, y) for x in np.linspace(x0, x1, 20)])
        return [[tuple(map(float, p)) for p in self.to_image(line)] for line in lines]

    # --- persistence ----------------------------------------------------------

    def with_image_zones(self, zones_image: list[list[Point]]) -> Calibration:
        """New calibration with zones drawn on the image, stored in cm when possible."""
        zones = [[tuple(map(float, p)) for p in z] for z in zones_image]
        if self.calibrated:
            zones = [[tuple(map(float, p)) for p in self.to_world(z)] for z in zones]
        return Calibration(
            self.image_points, self.world_points, zones,
            "world" if self.calibrated else "image", self.min_size_cm, self.max_size_cm,
        )

    def to_dict(self) -> dict:
        return {
            "image_points": self.image_points,
            "world_points": self.world_points,
            "zones": self.zones,
            "zones_space": self.zones_space,
            "min_size_cm": self.min_size_cm,
            "max_size_cm": self.max_size_cm,
        }

    @classmethod
    def from_dict(cls, d: dict) -> Calibration:
        def pts(v) -> list[Point]:
            return [(float(p[0]), float(p[1])) for p in v]

        return cls(
            image_points=pts(d.get("image_points", [])),
            world_points=pts(d.get("world_points", [])),
            zones=[pts(z) for z in d.get("zones", [])],
            zones_space=d.get("zones_space", "image"),
            min_size_cm=float(d.get("min_size_cm", 6.0)),
            max_size_cm=float(d.get("max_size_cm", 80.0)),
        )

    @classmethod
    def load(cls, path: Path) -> Calibration:
        return cls.from_dict(json.loads(path.read_text())) if path.exists() else cls()

    def save(self, path: Path) -> None:
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.to_dict(), indent=2))
        tmp.replace(path)


def _apply(H: np.ndarray | None, pts) -> np.ndarray:
    if H is None:
        raise ValueError("camera is not calibrated (need 4+ reference points)")
    p = np.float64(pts).reshape(-1, 1, 2)
    return cv2.perspectiveTransform(p, H).reshape(-1, 2)
