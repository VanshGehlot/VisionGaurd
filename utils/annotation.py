from __future__ import annotations

from PIL import Image, ImageColor, ImageDraw, ImageFont

LOCALIZED_HORIZONTAL = {"left", "center", "right"}
LOCALIZED_VERTICAL = {"upper", "middle", "lower"}


def get_region_box(width: int, height: int, horizontal: str, vertical: str) -> tuple[int, int, int, int]:
    horizontal = str(horizontal or "unknown").lower()
    vertical = str(vertical or "unknown").lower()
    third_w = width // 3
    third_h = height // 3
    margin_x = max(8, width // 24)
    margin_y = max(8, height // 24)

    x_map = {
        "left": (0, third_w + margin_x),
        "center": (third_w, 2 * third_w),
        "right": (2 * third_w - margin_x, width),
    }
    y_map = {
        "upper": (0, third_h + margin_y),
        "middle": (third_h, 2 * third_h),
        "lower": (2 * third_h - margin_y, height),
    }

    x1, x2 = x_map[horizontal]
    y1, y2 = y_map[vertical]
    return x1, y1, x2, y2


def annotate_image(image: Image.Image, result: dict) -> Image.Image:
    annotated, _ = annotate_image_with_metadata(image, result)
    return annotated


def annotate_image_with_metadata(image: Image.Image, result: dict) -> tuple[Image.Image, dict]:
    """
    Draw honest inspection annotations.

    This is not a detector. It only visualizes either a PASS/REVIEW badge, a
    heuristic speckle bounding box, or Qwen's approximate 3x3 region.
    """
    annotated = image.convert("RGBA").copy()
    draw = ImageDraw.Draw(annotated, "RGBA")
    width, height = annotated.size
    label_font = _load_font(_label_font_size(width, height), bold=True)

    meta = {
        "annotation_mode": "none",
        "annotation_confidence": "low",
        "annotation_reason": "No localized defect region available.",
        "bbox_source": "none",
    }

    action = str(result.get("action", "PASS") or "PASS").upper()
    severity = str(result.get("severity", "ok") or "ok").lower()
    defect_type = str(result.get("defect_type", "unknown") or "unknown").lower()

    if action == "PASS" or severity == "ok":
        _draw_label(draw, label_font, 14, 14, "PASS", "#16a34a", annotated.size)
        meta.update(
            {
                "annotation_mode": "badge_only",
                "annotation_confidence": "high",
                "annotation_reason": "Product passed inspection; no defect region was drawn.",
            }
        )
        return annotated, meta

    heuristic_box = _safe_bbox(result.get("heuristic_bbox"), width, height)
    if action in {"ALERT_OPERATOR", "LOG_WARNING"} and heuristic_box:
        color = "#f59e0b"
        _draw_box(
            annotated,
            heuristic_box,
            color,
            "REVIEW",
        )
        meta.update(
            {
                "annotation_mode": "heuristic_bbox",
                "annotation_confidence": str(result.get("heuristic_confidence") or "medium"),
                "annotation_reason": "Speckle heuristic found a localized cluster; this is not an exact defect boundary.",
                "bbox_source": "speckle_heuristic",
            }
        )
        return annotated, meta

    region = result.get("region") if isinstance(result.get("region"), dict) else {}
    horizontal = str(region.get("horizontal", "") or "").lower()
    vertical = str(region.get("vertical", "") or "").lower()
    has_qwen_region = horizontal in LOCALIZED_HORIZONTAL and vertical in LOCALIZED_VERTICAL

    if action == "STOP_LINE" and has_qwen_region:
        box = get_region_box(width, height, horizontal, vertical)
        _draw_box(
            annotated,
            box,
            "#dc2626",
            "STOP_LINE",
        )
        bbox_source = "structural_override" if result.get("safety_net_applied") else "qwen_region"
        meta.update(
            {
                "annotation_mode": "approximate_region",
                "annotation_confidence": "medium",
                "annotation_reason": "Qwen returned an approximate 3x3 product region; this is not a true bounding box.",
                "bbox_source": bbox_source,
            }
        )
        return annotated, meta

    if action in {"ALERT_OPERATOR", "LOG_WARNING"} and has_qwen_region and defect_type not in {"unknown", "none"}:
        box = get_region_box(width, height, horizontal, vertical)
        _draw_box(
            annotated,
            box,
            "#f59e0b",
            "REVIEW",
        )
        meta.update(
            {
                "annotation_mode": "approximate_region",
                "annotation_confidence": "medium",
                "annotation_reason": "Qwen returned an approximate 3x3 product region; this is not a true bounding box.",
                "bbox_source": "qwen_region",
            }
        )
        return annotated, meta

    _draw_label(draw, label_font, 14, 14, "REVIEW", "#f59e0b", annotated.size)
    meta.update(
        {
            "annotation_mode": "review_badge_only",
            "annotation_confidence": "low",
            "annotation_reason": "No localized defect region available. Human review required.",
        }
    )
    return annotated, meta


def _draw_box(
    image: Image.Image,
    box: tuple[int, int, int, int],
    color: str,
    label: str,
) -> None:
    rgb = ImageColor.getrgb(color)
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay, "RGBA")
    overlay_draw.rectangle(box, fill=(*rgb, 22))
    image.alpha_composite(overlay)

    draw = ImageDraw.Draw(image, "RGBA")
    label_font = _load_font(_label_font_size(*image.size), bold=True)
    x1, y1, x2, y2 = box
    draw.rectangle(box, outline=(*rgb, 235), width=3)
    _draw_corner_ticks(draw, box, (*rgb, 255), width=max(4, min(image.size) // 140))
    _draw_label(draw, label_font, x1 + 12, max(12, y1 + 12), label, color, image.size)


def _safe_bbox(raw_bbox: object, width: int, height: int) -> tuple[int, int, int, int] | None:
    if not isinstance(raw_bbox, (list, tuple)) or len(raw_bbox) != 4:
        return None
    try:
        x1, y1, x2, y2 = [int(value) for value in raw_bbox]
    except Exception:
        return None

    x1 = max(0, min(width - 1, x1))
    y1 = max(0, min(height - 1, y1))
    x2 = max(1, min(width, x2))
    y2 = max(1, min(height, y2))
    if x2 <= x1 or y2 <= y1:
        return None

    area_ratio = ((x2 - x1) * (y2 - y1)) / float(width * height)
    if area_ratio >= 0.82:
        return None
    return x1, y1, x2, y2


def _load_font(size: int, bold: bool) -> ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial Bold.ttf" if bold else "/Library/Fonts/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size=size)
        except Exception:
            continue
    return ImageFont.load_default()


def _label_font_size(width: int, height: int) -> int:
    return max(11, min(22, min(width, height) // 48))


def _draw_corner_ticks(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    color: tuple[int, int, int, int],
    width: int,
) -> None:
    x1, y1, x2, y2 = box
    tick_x = max(18, int((x2 - x1) * 0.16))
    tick_y = max(18, int((y2 - y1) * 0.16))
    draw.line((x1, y1, x1 + tick_x, y1), fill=color, width=width)
    draw.line((x1, y1, x1, y1 + tick_y), fill=color, width=width)
    draw.line((x2, y1, x2 - tick_x, y1), fill=color, width=width)
    draw.line((x2, y1, x2, y1 + tick_y), fill=color, width=width)
    draw.line((x1, y2, x1 + tick_x, y2), fill=color, width=width)
    draw.line((x1, y2, x1, y2 - tick_y), fill=color, width=width)
    draw.line((x2, y2, x2 - tick_x, y2), fill=color, width=width)
    draw.line((x2, y2, x2, y2 - tick_y), fill=color, width=width)


def _draw_label(
    draw: ImageDraw.ImageDraw,
    font: ImageFont.ImageFont,
    x: int,
    y: int,
    text: str,
    color: str,
    image_size: tuple[int, int],
) -> None:
    left, top, right, bottom = draw.textbbox((x, y), text, font=font)
    padding_x = 8
    padding_y = 5
    image_width, image_height = image_size
    label_width = right - left + padding_x * 2
    label_height = bottom - top + padding_y * 2
    x = max(padding_x, min(x, image_width - label_width + padding_x))
    y = max(padding_y, min(y, image_height - label_height + padding_y))
    left, top, right, bottom = draw.textbbox((x, y), text, font=font)
    background = ImageColor.getrgb(color)
    draw.rounded_rectangle(
        (left - padding_x, top - padding_y, right + padding_x, bottom + padding_y),
        radius=8,
        fill=(*background, 226),
    )
    draw.text((x, y), text, font=font, fill="#ffffff")
