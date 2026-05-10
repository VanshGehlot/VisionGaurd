from PIL import Image, ImageDraw
from requests import Timeout

from utils.pass_verifier import verify_pass_result
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


def test_clean_unknown_bottle_stays_pass():
    image = Image.new("RGB", (256, 256), "white")

    result = verify_pass_result(
        BASE_PASS,
        image,
        reviewer=lambda _image: BASE_PASS,
        speckle_detector=lambda _image: type("Heuristic", (), {"flagged": False, "reason": None})(),
    )

    assert result["action"] == "PASS"
    assert result["pass_verification_applied"] is True
    assert result["pass_verification_reason"] == "first and second pass agreed clean"
    assert result["second_pass_verdict"] == "passed"
    assert result["final_verdict"] == "PASS"


def test_dirty_speckled_bottle_routes_to_alert():
    image = _make_speckled_image()

    result = verify_pass_result(
        BASE_PASS,
        image,
        reviewer=lambda _image: BASE_PASS,
        speckle_detector=detect_dark_speckles,
    )

    assert result["action"] == "ALERT_OPERATOR"
    assert result["defect_type"] == "contamination"
    assert result["defect_category"] == "surface contamination"
    assert result["second_pass_called"] is False
    assert result["override_reason"] == "speckle_contamination_detected"
    assert result["second_pass_verdict"] == "skipped"
    assert result["final_verdict"] == "ALERT_OPERATOR"


def test_chipped_rim_bottle_uses_second_pass_review():
    image = Image.new("RGB", (256, 256), "white")
    chipped = {
        **BASE_PASS,
        "defect_detected": True,
        "defect_type": "broken_part",
        "defect_category": "broken edge",
        "severity": "critical",
        "action": "STOP_LINE",
        "confidence": 0.88,
    }

    result = verify_pass_result(
        BASE_PASS,
        image,
        reviewer=lambda _image: chipped,
        speckle_detector=lambda _image: type("Heuristic", (), {"flagged": False, "reason": None})(),
    )

    assert result["action"] == "STOP_LINE"
    assert result["pass_verification_reason"] == "strict second-pass review detected visible anomaly"
    assert result["second_pass_verdict"] == "failed"
    assert result["final_verdict"] == "STOP_LINE"


def test_dented_bottle_uses_second_pass_review():
    image = Image.new("RGB", (256, 256), "white")
    dented = {
        **BASE_PASS,
        "defect_detected": True,
        "defect_type": "dent",
        "defect_category": "unknown",
        "severity": "warning",
        "action": "ALERT_OPERATOR",
        "confidence": 0.74,
    }

    result = verify_pass_result(
        BASE_PASS,
        image,
        reviewer=lambda _image: dented,
        speckle_detector=lambda _image: type("Heuristic", (), {"flagged": False, "reason": None})(),
    )

    assert result["action"] == "ALERT_OPERATOR"
    assert result["defect_type"] == "dent"
    assert result["second_pass_verdict"] == "failed"


def test_second_pass_timeout_with_clean_confident_pass_stays_pass():
    image = Image.new("RGB", (256, 256), "white")

    result = verify_pass_result(
        BASE_PASS,
        image,
        reviewer=lambda _image: (_ for _ in ()).throw(Timeout("second pass timeout")),
        speckle_detector=lambda _image: type("Heuristic", (), {"flagged": False, "reason": None})(),
    )

    assert result["action"] == "PASS"
    assert result["second_pass_verdict"] == "timeout"
    assert result["second_pass_called"] is True
    assert result["pass_verification_reason"] == "second_pass_timeout"
    assert result["final_verdict"] == "PASS"


def test_second_pass_timeout_with_low_confidence_routes_to_alert():
    image = Image.new("RGB", (256, 256), "white")
    low_confidence = {**BASE_PASS, "confidence": 0.3}

    result = verify_pass_result(
        low_confidence,
        image,
        reviewer=lambda _image: (_ for _ in ()).throw(Timeout("second pass timeout")),
        speckle_detector=lambda _image: type("Heuristic", (), {"flagged": False, "reason": None})(),
    )

    assert result["action"] == "ALERT_OPERATOR"
    assert result["defect_detected"] is False
    assert result["second_pass_verdict"] == "timeout"
    assert result["pass_verification_reason"] == "second_pass_timeout_low_confidence"
    assert result["final_verdict"] == "ALERT_OPERATOR"


def test_speckles_route_to_alert_before_second_pass():
    image = _make_speckled_image()

    result = verify_pass_result(
        BASE_PASS,
        image,
        reviewer=lambda _image: (_ for _ in ()).throw(AssertionError("reviewer should not run")),
        speckle_detector=detect_dark_speckles,
    )

    assert result["action"] == "ALERT_OPERATOR"
    assert result["second_pass_verdict"] == "skipped"
    assert result["second_pass_called"] is False
    assert result["speckle_review_flagged"] is True
    assert result["override_reason"] == "speckle_contamination_detected"
    assert result["final_verdict"] == "ALERT_OPERATOR"


def test_surface_marks_route_to_alert_before_second_pass():
    image = Image.new("RGB", (256, 256), "white")
    marks = type(
        "SurfaceMarks",
        (),
        {
            "flagged": True,
            "bbox": (40, 45, 190, 210),
            "confidence": "high",
            "reason": "synthetic scratch-like lines",
        },
    )()

    result = verify_pass_result(
        BASE_PASS,
        image,
        reviewer=lambda _image: (_ for _ in ()).throw(AssertionError("reviewer should not run")),
        speckle_detector=lambda _image: type("Heuristic", (), {"flagged": False, "reason": None})(),
        surface_mark_detector=lambda _image: marks,
    )

    assert result["action"] == "ALERT_OPERATOR"
    assert result["defect_type"] == "scratch"
    assert result["override_reason"] == "surface_mark_anomaly_detected"
    assert result["second_pass_verdict"] == "skipped"
    assert result["final_verdict"] == "ALERT_OPERATOR"


def test_first_pass_defect_skips_second_pass():
    image = Image.new("RGB", (256, 256), "white")
    defect = {
        **BASE_PASS,
        "defect_detected": True,
        "defect_type": "crack",
        "severity": "critical",
        "action": "STOP_LINE",
    }

    result = verify_pass_result(
        defect,
        image,
        reviewer=lambda _image: (_ for _ in ()).throw(AssertionError("reviewer should not run")),
    )

    assert result["action"] == "STOP_LINE"
    assert result["second_pass_verdict"] == "skipped"
    assert result["final_verdict"] == "STOP_LINE"


def _make_speckled_image() -> Image.Image:
    image = Image.new("RGB", (256, 256), "white")
    draw = ImageDraw.Draw(image)
    for x, y in (
        (70, 70), (90, 92), (115, 80), (140, 95), (155, 120),
        (78, 140), (102, 150), (126, 132), (148, 160), (118, 112),
        (136, 88), (96, 118),
    ):
        draw.ellipse((x, y, x + 8, y + 8), fill="black")
    return image
