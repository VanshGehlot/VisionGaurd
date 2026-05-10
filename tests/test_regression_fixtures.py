from pathlib import Path

from PIL import Image

from utils.annotation import annotate_image_with_metadata
from utils.pass_verifier import verify_pass_result
from utils.safety_net import apply_safety_net
from utils.visual_heuristics import detect_dark_speckles


BASE_PASS = {
    "defect_detected": False,
    "defect_type": "none",
    "defect_category": "none",
    "severity": "ok",
    "confidence": 0.9,
    "location": "none",
    "region": {"horizontal": "none", "vertical": "none"},
    "action": "PASS",
    "visual_explanation": "No visible defect detected.",
    "possible_causes": [],
    "recommended_fix": [],
    "prevention": [],
    "factory_owner_summary": "Product appears clean.",
}

FIXTURES = Path("tests") / "fixtures" / "regression"


def test_clean_white_bottle_passes_with_badge_only_annotation():
    image = Image.open(FIXTURES / "clean_white_bottle.jpg")

    result = verify_pass_result(
        BASE_PASS,
        image,
        reviewer=lambda _image: BASE_PASS,
        speckle_detector=detect_dark_speckles,
    )
    _, annotation = annotate_image_with_metadata(image, result)

    assert result["final_verdict"] == "PASS"
    assert annotation["annotation_mode"] == "badge_only"
    assert annotation["bbox_source"] == "none"


def test_dirty_speckled_bottle_forces_operator_review():
    image = Image.open(FIXTURES / "dirty_speckled_bottle.jpg")

    result = verify_pass_result(
        BASE_PASS,
        image,
        reviewer=lambda _image: BASE_PASS,
        speckle_detector=detect_dark_speckles,
    )
    _, annotation = annotate_image_with_metadata(image, result)

    assert result["final_verdict"] == "ALERT_OPERATOR"
    assert result["defect_type"] == "contamination"
    assert result["override_reason"] == "speckle_contamination_detected"
    assert annotation["annotation_mode"] == "heuristic_bbox"
    assert annotation["bbox_source"] == "speckle_heuristic"


def test_generated_speckled_bottle_forces_operator_review():
    image = Image.open(FIXTURES / "generated_speckled_bottle.png")

    result = verify_pass_result(
        BASE_PASS,
        image,
        reviewer=lambda _image: BASE_PASS,
        speckle_detector=detect_dark_speckles,
    )
    _, annotation = annotate_image_with_metadata(image, result)

    assert result["final_verdict"] == "ALERT_OPERATOR"
    assert result["defect_type"] == "contamination"
    assert result["defect_category"] == "surface contamination"
    assert result["override_reason"] == "speckle_contamination_detected"
    assert annotation["annotation_mode"] == "heuristic_bbox"
    assert annotation["bbox_source"] == "speckle_heuristic"


def test_user_dirty_speckled_bottle_forces_operator_review():
    image = Image.open(FIXTURES / "user_dirty_speckled_bottle.png")

    result = verify_pass_result(
        BASE_PASS,
        image,
        reviewer=lambda _image: BASE_PASS,
        speckle_detector=detect_dark_speckles,
    )
    _, annotation = annotate_image_with_metadata(image, result)

    assert result["final_verdict"] == "ALERT_OPERATOR"
    assert result["defect_type"] == "contamination"
    assert result["defect_category"] == "surface contamination"
    assert result["override_reason"] == "speckle_contamination_detected"
    assert annotation["annotation_mode"] == "heuristic_bbox"


def test_broken_chipped_rim_safety_net_localizes_upper_neck():
    heuristic_review = {
        **BASE_PASS,
        "defect_type": "contamination",
        "defect_category": "surface contamination",
        "severity": "warning",
        "action": "ALERT_OPERATOR",
        "final_verdict": "ALERT_OPERATOR",
        "override_reason": "speckle_contamination_detected",
    }
    result = apply_safety_net(heuristic_review, "broken_chipped_rim_bottle.jpg")
    image = Image.open(FIXTURES / "broken_chipped_rim_bottle.jpg")
    _, annotation = annotate_image_with_metadata(image, result)

    assert result["final_verdict"] == "STOP_LINE"
    assert result["defect_type"] == "broken_part"
    assert result["region"] == {"horizontal": "center", "vertical": "upper"}
    assert annotation["annotation_mode"] == "approximate_region"
    assert annotation["bbox_source"] == "structural_override"


def test_neck_crack_safety_net_localizes_upper_neck():
    heuristic_review = {
        **BASE_PASS,
        "defect_type": "contamination",
        "defect_category": "surface contamination",
        "severity": "warning",
        "action": "ALERT_OPERATOR",
        "final_verdict": "ALERT_OPERATOR",
        "override_reason": "speckle_contamination_detected",
    }
    result = apply_safety_net(heuristic_review, "neck_crack_bottle.jpg")
    image = Image.open(FIXTURES / "neck_crack_bottle.jpg")
    _, annotation = annotate_image_with_metadata(image, result)

    assert result["final_verdict"] == "STOP_LINE"
    assert result["defect_type"] == "broken_part"
    assert result["region"] == {"horizontal": "center", "vertical": "upper"}
    assert annotation["annotation_mode"] == "approximate_region"
