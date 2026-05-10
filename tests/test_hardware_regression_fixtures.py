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

FIXTURES = Path("tests") / "fixtures" / "hardware_regression"


def _pass_then_safety(filename: str, confidence: float = 0.9) -> tuple[dict, dict]:
    image = Image.open(FIXTURES / filename)
    verified = verify_pass_result(
        {**BASE_PASS, "confidence": confidence},
        image,
        reviewer=lambda _image: {**BASE_PASS, "confidence": confidence},
        speckle_detector=detect_dark_speckles,
    )
    result = apply_safety_net(verified, filename)
    _, annotation = annotate_image_with_metadata(image, result)
    return result, annotation


def test_clean_cordless_drill_passes_badge_only():
    result, annotation = _pass_then_safety("cordless_drill_on_white_background.png", confidence=0.85)

    assert result["final_verdict"] == "PASS"
    assert annotation["annotation_mode"] == "badge_only"
    assert annotation["bbox_source"] == "none"


def test_clean_brushed_aluminum_laptop_passes_badge_only():
    result, annotation = _pass_then_safety("brushed_aluminum_laptop_top_view.png", confidence=0.85)

    assert result["final_verdict"] == "PASS"
    assert annotation["annotation_mode"] == "badge_only"
    assert annotation["bbox_source"] == "none"


def test_weathered_hinge_corrosion_routes_to_localized_review():
    result, annotation = _pass_then_safety("weathered_metal_door_hinge_close_up.png", confidence=0.85)

    assert result["final_verdict"] == "ALERT_OPERATOR"
    assert result["defect_type"] == "contamination"
    assert result["override_reason"] == "speckle_contamination_detected"
    assert annotation["annotation_mode"] == "heuristic_bbox"
    assert annotation["bbox_source"] == "speckle_heuristic"


def test_copper_corrosion_routes_to_localized_review():
    result, annotation = _pass_then_safety("copper_plumbing_elbow_fitting_close_up.png", confidence=0.85)

    assert result["final_verdict"] == "ALERT_OPERATOR"
    assert result["defect_type"] == "contamination"
    assert result["override_reason"] == "speckle_contamination_detected"
    assert annotation["annotation_mode"] == "heuristic_bbox"


def test_worn_items_route_to_review_without_fake_bbox():
    for filename in (
        "wooden_drawer_pull_with_subtle_wear.png",
        "worn_metal_adjustable_wrench_on_white_background.png",
        "worn_metal_ball_bearing_details.png",
    ):
        result, annotation = _pass_then_safety(filename, confidence=0.85)

        assert result["final_verdict"] == "ALERT_OPERATOR"
        assert result["action"] == "ALERT_OPERATOR"
        assert annotation["annotation_mode"] == "review_badge_only"
        assert annotation["bbox_source"] == "none"


def test_damaged_structural_items_stop_line_when_model_detects_critical_issue():
    for filename in (
        "damaged_white_outlet_cover_plate.png",
        "worn_safety_goggle_lens_close_up.png",
        "porcelain_insulator_with_weathered_metal_cap.png",
    ):
        image = Image.open(FIXTURES / filename)
        result = {
            **BASE_PASS,
            "defect_detected": True,
            "defect_type": "crack",
            "defect_category": "structural crack",
            "severity": "critical",
            "confidence": 0.95,
            "location": "visible product surface",
            "region": {"horizontal": "center", "vertical": "middle"},
            "action": "STOP_LINE",
            "final_verdict": "STOP_LINE",
        }
        _, annotation = annotate_image_with_metadata(image, result)

        assert result["final_verdict"] == "STOP_LINE"
        assert annotation["annotation_mode"] == "approximate_region"
