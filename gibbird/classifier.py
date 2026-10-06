"""Bird species classifier (TensorFlow Lite / LiteRT)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import numpy as np
from PIL import Image

from .names import Label


@dataclass(frozen=True)
class Prediction:
    sci: str
    common: str
    score: float

    @property
    def is_background(self) -> bool:
        return self.sci.lower() == "background"


class Classifier(Protocol):
    def classify(self, rgb: np.ndarray, top_k: int = 3) -> list[Prediction]: ...


def _interpreter_class():
    try:
        from ai_edge_litert.interpreter import Interpreter
    except ImportError:
        try:
            from tflite_runtime.interpreter import Interpreter
        except ImportError:
            try:
                from tensorflow.lite import Interpreter
            except ImportError as e:
                raise ImportError("install a TFLite runtime: pip install ai-edge-litert") from e
    return Interpreter


class TFLiteClassifier:
    """Image classifier for a single-input, single-output TFLite model."""

    def __init__(self, model_path: str | Path, labels: dict[int, Label], num_threads: int = 4):
        self._it = _interpreter_class()(model_path=str(model_path), num_threads=num_threads)
        self._it.allocate_tensors()
        inp = self._it.get_input_details()[0]
        out = self._it.get_output_details()[0]
        self._in_index, self._out_index = inp["index"], out["index"]
        self._in_dtype = inp["dtype"]
        _, self._h, self._w, _ = inp["shape"]
        self._out_scale, self._out_zero = out["quantization"]
        self._labels = labels

    def classify(self, rgb: np.ndarray, top_k: int = 3) -> list[Prediction]:
        img = Image.fromarray(rgb).convert("RGB").resize((self._w, self._h), Image.BILINEAR)
        x = np.asarray(img)[None]
        if self._in_dtype == np.uint8:
            x = x.astype(np.uint8)
        elif self._in_dtype == np.int8:
            x = (x.astype(np.int16) - 128).astype(np.int8)
        else:  # float MobileNet-style models expect [-1, 1]
            x = x.astype(np.float32) / 127.5 - 1.0
        self._it.set_tensor(self._in_index, x)
        self._it.invoke()
        scores = self._it.get_tensor(self._out_index)[0].astype(np.float32)
        if self._out_scale:
            scores = (scores - self._out_zero) * self._out_scale
        top = np.argsort(scores)[::-1][:top_k]
        unknown = Label("unknown", "unknown")
        return [
            Prediction(self._labels.get(int(i), unknown).sci, self._labels.get(int(i), unknown).common, float(scores[i]))
            for i in top
        ]
