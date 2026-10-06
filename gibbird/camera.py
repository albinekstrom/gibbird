"""Frame sources: the Pi camera, or OpenCV (USB webcam / video file) for testing."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass

import numpy as np

from .config import CamConfig


@dataclass
class Frame:
    lores: np.ndarray  # grayscale, for motion detection
    main: Callable[[], np.ndarray]  # full-resolution RGB, fetched only when needed
    t: float  # timestamp in seconds


def open_source(cfg: CamConfig) -> Iterator[Frame]:
    if cfg.source == "picamera2":
        return _picamera2_frames(cfg)
    if cfg.source.startswith("opencv:"):
        return _opencv_frames(int(cfg.source.split(":", 1)[1]), cfg, is_file=False)
    return _opencv_frames(cfg.source, cfg, is_file=True)


def _picamera2_frames(cfg: CamConfig) -> Iterator[Frame]:
    from picamera2 import Picamera2

    cam = Picamera2()
    config = cam.create_video_configuration(
        # Picamera2's "BGR888" gives arrays in R, G, B order.
        main={"size": tuple(cfg.main_size), "format": "BGR888"},
        lores={"size": tuple(cfg.lores_size), "format": "YUV420"},
        controls={"FrameRate": cfg.framerate},
        buffer_count=3,  # a full 12 MP RGB frame is 36 MB; keep camera memory (CMA) use low
    )
    cam.configure(config)
    cam.start()
    try:
        from libcamera import controls

        cam.set_controls({"AfMode": controls.AfModeEnum.Continuous})
    except Exception:
        pass  # camera without autofocus
    w, h = cfg.lores_size
    try:
        while True:
            req = cam.capture_request()
            try:
                gray = req.make_array("lores")[:h, :w]
                # The consumer must call main() before asking for the next frame.
                yield Frame(gray, lambda r=req: r.make_array("main"), time.time())
            finally:
                req.release()
    finally:
        cam.stop()


def _opencv_frames(src: int | str, cfg: CamConfig, is_file: bool) -> Iterator[Frame]:
    import cv2

    cap = cv2.VideoCapture(src)
    if not cap.isOpened():
        raise RuntimeError(f"cannot open video source {src!r}")
    if not is_file:
        # MJPG is needed for full HD at a useful frame rate over USB 2.0.
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, cfg.main_size[0])
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, cfg.main_size[1])
        cap.set(cv2.CAP_PROP_FPS, cfg.framerate)
        cap.set(cv2.CAP_PROP_AUTOFOCUS, 1)
        # Always hand us the newest frame: decoding 4K MJPEG is slower than the camera.
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        logging.getLogger(__name__).info(
            "USB camera running at %dx%d",
            cap.get(cv2.CAP_PROP_FRAME_WIDTH),
            cap.get(cv2.CAP_PROP_FRAME_HEIGHT),
        )
    start = time.time()
    try:
        while True:
            ok, bgr = cap.read()
            if not ok:
                if is_file:
                    return
                time.sleep(0.5)
                continue
            rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
            gray = cv2.cvtColor(cv2.resize(bgr, tuple(cfg.lores_size)), cv2.COLOR_BGR2GRAY)
            # Use the video's own clock for files so playback speed doesn't matter.
            t = start + cap.get(cv2.CAP_PROP_POS_MSEC) / 1000 if is_file else time.time()
            yield Frame(gray, lambda rgb=rgb: rgb, t)
    finally:
        cap.release()
