#!/usr/bin/env python3
"""Corrective entrypoint for analyze_video_cube.py.

OpenCV builds may return HoughLinesP rows as either ``(1, 4)`` or ``(4,)``.
The first flight assumed only the former and failed on the GitHub runner's flat
``numpy.int32`` row shape. This wrapper normalizes either form, patches the imported
symbol in the original analyzer, and preserves the failed receipt as development
evidence.
"""
from __future__ import annotations

import math

import cv2
import numpy as np

import analyze_video_cube as analyzer
import video_features


def line_features(gray: np.ndarray) -> list[dict]:
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


video_features.line_features = line_features
analyzer.line_features = line_features
analyzer.main()
