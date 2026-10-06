"""Model labels and regional species lists."""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path

REGIONS_DIR = Path(__file__).parent / "data" / "regions"

_INDEXED = re.compile(r"^\s*(\d+)\s+(.+?)\s*$")
_SCI_COMMON = re.compile(r"^(?P<sci>[^()]+?)\s*\((?P<common>[^()]+)\)$")


@dataclass(frozen=True)
class Label:
    sci: str
    common: str

    @property
    def is_background(self) -> bool:
        return self.sci.lower() == "background"


@dataclass(frozen=True)
class Species:
    sci: str
    en: str
    local: str


def load_labels(path: str | Path) -> dict[int, Label]:
    """Parse a label file: one label per line, optionally prefixed by its index.

    Lines look like "Parus major (Great Tit)" or "12  Parus major (Great Tit)".
    """
    labels: dict[int, Label] = {}
    lines = [ln for ln in Path(path).read_text(encoding="utf-8").splitlines() if ln.strip()]
    for i, line in enumerate(lines):
        m = _INDEXED.match(line)
        idx, text = (int(m[1]), m[2]) if m else (i, line.strip())
        n = _SCI_COMMON.match(text)
        sci, common = (n["sci"].strip(), n["common"].strip()) if n else (text, text)
        labels[idx] = Label(sci, common)
    return labels


def region_path(region: str) -> Path:
    bundled = REGIONS_DIR / f"{region}.csv"
    return bundled if bundled.exists() else Path(region).expanduser()


def load_region(path: str | Path) -> dict[str, Species]:
    """Map lower-cased model label (incl. aliases) -> canonical regional species."""
    lines = [ln for ln in Path(path).read_text(encoding="utf-8").splitlines() if not ln.startswith("#")]
    out: dict[str, Species] = {}
    for row in csv.DictReader(lines):
        sci = row["sci"].strip()
        species = Species(sci, row.get("en", "").strip() or sci, row.get("local", "").strip())
        aliases = [a.strip() for a in (row.get("aliases") or "").split(";") if a.strip()]
        for name in [sci, *aliases]:
            out[name.lower()] = species
    return out


def available_regions() -> list[str]:
    return sorted(p.stem for p in REGIONS_DIR.glob("*.csv"))
