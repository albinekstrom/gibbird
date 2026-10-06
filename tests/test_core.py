import json
import threading
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import urlopen

import numpy as np
import pytest
from PIL import Image

from gibbird.camera import Frame
from gibbird.classifier import Prediction
from gibbird.config import CamConfig, FrameConfig, load
from gibbird.frame_app import FrameApp, in_quiet_hours
from gibbird.names import load_labels, load_region, region_path
from gibbird.render import SIZE, Tile, render_poster
from gibbird.server import make_server
from gibbird.store import Store
from gibbird.watcher import BirdWatcher


def test_labels_with_and_without_index(tmp_path):
    p = tmp_path / "l.txt"
    p.write_text("Parus major (Great Tit)\nbackground\n")
    labels = load_labels(p)
    assert labels[0].sci == "Parus major" and labels[0].common == "Great Tit"
    assert labels[1].is_background
    p.write_text("5  Pica pica (Eurasian Magpie)\n")
    assert load_labels(p)[5].common == "Eurasian Magpie"


def test_gothenburg_region_and_aliases():
    region = load_region(region_path("gothenburg"))
    assert region["parus major"].local == "Talgoxe"
    assert region["corvus corone"].sci == "Corvus cornix"  # carrion crow counted as hooded crow


def test_region_names_exist_in_model_labels():
    labels_file = Path(__file__).parent.parent / "models" / "inat_bird_labels.txt"
    if not labels_file.exists():
        pytest.skip("model not downloaded")
    model = {lbl.sci.lower() for lbl in load_labels(labels_file).values()}
    region = load_region(region_path("gothenburg"))
    reachable = {sp.sci for name, sp in region.items() if name in model}
    assert {sp.sci for sp in region.values()} - reachable == set()


def test_config_rejects_unknown_keys(tmp_path):
    p = tmp_path / "c.toml"
    p.write_text('[cam]\nregon = "x"\n')
    with pytest.raises(ValueError, match="regon"):
        load(p)
    p.write_text('[frame]\nquiet_hours = [22, 6]\n')
    assert load(p).frame.quiet_hours == (22, 6)


def test_store_summary_picks_best_photo(tmp_path):
    s = Store(tmp_path / "v.db")
    a = s.open_visit("Parus major", 100, 0.6, "a.jpg")
    s.extend_visit(a, 150, 0.7)
    s.open_visit("Parus major", 500, 0.9, "b.jpg")
    s.open_visit("Pica pica", 600, 0.8, "c.jpg")
    s.open_visit("Pica pica", 10, 0.99, "old.jpg")  # before `since`
    rows = {r["sci"]: r for r in s.species_since(50)}
    assert rows["Parus major"]["visits"] == 2
    assert rows["Parus major"]["photo"] == "b.jpg"
    assert rows["Pica pica"]["visits"] == 1 and rows["Pica pica"]["photo"] == "c.jpg"


class FakeClassifier:
    def __init__(self, sci="Parus major", score=0.9):
        self.sci, self.score = sci, score

    def classify(self, rgb, top_k=3):
        return [Prediction(self.sci, "x", self.score)]


def _frames(t0, n, bird_from, step=0.5):
    """Static noisy background; a bright square appears from frame `bird_from` and moves."""
    rng = np.random.default_rng(0)
    bg = rng.integers(90, 110, (270, 480), dtype=np.uint8)
    for i in range(n):
        g = bg.copy()
        if i >= bird_from:
            x = 100 + (i - bird_from) * 3
            g[100:140, x : x + 40] = 250
        rgb = np.repeat(np.kron(g, np.ones((2, 2), np.uint8))[..., None], 3, axis=2)
        yield Frame(g, lambda rgb=rgb: rgb, t0 + i * step)


def _watcher(tmp_path, clf, **kw):
    cfg = CamConfig(**kw)
    region = load_region(region_path("gothenburg"))
    store = Store(tmp_path / "v.db")
    return BirdWatcher(cfg, clf, region, store, tmp_path / "photos"), store


def test_watcher_confirms_and_groups_visits(tmp_path):
    w, store = _watcher(tmp_path, FakeClassifier())
    hits = [s for f in _frames(1000, 40, bird_from=20) if (s := w.process(f))]
    assert hits and hits[0].new_visit and hits[0].species.local == "Talgoxe"
    assert all(not h.new_visit for h in hits[1:])
    # same bird again 10 minutes later -> a second visit
    w2_hits = [s for f in _frames(1600, 40, bird_from=20) if (s := w.process(f))]
    assert w2_hits and w2_hits[0].new_visit
    rows = store.species_since(0)
    assert rows[0]["visits"] == 2
    assert (tmp_path / "photos" / rows[0]["photo"]).exists()


@pytest.mark.parametrize(
    "clf",
    [FakeClassifier("Cardinalis cardinalis"), FakeClassifier(score=0.2), FakeClassifier("background")],
)
def test_watcher_rejects(tmp_path, clf):
    w, store = _watcher(tmp_path, clf)
    assert not any(w.process(f) for f in _frames(1000, 40, bird_from=20))
    assert store.species_since(0) == []


def test_watcher_allowlist_off_keeps_unknown_species(tmp_path):
    w, _ = _watcher(tmp_path, FakeClassifier("Cardinalis cardinalis"), allowlist_only=False)
    assert any(w.process(f) for f in _frames(1000, 40, bird_from=20))


@pytest.mark.parametrize("size", [SIZE, (480, 800)])
@pytest.mark.parametrize("n", [0, 1, 3, 7, 12])
def test_render_poster(n, size):
    photo = Image.new("RGB", (300, 200), (120, 80, 40))
    tiles = [Tile(f"Bird number {i} with a long name", i + 1, 1_700_000_000, photo if i % 2 else None) for i in range(n)]
    img = render_poster(tiles, "Seen Today", "Balcony Visitors", "Tuesday 6 October", size=size)
    assert img.size == size


def test_quiet_hours():
    assert in_quiet_hours(datetime(2026, 1, 1, 23, 30), (23, 7))
    assert in_quiet_hours(datetime(2026, 1, 1, 3, 0), (23, 7))
    assert not in_quiet_hours(datetime(2026, 1, 1, 12, 0), (23, 7))
    assert in_quiet_hours(datetime(2026, 1, 1, 1, 0), (0, 6))


class FakeDisplay:
    def __init__(self):
        self.shown = []

    def show(self, img):
        self.shown.append(img)


def test_frame_app_refreshes_only_on_change(tmp_path):
    photo = tmp_path / "p.jpg"
    Image.new("RGB", (50, 50)).save(photo)
    state = {"species": [{"sci": "Parus major", "en": "Great Tit", "local": "Talgoxe", "visits": 1,
                          "last_seen": 1_700_000_000, "photo": "p.jpg"}]}
    now = [datetime(2026, 10, 6, 12, 0)]

    def get(url):
        return photo.read_bytes() if "/photos/" in url else json.dumps(state).encode()

    disp = FakeDisplay()
    app = FrameApp(FrameConfig(min_refresh_minutes=15), disp, get=get, clock=lambda: now[0])
    assert app.tick() and len(disp.shown) == 1
    assert not app.tick()  # nothing changed
    state["species"][0]["visits"] = 2
    now[0] = datetime(2026, 10, 6, 12, 5)
    assert not app.tick()  # changed, but too soon
    now[0] = datetime(2026, 10, 6, 12, 20)
    assert app.tick() and len(disp.shown) == 2
    now[0] = datetime(2026, 10, 6, 23, 30)
    state["species"][0]["visits"] = 3
    assert not app.tick()  # quiet hours


def test_server(tmp_path):
    store = Store(tmp_path / "v.db")
    photos = tmp_path / "photos"
    photos.mkdir()
    Image.new("RGB", (10, 10)).save(photos / "a.jpg")
    store.open_visit("Parus major", datetime.now().timestamp(), 0.9, "a.jpg")
    srv = make_server(store, load_region(region_path("gothenburg")), photos, "127.0.0.1", 0)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_address[1]}"
    try:
        data = json.load(urlopen(f"{base}/api/summary?days=1"))
        assert data["species"][0]["local"] == "Talgoxe"
        assert urlopen(f"{base}/photos/a.jpg").read()[:2] == b"\xff\xd8"
        with pytest.raises(HTTPError):
            urlopen(f"{base}/photos/..%2Fv.db")
        assert b"Talgoxe" in urlopen(base + "/").read()
    finally:
        srv.shutdown()


def test_make_display_rejects_unknown_kind():
    from gibbird.display import make_display

    with pytest.raises(ValueError, match="unknown display"):
        make_display("lcd")
