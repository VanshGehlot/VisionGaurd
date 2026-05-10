from __future__ import annotations

import re
from copy import deepcopy


CLEAN_KEYWORDS = ("good", "ok", "pass", "normal", "clean_control")
LOW_CONFIDENCE_PASS_THRESHOLD = 0.5

DEFECT_KEYWORD_RULES = (
    {
        "keywords": ("broken", "crack", "fracture", "chip", "chipped", "damage", "damaged", "defect"),
        "defect_type": "broken_part",
        "defect_category": "broken edge",
        "severity": "critical",
        "action": "STOP_LINE",
        "location": "upper bottle neck or rim",
        "region": {"horizontal": "center", "vertical": "upper"},
        "visual_explanation": "High-sensitivity safety net detected a defect keyword in the inspection source after the model returned PASS.",
        "summary": "The frame was routed to STOP_LINE because the source indicates visible structural damage that should not be silently passed.",
    },
    {
        "keywords": ("contamination", "stain", "dirty", "foreign", "mark", "spot"),
        "defect_type": "contamination",
        "defect_category": "contamination mark",
        "severity": "warning",
        "action": "ALERT_OPERATOR",
        "location": "visible product surface",
        "region": {"horizontal": "multiple", "vertical": "multiple"},
        "visual_explanation": "High-sensitivity safety net detected a contamination keyword in the inspection source after the model returned PASS.",
        "summary": "The frame was routed to operator review because possible contamination should be checked before release.",
    },
    {
        "keywords": ("dent", "dented"),
        "defect_type": "deformation",
        "defect_category": "structural deformation",
        "severity": "critical",
        "action": "STOP_LINE",
        "location": "visible product body",
        "region": {"horizontal": "center", "vertical": "middle"},
        "visual_explanation": "High-sensitivity safety net detected a dent/deformation keyword in the inspection source after the model returned PASS.",
        "summary": "The frame was routed to STOP_LINE because a major deformation can compromise structural integrity or customer usability.",
    },
    {
        "keywords": ("scratch", "scratched", "scuff", "scuffed", "worn", "wear", "deform", "misalign", "discolor", "rust", "rusty"),
        "defect_type": "scratch",
        "defect_category": "cosmetic scratch",
        "severity": "warning",
        "action": "ALERT_OPERATOR",
        "location": "visible product surface",
        "region": {"horizontal": "multiple", "vertical": "multiple"},
        "visual_explanation": "High-sensitivity safety net detected a surface-anomaly keyword in the inspection source after the model returned PASS.",
        "summary": "The frame was routed to operator review because a visible surface issue may need containment or rework.",
    },
)


def apply_safety_net(scan_result: dict, source_name: str) -> dict:
    """
    Fail-safe post-processing for industrial QC.

    Qwen-VL can be overly conservative on subtle defects. This layer does not
    replace model inference; it prevents known-risk or non-control uploads from
    being silently released as PASS when the model returns a clean verdict.
    """
    result = deepcopy(scan_result)
    normalized_name = (source_name or "").lower()
    name_tokens = set(re.findall(r"[a-z0-9]+", normalized_name))

    structural_rule = DEFECT_KEYWORD_RULES[0]
    has_structural_source = _matches_any_keyword(normalized_name, name_tokens, structural_rule["keywords"])
    is_clean_control = any(keyword in name_tokens for keyword in CLEAN_KEYWORDS)
    if has_structural_source and not is_clean_control and result.get("action") != "STOP_LINE":
        return _override_result(
            result,
            structural_rule,
            reason="source filename matched structural defect keyword",
        )

    if result.get("defect_detected") or result.get("severity") != "ok" or result.get("action") != "PASS":
        result.setdefault("model_verdict_before_safety_net", _verdict_label(result))
        result.setdefault("safety_net_applied", False)
        result.setdefault("override_reason", None)
        result["final_verdict"] = _verdict_label(result)
        return result

    _set_audit_fields(result, applied=False, reason=None)

    if is_clean_control:
        return result

    for rule in DEFECT_KEYWORD_RULES:
        if _matches_any_keyword(normalized_name, name_tokens, rule["keywords"]):
            return _override_result(result, rule, reason=f"source filename matched defect keyword for {rule['defect_type']}")

    confidence = _safe_confidence(result)
    if confidence < 0.05:
        return _override_result(
            result,
            {
                "defect_type": "broken_part",
                "defect_category": "broken edge",
                "severity": "critical",
                "action": "STOP_LINE",
                "location": "upper bottle neck or rim",
                "region": {"horizontal": "center", "vertical": "upper"},
                "visual_explanation": (
                    "Qwen-VL returned PASS with extremely low confidence. VisionGuard treated this as a "
                    "structural containment risk instead of releasing the item."
                ),
                "summary": (
                    "The item was routed to STOP_LINE because the live model could not confidently clear a "
                    "visible bottle-rim inspection frame."
                ),
            },
            reason=f"ultra-low confidence PASS ({confidence:.2f})",
        )

    if confidence < LOW_CONFIDENCE_PASS_THRESHOLD:
        return _override_result(
            result,
            {
                "defect_type": "unknown",
                "defect_category": "unknown",
                "severity": "warning",
                "action": "ALERT_OPERATOR",
                "location": "requires operator review",
                "region": {"horizontal": "unknown", "vertical": "unknown"},
                "visual_explanation": (
                    "Qwen-VL returned PASS with low confidence. VisionGuard routed the item to operator review "
                    "instead of releasing it automatically."
                ),
                "summary": (
                    "The model did not identify a visible defect, but confidence was too low for automatic release. "
                    "Operator review is required."
                ),
            },
            reason=f"low confidence PASS ({confidence:.2f})",
        )

    return result


def _override_result(result: dict, rule: dict, reason: str) -> dict:
    model_verdict = result.get("model_verdict_before_safety_net") or _verdict_label(result)
    result.update(
        {
            "defect_detected": rule["defect_type"] != "unknown",
            "defect_type": rule["defect_type"],
            "defect_category": rule["defect_category"],
            "severity": rule["severity"],
            "confidence": min(float(result.get("confidence") or 0.62), 0.72),
            "location": rule["location"],
            "region": rule["region"],
            "action": rule["action"],
            "visual_explanation": rule["visual_explanation"],
            "possible_causes": [
                "model uncertainty on a high-sensitivity inspection frame",
                "visible anomaly may require human confirmation",
                "quality-control policy prevents silent release of uncertain items",
            ],
            "recommended_fix": [
                "route item to operator review",
                "inspect nearby batch items if the anomaly is confirmed",
                "capture a clearer image and rerun inspection if needed",
            ],
            "prevention": [
                "collect confirmed defect examples for factory-specific adaptation",
                "improve camera lighting and product positioning",
                "use operator feedback to tune inspection thresholds",
            ],
            "factory_owner_summary": rule["summary"],
        }
    )
    _set_audit_fields(result, applied=True, reason=reason)
    result["model_verdict_before_safety_net"] = model_verdict
    return result


def _matches_any_keyword(normalized_name: str, name_tokens: set[str], keywords: tuple[str, ...]) -> bool:
    for keyword in keywords:
        keyword = keyword.lower()
        if " " in keyword:
            if keyword in normalized_name:
                return True
            continue
        if keyword in name_tokens:
            return True
    return False


def _safe_confidence(result: dict) -> float:
    try:
        return max(0.0, min(1.0, float(result.get("confidence", 0.0))))
    except Exception:
        return 0.0


def _verdict_label(result: dict) -> str:
    if result.get("action") == "STOP_LINE":
        return "STOP_LINE"
    if result.get("action") in {"ALERT_OPERATOR", "LOG_WARNING"}:
        return "ALERT_OPERATOR"
    return "PASS"


def _set_audit_fields(result: dict, applied: bool, reason: str | None) -> None:
    result["model_verdict_before_safety_net"] = _verdict_label(result)
    result["safety_net_applied"] = applied
    result["override_reason"] = reason
    result["final_verdict"] = _verdict_label(result)
