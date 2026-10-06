"""Configuration, loaded from a TOML file (see config.example.toml)."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field, fields
from pathlib import Path


@dataclass
class CamConfig:
    # "picamera2", "opencv:<device index>", or a path to a video file (for testing).
    source: str = "picamera2"
    main_size: tuple[int, int] = (2304, 1296)
    lores_size: tuple[int, int] = (480, 270)
    framerate: float = 10.0
    model: str = "models/mobilenet_v2_1.0_224_inat_bird_quant.tflite"
    labels: str = "models/inat_bird_labels.txt"
    # Bundled region name (gibbird/data/regions/<name>.csv) or a path to a CSV.
    region: str = "gothenburg"
    # Ignore species that are not in the region list. Strongly recommended.
    allowlist_only: bool = True
    min_score: float = 0.55
    # A species is confirmed when it wins `confirm_frames` of the last `confirm_window` checks.
    confirm_frames: int = 2
    confirm_window: int = 4
    # Sightings of the same species closer than this are one visit.
    visit_gap_s: float = 120.0
    classify_interval_s: float = 0.4
    motion_threshold: int = 25
    motion_min_area: float = 0.002
    motion_max_area: float = 0.5
    crop_scale: float = 1.6
    data_dir: str = "data"
    http_host: str = "0.0.0.0"
    http_port: int = 8080


@dataclass
class FrameConfig:
    server: str = "http://birdcam.local:8080"
    subtitle: str = "Balcony Visitors"
    title: str = "Seen Today"
    title_recent: str = "Recent Visitors"
    # "local" uses the region file's local names (Swedish for Gothenburg), "en" English.
    names: str = "local"
    # Language for dates and labels on the poster ("en", "sv"; see render.TEXT).
    language: str = "en"
    # Degrees to rotate the portrait poster onto the landscape panel (90 or 270).
    rotation: int = 90
    saturation: float = 0.6
    min_refresh_minutes: int = 15
    poll_seconds: int = 120
    quiet_hours: tuple[int, int] = (23, 7)
    max_tiles: int = 9


@dataclass
class Config:
    cam: CamConfig = field(default_factory=CamConfig)
    frame: FrameConfig = field(default_factory=FrameConfig)
    base_dir: Path = Path(".")

    def path(self, p: str) -> Path:
        """Resolve a path from the config relative to the config file's directory."""
        q = Path(p).expanduser()
        return q if q.is_absolute() else self.base_dir / q


def _section(cls, data: dict, name: str):
    known = {f.name: f for f in fields(cls)}
    unknown = set(data) - set(known)
    if unknown:
        raise ValueError(f"unknown key(s) in [{name}]: {', '.join(sorted(unknown))}")
    values = {k: tuple(v) if isinstance(v, list) else v for k, v in data.items()}
    return cls(**values)


def load(path: str | Path | None) -> Config:
    if path is None:
        return Config()
    path = Path(path)
    with path.open("rb") as f:
        data = tomllib.load(f)
    unknown = set(data) - {"cam", "frame"}
    if unknown:
        raise ValueError(f"unknown section(s): {', '.join(sorted(unknown))}")
    return Config(
        cam=_section(CamConfig, data.get("cam", {}), "cam"),
        frame=_section(FrameConfig, data.get("frame", {}), "frame"),
        base_dir=path.resolve().parent,
    )
