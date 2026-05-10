from model.json_parser import parse_model_json


def test_parse_valid_json():
    result = parse_model_json(
        '{"defect_detected": true, "defect_type": "crack", "defect_category": "surface crack", '
        '"severity": "critical", "confidence": 0.9, "location": "upper-left bottle neck", '
        '"region": {"horizontal": "left", "vertical": "upper"}, "action": "PASS", '
        '"visual_explanation": "Crack visible.", "possible_causes": ["thermal stress"], '
        '"recommended_fix": ["remove item"], "prevention": ["calibrate cooling"], '
        '"factory_owner_summary": "Critical crack summary."}'
    )
    assert result["defect_detected"] is True
    assert result["defect_type"] == "crack"
    assert result["defect_category"] == "surface crack"
    assert result["severity"] == "critical"
    assert result["action"] == "STOP_LINE"
    assert result["region"]["horizontal"] == "left"
    assert result["possible_causes"] == ["thermal stress"]


def test_parse_markdown_wrapped_json():
    result = parse_model_json(
        '```json\n{"defect_detected": false, "defect_type": "unknown", "severity": "ok"}\n```'
    )
    assert result["defect_detected"] is False
    assert result["defect_type"] == "none"
    assert result["defect_category"] == "none"
    assert result["action"] == "PASS"


def test_parse_invalid_json_fallback():
    result = parse_model_json("not-json")
    assert result["defect_detected"] is False
    assert result["action"] == "PASS"
    assert "could not be parsed" in result["visual_explanation"].lower()
    assert result["possible_causes"] == []


def test_warning_severity_promotes_alert_operator():
    result = parse_model_json(
        '{"defect_detected": true, "defect_type": "contamination", "severity": "warning", '
        '"confidence": 0.75, "location": "multiple", "action": "PASS"}'
    )
    assert result["action"] == "ALERT_OPERATOR"


def test_missing_fields_fallback_safely():
    result = parse_model_json(
        '{"defect_detected": true, "defect_type": "crack", "severity": "warning"}'
    )
    assert result["defect_category"] == "surface crack"
    assert result["region"]["horizontal"] == "unknown"
    assert result["recommended_fix"] == []
