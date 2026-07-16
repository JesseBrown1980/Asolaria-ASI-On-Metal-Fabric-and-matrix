#!/usr/bin/env python3
"""Feature, geometry, nullspace, model-tournament, and GNN-shadow tools."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

import cv2
import numpy as np


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path, block: int = 4 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(block):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json(obj: Any) -> bytes:
    return json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def round_float(value: Any, digits: int = 9):
    if isinstance(value, (np.floating, float)):
        number = float(value)
        return round(number, digits) if math.isfinite(number) else None
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, dict):
        return {key: round_float(item, digits) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [round_float(item, digits) for item in value]
    return value


def image_entropy(gray: np.ndarray) -> float:
    histogram = np.bincount(gray.ravel(), minlength=256).astype(np.float64)
    probability = histogram[histogram > 0] / gray.size
    return float(-(probability * np.log2(probability)).sum())


def phash(gray: np.ndarray) -> str:
    small = cv2.resize(gray, (32, 32), interpolation=cv2.INTER_AREA).astype(np.float32)
    dct = cv2.dct(small)[:8, :8]
    median = np.median(dct[1:])
    bits = (dct > median).ravel()
    value = 0
    for bit in bits:
        value = (value << 1) | int(bit)
    return f"{value:016x}"


def resize_analysis(frame: np.ndarray, max_width: int = 640) -> np.ndarray:
    height, width = frame.shape[:2]
    if width <= max_width:
        return frame
    scale = max_width / width
    return cv2.resize(
        frame,
        (max_width, max(1, round(height * scale))),
        interpolation=cv2.INTER_AREA,
    )


def bright_components(gray: np.ndarray) -> list[dict[str, Any]]:
    threshold = max(220.0, float(np.percentile(gray, 99.5)))
    mask = (gray >= threshold).astype(np.uint8) * 255
    count, _, stats, centroids = cv2.connectedComponentsWithStats(mask, 8)
    output = []
    area_minimum = max(2, gray.size // 200000)
    for index in range(1, count):
        x, y, width, height, area = [int(item) for item in stats[index]]
        if area < area_minimum:
            continue
        center_x, center_y = [float(item) for item in centroids[index]]
        output.append(
            {
                "x": center_x / gray.shape[1],
                "y": center_y / gray.shape[0],
                "w": width / gray.shape[1],
                "h": height / gray.shape[0],
                "area": area / gray.size,
                "threshold": threshold,
            }
        )
    output.sort(key=lambda row: row["area"], reverse=True)
    return output[:32]


def line_features(gray: np.ndarray) -> list[dict[str, Any]]:
    edges = cv2.Canny(gray, 60, 160)
    minimum_length = max(12, min(gray.shape) // 12)
    lines = cv2.HoughLinesP(
        edges,
        1,
        np.pi / 180,
        threshold=30,
        minLineLength=minimum_length,
        maxLineGap=8,
    )
    output = []
    if lines is not None:
        height, width = gray.shape
        for raw in lines[:128]:
            x1, y1, x2, y2 = map(int, raw[0])
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


def ellipse_features(gray: np.ndarray) -> list[dict[str, Any]]:
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blur, 40, 130)
    contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
    height, width = gray.shape
    output = []
    for contour in contours:
        if len(contour) < 20:
            continue
        area = abs(cv2.contourArea(contour))
        if area < max(20, gray.size * 0.00008) or area > gray.size * 0.8:
            continue
        try:
            (center_x, center_y), (axis_a, axis_b), angle = cv2.fitEllipse(contour)
        except cv2.error:
            continue
        major = max(axis_a, axis_b)
        minor = min(axis_a, axis_b)
        if major <= 0 or minor / major < 0.08:
            continue
        perimeter = cv2.arcLength(contour, True)
        ellipse_area = math.pi * (axis_a / 2) * (axis_b / 2)
        fill = area / ellipse_area if ellipse_area else 0
        output.append(
            {
                "cx": center_x / width,
                "cy": center_y / height,
                "major": major / max(width, height),
                "minor": minor / max(width, height),
                "axis_ratio": minor / major,
                "eccentricity": math.sqrt(max(0, 1 - (minor / major) ** 2)),
                "angle_deg": float(angle),
                "area_fraction": area / gray.size,
                "fill_ratio": fill,
                "perimeter_norm": perimeter / (2 * (width + height)),
            }
        )
    output.sort(key=lambda row: row["area_fraction"], reverse=True)
    return output[:24]


def frame_statistics(gray: np.ndarray) -> dict[str, Any]:
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    edges = cv2.Canny(gray, 60, 160)
    return {
        "mean": float(gray.mean()),
        "std": float(gray.std()),
        "entropy": image_entropy(gray),
        "blur_laplacian_var": float(laplacian.var()),
        "dark_fraction": float(np.mean(gray < 10)),
        "bright_fraction": float(np.mean(gray > 245)),
        "saturated_fraction": float(np.mean(gray >= 254)),
        "edge_fraction": float(np.mean(edges > 0)),
        "phash": phash(gray),
    }


def orb_pair_geometry(first: np.ndarray, second: np.ndarray) -> dict[str, Any]:
    orb = cv2.ORB_create(nfeatures=700, fastThreshold=10)
    keypoints_1, descriptors_1 = orb.detectAndCompute(first, None)
    keypoints_2, descriptors_2 = orb.detectAndCompute(second, None)
    result = {
        "keypoints_1": len(keypoints_1),
        "keypoints_2": len(keypoints_2),
        "matches": 0,
        "homography_inlier_ratio": None,
        "homography_median_error_px": None,
        "fundamental_inlier_ratio": None,
        "fundamental_median_sampson": None,
    }
    if descriptors_1 is None or descriptors_2 is None:
        return result
    matches = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True).match(
        descriptors_1, descriptors_2
    )
    matches = sorted(matches, key=lambda item: item.distance)[:400]
    result["matches"] = len(matches)
    if len(matches) < 8:
        return result
    points_1 = np.float32([keypoints_1[item.queryIdx].pt for item in matches])
    points_2 = np.float32([keypoints_2[item.trainIdx].pt for item in matches])

    homography, homography_mask = cv2.findHomography(points_1, points_2, cv2.RANSAC, 3.0)
    if homography is not None and homography_mask is not None:
        predicted = cv2.perspectiveTransform(
            points_1.reshape(-1, 1, 2), homography
        ).reshape(-1, 2)
        error = np.linalg.norm(predicted - points_2, axis=1)
        mask = homography_mask.ravel().astype(bool)
        result["homography_inlier_ratio"] = float(mask.mean())
        result["homography_median_error_px"] = (
            float(np.median(error[mask])) if mask.any() else None
        )

    fundamental, fundamental_mask = cv2.findFundamentalMat(
        points_1, points_2, cv2.FM_RANSAC, 1.5, 0.99
    )
    if (
        fundamental is not None
        and np.asarray(fundamental).shape == (3, 3)
        and fundamental_mask is not None
    ):
        homogeneous_1 = np.column_stack([points_1, np.ones(len(points_1))])
        homogeneous_2 = np.column_stack([points_2, np.ones(len(points_2))])
        fx1 = homogeneous_1 @ fundamental.T
        ftx2 = homogeneous_2 @ fundamental
        numerator = np.sum(homogeneous_2 * fx1, axis=1) ** 2
        denominator = (
            fx1[:, 0] ** 2
            + fx1[:, 1] ** 2
            + ftx2[:, 0] ** 2
            + ftx2[:, 1] ** 2
            + 1e-12
        )
        sampson = numerator / denominator
        mask = fundamental_mask.ravel().astype(bool)
        result["fundamental_inlier_ratio"] = float(mask.mean())
        result["fundamental_median_sampson"] = (
            float(np.median(sampson[mask])) if mask.any() else None
        )
    return result


def stable_tracks(frames: list[np.ndarray], max_points: int = 180) -> dict[str, Any]:
    if len(frames) < 3:
        return {"track_count": 0, "frames": len(frames), "measurement": None}
    first = frames[0]
    points = cv2.goodFeaturesToTrack(
        first,
        maxCorners=max_points,
        qualityLevel=0.01,
        minDistance=5,
        blockSize=5,
    )
    if points is None:
        return {"track_count": 0, "frames": len(frames), "measurement": None}
    active = points.astype(np.float32)
    histories = [active.reshape(-1, 2).copy()]
    previous = first
    for gray in frames[1:]:
        following, status, _ = cv2.calcOpticalFlowPyrLK(
            previous,
            gray,
            active,
            None,
            winSize=(21, 21),
            maxLevel=3,
            criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 30, 0.01),
        )
        if following is None or status is None:
            break
        backward, backward_status, _ = cv2.calcOpticalFlowPyrLK(
            gray,
            previous,
            following,
            None,
            winSize=(21, 21),
            maxLevel=3,
            criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 30, 0.01),
        )
        if backward is None or backward_status is None:
            break
        forward_backward = np.linalg.norm(
            active.reshape(-1, 2) - backward.reshape(-1, 2), axis=1
        )
        good = (
            (status.ravel() == 1)
            & (backward_status.ravel() == 1)
            & (forward_backward < 1.5)
        )
        if good.sum() < 4:
            break
        histories = [history[good] for history in histories]
        active = following[good].reshape(-1, 1, 2)
        histories.append(active.reshape(-1, 2).copy())
        previous = gray

    frame_count = len(histories)
    track_count = len(histories[-1]) if histories else 0
    if frame_count < 3 or track_count < 4:
        return {"track_count": track_count, "frames": frame_count, "measurement": None}

    coordinates = np.stack(histories, axis=0)
    measurement = np.concatenate(
        [coordinates[:, :, 0], coordinates[:, :, 1]], axis=0
    )
    centered = measurement - measurement.mean(axis=1, keepdims=True)
    singular_values = np.linalg.svd(centered, compute_uv=False)
    energy = float(np.sum(singular_values * singular_values)) or 1.0
    rank_2_residual = (
        float(np.sum(singular_values[2:] ** 2) / energy)
        if len(singular_values) > 2
        else 0.0
    )
    rank_3_residual = (
        float(np.sum(singular_values[3:] ** 2) / energy)
        if len(singular_values) > 3
        else 0.0
    )
    motion = np.diff(coordinates, axis=0)
    return {
        "track_count": track_count,
        "frames": frame_count,
        "measurement": {
            "singular_values": [float(value) for value in singular_values[:12]],
            "rank2_residual": rank_2_residual,
            "rank3_residual": rank_3_residual,
            "mean_motion_px": float(np.mean(np.linalg.norm(motion, axis=2))),
            "median_motion_px": float(np.median(np.linalg.norm(motion, axis=2))),
            "coords": coordinates.tolist(),
        },
    }


def complexity_score(
    residual: float | None, observations: int, parameters: int
) -> float | None:
    if residual is None or observations <= parameters + 1 or residual < 0:
        return None
    rss = max(residual * residual * observations, 1e-12)
    return float(
        observations * math.log(rss / observations)
        + parameters * math.log(observations)
    )


def model_tournament(
    pair_rows: list[dict[str, Any]],
    track: dict[str, Any],
    ellipses: list[list[dict[str, Any]]],
    brights: list[list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    homography_errors = [
        row["homography_median_error_px"]
        for row in pair_rows
        if row.get("homography_median_error_px") is not None
    ]
    fundamental_errors = [
        row["fundamental_median_sampson"]
        for row in pair_rows
        if row.get("fundamental_median_sampson") is not None
    ]
    homography_inliers = [
        row["homography_inlier_ratio"]
        for row in pair_rows
        if row.get("homography_inlier_ratio") is not None
    ]
    observations = max(1, sum(row.get("matches", 0) for row in pair_rows))
    median_homography = (
        float(np.median(homography_errors)) if homography_errors else None
    )
    measurement = track.get("measurement") or {}
    rank_3 = measurement.get("rank3_residual")
    rank_2 = measurement.get("rank2_residual")

    ellipse_frames = [row for row in ellipses if row]
    ellipse_axes = [row[0]["axis_ratio"] for row in ellipse_frames]
    ellipse_centers = (
        np.array([[row[0]["cx"], row[0]["cy"]] for row in ellipse_frames])
        if ellipse_frames
        else np.empty((0, 2))
    )
    ellipse_smoothness = (
        float(np.mean(np.linalg.norm(np.diff(ellipse_centers, axis=0), axis=1)))
        if len(ellipse_centers) > 1
        else None
    )
    double_conics = []
    for row in ellipse_frames:
        if len(row) < 2:
            continue
        first, second = row[0], row[1]
        center_distance = math.hypot(
            first["cx"] - second["cx"], first["cy"] - second["cy"]
        )
        angle_distance = abs(first["angle_deg"] - second["angle_deg"]) % 180
        if center_distance < 0.04 and angle_distance < 20:
            double_conics.append(
                {
                    "center_dist": center_distance,
                    "radius_ratio": second["major"] / max(first["major"], 1e-9),
                }
            )

    models = []

    def add(name, status, residual, parameters, model_observations, evidence):
        models.append(
            {
                "model": name,
                "status": status,
                "residual": residual,
                "parameters": parameters,
                "observations": model_observations,
                "bic_like": complexity_score(
                    residual, model_observations, parameters
                ),
                "evidence": evidence,
                "global_selection": "HELD_UNTIL_COMMON_HELDOUT_PIXEL_LOSS",
            }
        )

    add(
        "C0_SENSOR_OR_OPTICAL_ARTIFACT",
        "MEASURED_CANDIDATE",
        None if not brights else float(np.std([len(item) for item in brights])),
        4,
        len(brights),
        {
            "bright_count_variance": (
                None if not brights else float(np.var([len(item) for item in brights]))
            ),
            "note": "low count variance alone does not prove a lens artifact",
        },
    )
    add(
        "C1_PLANAR_HOMOGRAPHY",
        "MEASURED_CANDIDATE"
        if median_homography is not None
        else "HELD_INSUFFICIENT_MATCHES",
        median_homography,
        8,
        observations,
        {
            "median_inlier_ratio": (
                float(np.median(homography_inliers)) if homography_inliers else None
            )
        },
    )
    add(
        "C2_REGULAR_TETRAHEDRON",
        "HELD_AUTOMATIC_VERTEX_CORRESPONDENCE_UNRESOLVED",
        None,
        18,
        track.get("track_count", 0),
        {"required": "four persistent vertex identities + camera calibration + held-out PnP"},
    )
    add(
        "C3_UNCONSTRAINED_RIGID_LATTICE",
        "MEASURED_CANDIDATE"
        if rank_3 is not None
        else "HELD_INSUFFICIENT_TRACKS",
        math.sqrt(rank_3) if rank_3 is not None else None,
        3 * track.get("track_count", 0) + 6 * track.get("frames", 0),
        track.get("track_count", 0) * track.get("frames", 0) * 2,
        {
            "rank2_residual": rank_2,
            "rank3_residual": rank_3,
            "singular_values": measurement.get("singular_values"),
        },
    )
    add(
        "C4_SQUARE_PYRAMID",
        "HELD_AUTOMATIC_VERTEX_CORRESPONDENCE_UNRESOLVED",
        None,
        21,
        track.get("track_count", 0),
        {"required": "five persistent vertex identities"},
    )
    add(
        "C5_TRIANGULAR_PRISM",
        "HELD_AUTOMATIC_VERTEX_CORRESPONDENCE_UNRESOLVED",
        None,
        24,
        track.get("track_count", 0),
        {"required": "six persistent vertex identities"},
    )
    add(
        "C6_CYLINDRICAL_OR_PLANAR_CIRCLE_CORE",
        "MEASURED_CANDIDATE"
        if len(ellipse_frames) >= 5
        else "HELD_INSUFFICIENT_CONICS",
        float(np.std(ellipse_axes)) if len(ellipse_axes) >= 5 else None,
        7,
        len(ellipse_axes),
        {
            "ellipse_frames": len(ellipse_frames),
            "axis_ratio_mean": (
                float(np.mean(ellipse_axes)) if ellipse_axes else None
            ),
            "axis_ratio_std": (
                float(np.std(ellipse_axes)) if ellipse_axes else None
            ),
            "center_step_mean": ellipse_smoothness,
            "boundary": (
                "ellipse consistency does not distinguish a planar circle from "
                "a cylinder by itself"
            ),
        },
    )
    add(
        "C7_TOROIDAL_CORE",
        "MEASURED_CANDIDATE"
        if len(double_conics) >= 5
        else "HELD_INSUFFICIENT_DOUBLE_CONICS",
        (
            float(np.std([item["radius_ratio"] for item in double_conics]))
            if len(double_conics) >= 5
            else None
        ),
        10,
        len(double_conics),
        {
            "double_conic_frames": len(double_conics),
            "mean_center_delta": (
                float(np.mean([item["center_dist"] for item in double_conics]))
                if double_conics
                else None
            ),
            "boundary": (
                "requires stable inner/outer contours and self-occlusion; "
                "no mechanism inferred"
            ),
        },
    )
    return models


def gnn_shadow(
    frame_rows: list[dict[str, Any]],
    pair_rows: list[dict[str, Any]],
    layers: int = 8,
) -> dict[str, Any]:
    if not frame_rows:
        return {"status": "HELD_EMPTY_GRAPH"}
    values = []
    for row in frame_rows:
        stats = row["stats"]
        values.append(
            [
                stats["mean"] / 255,
                stats["std"] / 128,
                stats["entropy"] / 8,
                math.log1p(stats["blur_laplacian_var"]) / 15,
                stats["dark_fraction"],
                stats["bright_fraction"] * 20,
                stats["edge_fraction"] * 5,
                (row.get("bright_count") or 0) / 20,
                (row.get("ellipse_count") or 0) / 10,
                (row.get("line_count") or 0) / 50,
            ]
        )
    features = np.asarray(values, dtype=np.float64)
    mean = features.mean(axis=0)
    deviation = features.std(axis=0)
    deviation[deviation < 1e-9] = 1
    initial = np.tanh((features - mean) / deviation)

    def run(direction: str):
        hidden = initial.copy()
        node_count = len(hidden)
        order = range(node_count) if direction == "forward" else range(node_count - 1, -1, -1)
        for _ in range(layers):
            next_hidden = np.empty_like(hidden)
            for index in order:
                neighbors = []
                if index > 0:
                    neighbors.append(hidden[index - 1])
                if index + 1 < node_count:
                    neighbors.append(hidden[index + 1])
                if index > 1:
                    neighbors.append(hidden[index - 2])
                if index + 2 < node_count:
                    neighbors.append(hidden[index + 2])
                neighbor_mean = np.mean(neighbors, axis=0) if neighbors else hidden[index]
                directional = (
                    hidden[index - 1] - hidden[index + 1]
                    if 0 < index < node_count - 1
                    else np.zeros_like(hidden[index])
                )
                if direction == "reverse":
                    directional = -directional
                next_hidden[index] = np.tanh(
                    0.55 * hidden[index]
                    + 0.35 * neighbor_mean
                    + 0.10 * directional
                )
            hidden = next_hidden
        return hidden

    forward = run("forward")
    reverse = run("reverse")
    return {
        "status": "MEASURED_DETERMINISTIC_GNN_SHADOW_NOT_TRAINED",
        "nodes": len(frame_rows),
        "features": initial.shape[1],
        "layers": layers,
        "forward_sha256": sha256_bytes(forward.astype(">f4").tobytes()),
        "reverse_sha256": sha256_bytes(reverse.astype(">f4").tobytes()),
        "forward_reverse_mean_abs": float(np.mean(np.abs(forward - reverse))),
        "embedding_mean": [float(item) for item in ((forward + reverse) / 2).mean(axis=0)],
        "pair_rows_supplied": len(pair_rows),
    }
