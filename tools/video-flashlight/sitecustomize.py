"""Runner compatibility patches loaded automatically from PYTHONPATH.

OpenCV's HoughLinesP result is represented as ``(N, 1, 4)`` on some builds and
``(N, 4)`` on others. The original analyzer assumed only ``(N, 1, 4)``. Normalize
both forms without changing the measured feature definition.
"""
from __future__ import annotations

import math

import cv2
import numpy as np

try:
    import video_features
except Exception:  # pragma: no cover - only relevant before analysis deps exist
    video_features = None


def _line_features(gray: np.ndarray) -> list[dict]:
    edges = cv2.Canny(gray, 60, 160)
    minimum_length = max(12, min(gray.shape) // 12)
    detected = cv2.HoughLinesP(
        edges,
        1,
        np.pi / 180,
        threshold=30,
        minLineLength=minimum_length,
        maxLineGap=8,
    )
    output: list[dict] = []
    if detected is None:
        return output
    height, width = gray.shape
    for raw in detected[:128]:
        values = np.asarray(raw).reshape(-1)
        if values.size < 4:
            continue
        x1, y1, x2, y2 = map(int, values[:4])
        dx, dy = x2 - x1, y2 - y1
        output.append(
            {
                "x1": x1 / width,
                "y1": y1 / height,
                "x2": x2 / width,
                "y2": y2 / height,
                "length": math.hypot(dx, dy) / math.hypot(width, height),
                "angle": math.atan2(dy, dx),
            }
        )
    return output


if video_features is not None:
    video_features.line_features = _line_features
