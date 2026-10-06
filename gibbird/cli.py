"""Command line entry point: `gibbird cam | frame | classify | demo`."""

from __future__ import annotations

import argparse
import logging
import random
import time
from datetime import datetime
from pathlib import Path

from . import config as config_mod
from .names import available_regions, load_labels, load_region, region_path

log = logging.getLogger("gibbird")


def cmd_cam(cfg: config_mod.Config, args) -> None:
    from .calibration import Calibration
    from .camera import open_source
    from .classifier import TFLiteClassifier
    from .server import make_server, serve_in_background
    from .store import Store
    from .watcher import BirdWatcher

    c = cfg.cam
    labels = load_labels(cfg.path(c.labels))
    region = load_region(region_path(c.region))
    data_dir = cfg.path(c.data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    store = Store(data_dir / "visits.db")
    photos = data_dir / "photos"

    cal_path = cfg.path(c.calibration)
    calibration = Calibration.load(cal_path)
    log.info(
        "calibration: %s, %d zone(s)",
        f"{len(calibration.image_points)} reference points" if calibration.calibrated else "none",
        len(calibration.zones),
    )
    watcher = BirdWatcher(c, TFLiteClassifier(cfg.path(c.model), labels), region, store, photos, calibration)

    server = make_server(store, region, photos, c.http_host, c.http_port, watcher, cal_path)
    serve_in_background(server)
    log.info("API on http://%s:%d  (region: %s, %d species)", c.http_host, c.http_port, c.region, len(set(region.values())))
    for frame in open_source(c):
        watcher.process(frame)


def cmd_frame(cfg: config_mod.Config, args) -> None:
    from .display import PreviewDisplay, make_display
    from .frame_app import FrameApp

    f = cfg.frame
    display = PreviewDisplay(args.preview) if args.preview else make_display(f.display, f.rotation, f.saturation)
    app = FrameApp(f, display)
    if args.once:
        app.tick()
    else:
        app.run_forever()


def cmd_classify(cfg: config_mod.Config, args) -> None:
    import numpy as np
    from PIL import Image

    from .classifier import TFLiteClassifier

    c = cfg.cam
    region = load_region(region_path(c.region))
    clf = TFLiteClassifier(cfg.path(c.model), load_labels(cfg.path(c.labels)))
    for path in args.images:
        print(path)
        for p in clf.classify(np.asarray(Image.open(path).convert("RGB")), top_k=5):
            sp = region.get(p.sci.lower())
            local = f" = {sp.local or sp.en}" if sp else "  (not in region list)"
            print(f"  {p.score:5.2f}  {p.sci} ({p.common}){local}")


def cmd_demo(cfg: config_mod.Config, args) -> None:
    """Render a poster from made-up sightings, to tweak the design without hardware."""
    from PIL import Image, ImageDraw

    from .display import PreviewDisplay
    from .render import Tile, format_date, render_poster

    region = load_region(region_path(cfg.cam.region))
    species = sorted(set(region.values()), key=lambda s: s.sci)
    rng = random.Random(args.seed)
    photos = sorted(Path(args.photos).glob("*.jp*g")) if args.photos else []
    now = time.time()
    tiles = []
    for i, sp in enumerate(rng.sample(species, min(args.count, len(species)))):
        if photos:
            img = Image.open(photos[i % len(photos)])
        else:
            img = Image.new("RGB", (400, 400), tuple(rng.randrange(60, 200) for _ in range(3)))
            ImageDraw.Draw(img).ellipse([110, 110, 290, 290], fill=(240, 230, 210))
        name = sp.local if cfg.frame.names == "local" and sp.local else sp.en
        tiles.append(Tile(name, rng.randint(1, 9), now - rng.randint(0, 6 * 3600), img))
    tiles.sort(key=lambda t: -t.visits)
    f = cfg.frame
    img = render_poster(tiles, f.title, f.subtitle, format_date(datetime.now(), f.language),
                        max_tiles=f.max_tiles, lang=f.language, size=tuple(args.size or f.poster_size))
    PreviewDisplay(args.out, simulate=not args.no_simulate).show(img)
    print(f"wrote {args.out}")


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(prog="gibbird", description="Balcony bird camera + e-ink frame")
    ap.add_argument("-c", "--config", help="TOML config file (default: built-in defaults)")
    ap.add_argument("-v", "--verbose", action="store_true")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("cam", help="run the balcony camera + API (camera Pi)")

    p = sub.add_parser("frame", help="drive the e-ink frame (display Pi)")
    p.add_argument("--once", action="store_true", help="update once and exit")
    p.add_argument("--preview", metavar="PNG", help="write a PNG instead of using the panel")

    p = sub.add_parser("classify", help="classify still images (test the model)")
    p.add_argument("images", nargs="+")

    p = sub.add_parser("demo", help="render a poster with fake data")
    p.add_argument("--out", default="poster.png")
    p.add_argument("--count", type=int, default=6)
    p.add_argument("--photos", help="folder of bird photos to use in tiles")
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--no-simulate", action="store_true", help="skip the 6-colour dither preview")
    p.add_argument("--size", type=int, nargs=2, metavar=("W", "H"), help="poster size, e.g. 480 800")

    sub.add_parser("regions", help="list bundled region species lists")

    args = ap.parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    cfg = config_mod.load(args.config)
    if args.cmd == "regions":
        print("\n".join(available_regions()))
        return
    {"cam": cmd_cam, "frame": cmd_frame, "classify": cmd_classify, "demo": cmd_demo}[args.cmd](cfg, args)


if __name__ == "__main__":
    main()
