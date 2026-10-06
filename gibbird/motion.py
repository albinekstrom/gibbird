"""Cheap motion detection on the low-resolution stream, used to trigger the classifier."""

from __future__ import annotations

import cv2
import numpy as np

# (x, y, w, h), normalised to 0..1 of the frame
Box = tuple[float, float, float, float]


class MotionDetector:
    def __init__(
        self,
        threshold: int = 25,
        min_area: float = 0.002,
        max_area: float = 0.5,
        learn_rate: float = 0.05,
        warmup_frames: int = 15,
    ):
        self.threshold = threshold
        self.min_area = min_area
        self.max_area = max_area
        self.learn_rate = learn_rate
        self.warmup_frames = warmup_frames
        self._bg: np.ndarray | None = None
        self._seen = 0

    def update(self, gray: np.ndarray, mask: np.ndarray | None = None) -> list[Box]:
        """Feed one grayscale frame; return moving regions, largest first.

        `mask` (uint8, same size, 255 = watch) limits detection to the detection zones.
        """
        g = cv2.GaussianBlur(gray, (5, 5), 0).astype(np.float32)
        if self._bg is None or self._bg.shape != g.shape:
            self._bg, self._seen = g, 1
            return []
        diff = cv2.absdiff(g, self._bg)
        cv2.accumulateWeighted(g, self._bg, self.learn_rate)
        self._seen += 1
        if self._seen <= self.warmup_frames:
            return []

        moving = (diff > self.threshold).astype(np.uint8) * 255
        if mask is not None:
            moving = cv2.bitwise_and(moving, mask)
        moving = cv2.dilate(moving, None, iterations=2)
        contours, _ = cv2.findContours(moving, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        h, w = gray.shape[:2]
        boxes = []
        for c in contours:
            area = cv2.contourArea(c) / (w * h)
            # Huge regions are lighting changes (clouds, sun), not birds.
            if self.min_area <= area <= self.max_area:
                x, y, bw, bh = cv2.boundingRect(c)
                boxes.append((x / w, y / h, bw / w, bh / h))
        boxes.sort(key=lambda b: b[2] * b[3], reverse=True)
        return boxes


def square_crop(img: np.ndarray, box: Box, scale: float = 1.6, min_px: int = 224) -> np.ndarray:
    """Square crop around a normalised box, padded by `scale` and kept inside the image."""
    H, W = img.shape[:2]
    x, y, w, h = box
    cx, cy = (x + w / 2) * W, (y + h / 2) * H
    side = int(min(max(max(w * W, h * H) * scale, min_px), W, H))
    x0 = int(round(min(max(cx - side / 2, 0), W - side)))
    y0 = int(round(min(max(cy - side / 2, 0), H - side)))
    return img[y0 : y0 + side, x0 : x0 + side]
