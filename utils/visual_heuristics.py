from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from PIL import Image

try:
    import cv2
except Exception:  # pragma: no cover - covered by logic fallback
    cv2 = None


@dataclass(frozen=True)
class SpeckleHeuristicResult:
    flagged: bool
    cluster_count: int
    area_ratio: float
    dark_ratio: float
    reason: str | None
    bbox: tuple[int, int, int, int] | None = None
    confidence: str = "low"


@dataclass(frozen=True)
class SurfaceMarkHeuristicResult:
    flagged: bool
    line_count: int
    reason: str | None
    bbox: tuple[int, int, int, int] | None = None
    confidence: str = "low"


def detect_dark_speckles(image: Image.Image) -> SpeckleHeuristicResult:
    if cv2 is None:
        return SpeckleHeuristicResult(False, 0, 0.0, 0.0, None)

    rgb = np.array(image.convert("RGB"))
    if rgb.size == 0:
        return SpeckleHeuristicResult(False, 0, 0.0, 0.0, None)

    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    h, w = gray.shape
    if h < 80 or w < 80:
        return SpeckleHeuristicResult(False, 0, 0.0, 0.0, None)

    # Focus on the inner product area and ignore most of the background.
    x1 = int(w * 0.18)
    x2 = int(w * 0.82)
    y1 = int(h * 0.18)
    y2 = int(h * 0.82)
    roi = gray[y1:y2, x1:x2]

    blur = cv2.GaussianBlur(roi, (5, 5), 0)
    threshold = min(180, max(35, int(np.percentile(blur, 18))))
    dark_mask = (blur < threshold).astype(np.uint8)
    dark_ratio = float(dark_mask.mean())

    num_labels, _, stats, _ = cv2.connectedComponentsWithStats(dark_mask, connectivity=8)
    cluster_count = 0
    area_pixels = 0
    component_boxes: list[tuple[int, int, int, int]] = []
    component_records: list[tuple[int, int, tuple[int, int, int, int], int]] = []
    for idx in range(1, num_labels):
        area = int(stats[idx, cv2.CC_STAT_AREA])
        if 4 <= area <= 400:
            cluster_count += 1
            area_pixels += area
            cx = int(stats[idx, cv2.CC_STAT_LEFT]) + x1
            cy = int(stats[idx, cv2.CC_STAT_TOP]) + y1
            cw = int(stats[idx, cv2.CC_STAT_WIDTH])
            ch = int(stats[idx, cv2.CC_STAT_HEIGHT])
            box = (cx, cy, cx + cw, cy + ch)
            component_boxes.append(box)
            component_records.append((cx + cw // 2, cy + ch // 2, box, area))

    roi_area = float(roi.shape[0] * roi.shape[1]) or 1.0
    area_ratio = area_pixels / roi_area
    dense_bbox, dense_count, dense_area_ratio = _densest_cluster_box(component_records, w, h)
    bbox = dense_bbox or _merge_boxes(component_boxes)
    bbox_area_ratio = 0.0
    if bbox:
        bx1, by1, bx2, by2 = bbox
        bbox_area_ratio = ((bx2 - bx1) * (by2 - by1)) / float(w * h)

    # Keep this deliberately conservative. The heuristic is only a review trigger
    # for obvious dark contamination clusters, not a general defect detector.
    dense_compact_cluster = (
        dense_count >= 10
        and dense_area_ratio >= 0.003
        and dark_ratio <= 0.06
        and 0.015 <= bbox_area_ratio <= 0.18
    )
    broad_surface_contamination = (
        cluster_count >= 150
        and area_ratio >= 0.012
        and dark_ratio >= 0.08
        and 0.015 <= bbox_area_ratio <= 0.34
    )
    scattered_surface_contamination = (
        cluster_count >= 200
        and area_ratio >= 0.007
        and dark_ratio >= 0.05
        and 0.012 <= bbox_area_ratio <= 0.30
    )
    flagged = dense_compact_cluster or broad_surface_contamination or scattered_surface_contamination
    confidence = "high" if flagged and area_ratio >= 0.014 else "medium" if flagged else "low"
    reason = None
    if flagged:
        reason = (
            f"dark speckle heuristic flagged {cluster_count} clusters "
            f"(area_ratio={area_ratio:.4f}, dark_ratio={dark_ratio:.4f})"
        )

    if flagged and dense_bbox and (dense_compact_cluster or dense_count >= 24):
        bbox = dense_bbox

    return SpeckleHeuristicResult(flagged, cluster_count, area_ratio, dark_ratio, reason, bbox, confidence)


def detect_linear_surface_marks(image: Image.Image) -> SurfaceMarkHeuristicResult:
    """Detect obvious scratch/wear patterns without treating normal bottle edges as defects."""
    if cv2 is None:
        return SurfaceMarkHeuristicResult(False, 0, None)

    rgb = np.array(image.convert("RGB"))
    if rgb.size == 0:
        return SurfaceMarkHeuristicResult(False, 0, None)

    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    h, w = gray.shape
    if h < 120 or w < 120:
        return SurfaceMarkHeuristicResult(False, 0, None)

    x1 = int(w * 0.25)
    x2 = int(w * 0.75)
    y1 = int(h * 0.18)
    y2 = int(h * 0.88)
    roi = gray[y1:y2, x1:x2]

    roi = cv2.GaussianBlur(roi, (3, 3), 0)
    edges = cv2.Canny(roi, 55, 145)
    lines = cv2.HoughLinesP(
        edges,
        rho=1,
        theta=np.pi / 180,
        threshold=34,
        minLineLength=max(36, min(w, h) // 24),
        maxLineGap=8,
    )
    if lines is None:
        return SurfaceMarkHeuristicResult(False, 0, None)

    diagonal_boxes: list[tuple[int, int, int, int]] = []
    for line in lines[:, 0]:
        lx1, ly1, lx2, ly2 = [int(v) for v in line]
        dx = lx2 - lx1
        dy = ly2 - ly1
        length = float((dx * dx + dy * dy) ** 0.5)
        if length < max(36, min(w, h) // 24):
            continue
        angle = abs(np.degrees(np.arctan2(dy, dx))) % 180
        # Product silhouettes and threads are mostly vertical/horizontal. Scratches
        # and scuffs usually appear as many diagonal hairlines.
        if 18 <= angle <= 72 or 108 <= angle <= 162:
            diagonal_boxes.append(
                (
                    min(lx1, lx2) + x1,
                    min(ly1, ly2) + y1,
                    max(lx1, lx2) + x1,
                    max(ly1, ly2) + y1,
                )
            )

    line_count = len(diagonal_boxes)
    bbox = _merge_boxes(diagonal_boxes)
    bbox_area_ratio = 0.0
    if bbox:
        bx1, by1, bx2, by2 = bbox
        bbox_area_ratio = ((bx2 - bx1) * (by2 - by1)) / float(w * h)

    flagged = line_count >= 14 and 0.025 <= bbox_area_ratio <= 0.45
    reason = None
    if flagged:
        reason = f"linear surface mark heuristic flagged {line_count} diagonal scratch-like lines"

    confidence = "high" if flagged and line_count >= 28 else "medium" if flagged else "low"
    return SurfaceMarkHeuristicResult(flagged, line_count, reason, bbox, confidence)


def _merge_boxes(boxes: list[tuple[int, int, int, int]]) -> tuple[int, int, int, int] | None:
    if not boxes:
        return None
    return (
        min(box[0] for box in boxes),
        min(box[1] for box in boxes),
        max(box[2] for box in boxes),
        max(box[3] for box in boxes),
    )


def _densest_cluster_box(
    records: list[tuple[int, int, tuple[int, int, int, int], int]],
    width: int,
    height: int,
) -> tuple[tuple[int, int, int, int] | None, int, float]:
    if not records:
        return None, 0, 0.0

    window_w = max(96, width // 5)
    window_h = max(96, height // 5)
    best: list[tuple[int, int, tuple[int, int, int, int], int]] = []
    for cx, cy, _, _ in records:
        x1 = cx - window_w // 2
        x2 = cx + window_w // 2
        y1 = cy - window_h // 2
        y2 = cy + window_h // 2
        current = [record for record in records if x1 <= record[0] <= x2 and y1 <= record[1] <= y2]
        if len(current) > len(best):
            best = current

    if len(best) < 8:
        return None, len(best), 0.0

    boxes = [record[2] for record in best]
    area = sum(record[3] for record in best)
    bbox = _merge_boxes(boxes)
    image_area = float(width * height) or 1.0
    return bbox, len(best), area / image_area
