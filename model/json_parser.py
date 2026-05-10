import json
import re

SAFE_RESULT = {
    "defect_detected": False,
    "defect_type": "unknown",
    "defect_category": "unknown",
    "severity": "ok",
    "confidence": 0.0,
    "location": "unknown",
    "region": {
        "horizontal": "unknown",
        "vertical": "unknown",
    },
    "action": "PASS",
    "visual_explanation": "Model output could not be parsed safely.",
    "possible_causes": [],
    "recommended_fix": [],
    "prevention": [],
    "factory_owner_summary": "No reliable inspection summary could be generated.",
}

ALLOWED_DEFECT_TYPES = {
    "crack",
    "contamination",
    "scratch",
    "deformation",
    "broken_part",
    "missing_part",
    "misalignment",
    "discoloration",
    "dent",
    "none",
    "unknown",
}

ALLOWED_DEFECT_CATEGORIES = {
    "surface crack",
    "structural crack",
    "hairline crack",
    "edge crack",
    "contamination mark",
    "deformation",
    "broken edge",
    "missing component",
    "alignment issue",
    "cosmetic scratch",
    "none",
    "unknown",
}

ALLOWED_SEVERITIES = {"critical", "warning", "ok"}
ALLOWED_ACTIONS = {"STOP_LINE", "ALERT_OPERATOR", "LOG_WARNING", "PASS"}
ALLOWED_REGION_HORIZONTAL = {"left", "center", "right", "multiple", "none", "unknown"}
ALLOWED_REGION_VERTICAL = {"upper", "middle", "lower", "multiple", "none", "unknown"}


def parse_model_json(raw_text: str) -> dict:
    if not raw_text:
        return _copy_safe_result()

    text = raw_text.strip().replace("```json", "").replace("```", "").strip()

    try:
        return normalize_result(json.loads(text))
    except Exception:
        pass

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return normalize_result(json.loads(match.group(0)))
        except Exception:
            pass

    return _copy_safe_result()


def _copy_safe_result() -> dict:
    return {
        **SAFE_RESULT,
        "region": dict(SAFE_RESULT["region"]),
        "possible_causes": list(SAFE_RESULT["possible_causes"]),
        "recommended_fix": list(SAFE_RESULT["recommended_fix"]),
        "prevention": list(SAFE_RESULT["prevention"]),
    }


def _safe_text(value: object, default: str) -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text or default


def _safe_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    items: list[str] = []
    for item in value:
        text = _safe_text(item, "")
        if text:
            items.append(text)
    return items


def normalize_result(data: dict) -> dict:
    result = _copy_safe_result()
    defect_type = _safe_text(data.get("defect_type"), "unknown").lower()
    defect_category = _safe_text(data.get("defect_category"), "unknown").lower()
    severity = _safe_text(data.get("severity"), "ok").lower()
    location = _safe_text(data.get("location"), "unknown")
    action = _safe_text(data.get("action"), "PASS").upper()
    region_data = data.get("region") if isinstance(data.get("region"), dict) else {}
    region_horizontal = _safe_text(region_data.get("horizontal"), "unknown").lower()
    region_vertical = _safe_text(region_data.get("vertical"), "unknown").lower()

    result["defect_detected"] = bool(data.get("defect_detected", False))
    result["defect_type"] = defect_type if defect_type in ALLOWED_DEFECT_TYPES else "unknown"
    result["defect_category"] = (
        defect_category if defect_category in ALLOWED_DEFECT_CATEGORIES else "unknown"
    )
    result["severity"] = severity if severity in ALLOWED_SEVERITIES else "ok"
    result["location"] = location
    result["action"] = action if action in ALLOWED_ACTIONS else "PASS"
    result["region"] = {
        "horizontal": (
            region_horizontal if region_horizontal in ALLOWED_REGION_HORIZONTAL else "unknown"
        ),
        "vertical": region_vertical if region_vertical in ALLOWED_REGION_VERTICAL else "unknown",
    }
    result["visual_explanation"] = _safe_text(
        data.get("visual_explanation") or data.get("explanation"),
        SAFE_RESULT["visual_explanation"],
    )
    result["possible_causes"] = _safe_list(data.get("possible_causes"))
    result["recommended_fix"] = _safe_list(data.get("recommended_fix"))
    result["prevention"] = _safe_list(data.get("prevention"))
    result["factory_owner_summary"] = _safe_text(
        data.get("factory_owner_summary"),
        SAFE_RESULT["factory_owner_summary"],
    )

    try:
        confidence = float(data.get("confidence", 0.0))
        result["confidence"] = max(0.0, min(1.0, confidence))
    except Exception:
        result["confidence"] = 0.0

    if result["severity"] == "critical":
        result["action"] = "STOP_LINE"
    elif result["severity"] == "warning" and result["action"] == "PASS":
        result["action"] = "ALERT_OPERATOR"
    elif result["severity"] == "ok":
        result["action"] = "PASS"

    if result["severity"] == "ok":
        result["defect_detected"] = False
        result["region"] = {"horizontal": "none", "vertical": "none"}
        if result["defect_type"] == "unknown":
            result["defect_type"] = "none"
        if result["defect_category"] == "unknown":
            result["defect_category"] = "none"
        if result["location"].lower() == "unknown":
            result["location"] = "none"
    elif result["defect_category"] == "unknown":
        mapping = {
            "crack": "surface crack",
            "contamination": "contamination mark",
            "scratch": "cosmetic scratch",
            "deformation": "deformation",
            "broken_part": "broken edge",
            "missing_part": "missing component",
            "misalignment": "alignment issue",
            "discoloration": "unknown",
            "dent": "unknown",
        }
        result["defect_category"] = mapping.get(result["defect_type"], "unknown")

    if not result["defect_detected"]:
        result["defect_type"] = "none"
        if result["defect_category"] == "unknown":
            result["defect_category"] = "none"

    return result
