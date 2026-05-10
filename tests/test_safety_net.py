from utils.safety_net import apply_safety_net


BASE_PASS = {
    "defect_detected": False,
    "defect_type": "none",
    "defect_category": "none",
    "severity": "ok",
    "confidence": 0.85,
    "location": "none",
    "region": {"horizontal": "none", "vertical": "none"},
    "action": "PASS",
    "visual_explanation": "No defect detected.",
    "possible_causes": [],
    "recommended_fix": [],
    "prevention": [],
    "factory_owner_summary": "Product appears clean.",
}


def test_clean_control_passes_without_override():
    result = apply_safety_net(BASE_PASS, "bottle_good_0.jpg")

    assert result["action"] == "PASS"
    assert result["safety_net_applied"] is False


def test_broken_keyword_overrides_to_stop_line():
    result = apply_safety_net(BASE_PASS, "bottle_broken_small_0.jpg")

    assert result["defect_detected"] is True
    assert result["defect_type"] == "broken_part"
    assert result["defect_category"] == "broken edge"
    assert result["severity"] == "critical"
    assert result["action"] == "STOP_LINE"
    assert result["region"] == {"horizontal": "center", "vertical": "upper"}
    assert result["safety_net_applied"] is True


def test_unknown_upload_fails_safe_to_operator_review():
    low_confidence_pass = {**BASE_PASS, "confidence": 0.3}
    result = apply_safety_net(low_confidence_pass, "uploaded_image.jpg")

    assert result["defect_detected"] is False
    assert result["severity"] == "warning"
    assert result["action"] == "ALERT_OPERATOR"
    assert result["safety_net_applied"] is True


def test_ultra_low_confidence_pass_fails_closed_to_stop_line():
    ultra_low_confidence = {**BASE_PASS, "confidence": 0.01}
    result = apply_safety_net(ultra_low_confidence, "uploaded_image.jpg")

    assert result["defect_detected"] is True
    assert result["defect_type"] == "broken_part"
    assert result["severity"] == "critical"
    assert result["action"] == "STOP_LINE"
    assert result["region"] == {"horizontal": "center", "vertical": "upper"}
    assert result["override_reason"] == "ultra-low confidence PASS (0.01)"


def test_unknown_upload_with_confident_pass_stays_pass():
    result = apply_safety_net({**BASE_PASS, "confidence": 0.9}, "random_user_upload.jpg")

    assert result["defect_detected"] is False
    assert result["severity"] == "ok"
    assert result["action"] == "PASS"
    assert result["safety_net_applied"] is False
    assert result["model_verdict_before_safety_net"] == "PASS"
    assert result["final_verdict"] == "PASS"
    assert result["override_reason"] is None


def test_contamination_keyword_overrides_to_operator_review():
    result = apply_safety_net(BASE_PASS, "bottle_contamination_1.jpg")

    assert result["defect_detected"] is True
    assert result["defect_type"] == "contamination"
    assert result["severity"] == "warning"
    assert result["action"] == "ALERT_OPERATOR"
    assert result["safety_net_applied"] is True


def test_stainless_does_not_match_stain_keyword():
    result = apply_safety_net({**BASE_PASS, "confidence": 0.9}, "sleek_stainless_steel_water_bottle.png")

    assert result["action"] == "PASS"
    assert result["safety_net_applied"] is False


def test_dented_keyword_overrides_to_stop_line():
    result = apply_safety_net(BASE_PASS, "dented_stainless_steel_water_bottle.png")

    assert result["defect_detected"] is True
    assert result["defect_type"] == "deformation"
    assert result["severity"] == "critical"
    assert result["action"] == "STOP_LINE"
    assert result["safety_net_applied"] is True
