import json
import threading
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import numpy as np
import pytest

from gibbird.calibration import Calibration
from gibbird.config import CamConfig
from gibbird.names import load_region, region_path
from gibbird.server import make_server, updated_calibration
from gibbird.store import Store
from gibbird.watcher import BirdWatcher
from test_core import FakeClassifier, _frames

# A railing seen at an angle: image corners of a 300 x 100 cm rectangle.
IMG = [(0.1, 0.3), (0.9, 0.2), (0.85, 0.8), (0.15, 0.7)]
WORLD = [(0, 100), (300, 100), (300, 0), (0, 0)]


def test_homography_roundtrip_and_size():
    cal = Calibration(IMG, WORLD)
    assert cal.calibrated
    assert np.allclose(cal.to_world(IMG), WORLD, atol=1e-3)
    assert np.allclose(cal.to_image(WORLD), IMG, atol=1e-9)
    # a box spanning the full bottom edge of the railing is ~300 cm wide
    size = cal.size_cm((0.15, 0.6, 0.70, 0.1))
    assert 250 < size < 330


def test_degenerate_points_rejected():
    with pytest.raises(ValueError):
        Calibration([(0.1, 0.1), (0.2, 0.2), (0.3, 0.3), (0.4, 0.4)], WORLD)
    with pytest.raises(ValueError):
        Calibration(IMG, WORLD[:3])


def test_zones_in_world_survive_camera_move():
    cal = Calibration(IMG, WORLD).with_image_zones([[(0.1, 0.3), (0.5, 0.25), (0.5, 0.75), (0.15, 0.7)]])
    assert cal.zones_space == "world"
    area = cal.zone_areas_m2()[0]
    # camera nudged: every image point shifts right by 0.05; redo reference points only
    moved = [(x + 0.05, y) for x, y in IMG]
    new = updated_calibration(cal, {"image_points": moved, "world_points": WORLD})
    assert new.zones == cal.zones and new.zone_areas_m2()[0] == pytest.approx(area)
    assert np.allclose(new.zones_image()[0], np.float64(cal.zones_image()[0]) + [0.05, 0], atol=1e-6)


def test_accepts_by_zone_and_size():
    cal = Calibration(IMG, WORLD, min_size_cm=5, max_size_cm=60).with_image_zones(
        [[(0.1, 0.3), (0.5, 0.25), (0.5, 0.75), (0.15, 0.7)]]
    )
    assert cal.accepts((0.30, 0.50, 0.04, 0.05))[0]           # bird-sized, inside
    assert cal.accepts((0.70, 0.50, 0.04, 0.05)) == (False, "outside zones")
    ok, why = cal.accepts((0.15, 0.30, 0.30, 0.38))            # person-sized, inside
    assert not ok and why.startswith("size")


def test_image_zones_without_calibration():
    cal = Calibration(zones=[[(0, 0), (0.5, 0), (0.5, 1), (0, 1)]])
    assert cal.accepts((0.1, 0.4, 0.05, 0.05))[0]
    assert not cal.accepts((0.7, 0.4, 0.05, 0.05))[0]
    mask = cal.motion_mask((100, 200))
    assert mask[50, 50] == 255 and mask[50, 150] == 0


def test_world_zones_need_points():
    cal = Calibration(IMG, WORLD).with_image_zones([[(0.2, 0.3), (0.4, 0.3), (0.4, 0.6)]])
    with pytest.raises(ValueError, match="cm"):
        updated_calibration(cal, {"image_points": IMG[:2], "world_points": WORLD[:2]})


def _watcher(tmp_path, cal):
    tmp_path.mkdir(parents=True, exist_ok=True)
    region = load_region(region_path("gothenburg"))
    return BirdWatcher(CamConfig(), FakeClassifier(), region, Store(tmp_path / "v.db"), tmp_path / "p", cal)


def test_watcher_ignores_motion_outside_zone(tmp_path):
    # the synthetic bird moves around x = 0.2..0.35, y = 0.37..0.52
    outside = Calibration(zones=[[(0.6, 0), (1, 0), (1, 1), (0.6, 1)]])
    wa = _watcher(tmp_path / "a", outside)
    assert not any(wa.process(f) for f in _frames(1000, 40, bird_from=20))
    inside = Calibration(zones=[[(0, 0), (0.6, 0), (0.6, 1), (0, 1)]])
    wb = _watcher(tmp_path / "b", inside)
    assert any(wb.process(f) for f in _frames(1000, 40, bird_from=20))


def test_calibration_api(tmp_path):
    w = _watcher(tmp_path, Calibration())
    path = tmp_path / "cal.json"
    srv = make_server(w.store, w.region, w.photos_dir, "127.0.0.1", 0, w, path)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_address[1]}"

    def post(body):
        req = Request(f"{base}/api/calibration", json.dumps(body).encode(), {"Content-Type": "application/json"})
        return json.load(urlopen(req))

    try:
        assert b"Camera calibration" in urlopen(f"{base}/calibrate").read()
        d = post({"image_points": IMG, "world_points": WORLD, "zones_image": [[(0.2, 0.3), (0.4, 0.3), (0.4, 0.6)]]})
        assert d["calibrated"] and d["zones_space"] == "world" and d["grid"]
        assert w.calibration.calibrated and Calibration.load(path).zones == w.calibration.zones
        with pytest.raises(HTTPError) as e:
            post({"image_points": IMG, "world_points": WORLD[:3]})
        assert e.value.code == 400
    finally:
        srv.shutdown()
