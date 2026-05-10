from PIL import Image

from utils.annotation import annotate_image, annotate_image_with_metadata, get_region_box


def test_region_left_upper_maps_to_top_left_box():
    assert get_region_box(300, 300, "left", "upper") == (0, 0, 112, 112)


def test_unknown_region_is_not_mapped_to_fake_box():
    try:
        get_region_box(400, 300, "unknown", "unknown")
    except KeyError:
        assert True
    else:
        raise AssertionError("unknown regions must not create fake localization boxes")


def test_no_defect_returns_modified_image_with_pass_label():
    image = Image.new("RGB", (120, 120), "white")
    result = {
        "defect_detected": False,
        "defect_type": "none",
        "severity": "ok",
        "region": {"horizontal": "none", "vertical": "none"},
    }
    annotated = annotate_image(image, result)
    assert annotated.size == image.size
    assert annotated.getpixel((12, 12)) != (255, 255, 255)


def test_pass_metadata_uses_badge_only_no_box():
    image = Image.new("RGB", (180, 140), "white")
    result = {"defect_detected": False, "severity": "ok", "action": "PASS"}
    _, meta = annotate_image_with_metadata(image, result)
    assert meta["annotation_mode"] == "badge_only"
    assert meta["bbox_source"] == "none"


def test_review_unknown_uses_badge_only_no_box():
    image = Image.new("RGB", (180, 140), "white")
    result = {
        "defect_detected": False,
        "defect_type": "unknown",
        "severity": "warning",
        "action": "ALERT_OPERATOR",
        "region": {"horizontal": "unknown", "vertical": "unknown"},
    }
    _, meta = annotate_image_with_metadata(image, result)
    assert meta["annotation_mode"] == "review_badge_only"
    assert meta["bbox_source"] == "none"


def test_stop_line_known_region_uses_approximate_region():
    image = Image.new("RGB", (180, 140), "white")
    result = {
        "defect_detected": True,
        "defect_type": "crack",
        "severity": "critical",
        "action": "STOP_LINE",
        "region": {"horizontal": "right", "vertical": "upper"},
    }
    _, meta = annotate_image_with_metadata(image, result)
    assert meta["annotation_mode"] == "approximate_region"
    assert meta["bbox_source"] == "qwen_region"


def test_speckle_bbox_uses_heuristic_box_not_full_image():
    image = Image.new("RGB", (200, 160), "white")
    result = {
        "defect_detected": False,
        "defect_type": "contamination",
        "severity": "warning",
        "action": "ALERT_OPERATOR",
        "heuristic_bbox": [40, 30, 90, 80],
        "heuristic_confidence": "medium",
    }
    _, meta = annotate_image_with_metadata(image, result)
    assert meta["annotation_mode"] == "heuristic_bbox"
    assert meta["bbox_source"] == "speckle_heuristic"
