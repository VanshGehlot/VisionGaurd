from __future__ import annotations

from copy import deepcopy

from PIL import Image
from requests import Timeout

from model.qwen_client import inspect_pil_image_second_pass
from utils.visual_heuristics import detect_dark_speckles

LOW_CONFIDENCE_PASS_THRESHOLD = 0.5


def verify_pass_result(
    first_pass_result: dict,
    image: Image.Image,
    reviewer=inspect_pil_image_second_pass,
    speckle_detector=detect_dark_speckles,
    surface_mark_detector=None,
    inspection_profile: str | None = None,
) -> dict:
    result = deepcopy(first_pass_result)
    result["pass_verification_applied"] = False
    result["pass_verification_reason"] = None

    if result.get("defect_detected") or result.get("severity") != "ok" or result.get("action") != "PASS":
        result["second_pass_verdict"] = "skipped"
        result["second_pass_called"] = False
        result["speckle_review_flagged"] = False
        result["final_verdict"] = _verdict_label(result)
        return result

    speckles = speckle_detector(image)
    result["pass_verification_applied"] = True
    result["second_pass_called"] = False
    result["speckle_review_flagged"] = bool(getattr(speckles, "flagged", False))

    if getattr(speckles, "flagged", False):
        result["second_pass_verdict"] = "skipped"
        return _review_result_from_heuristic(result, speckles)

    if surface_mark_detector is not None:
        surface_marks = surface_mark_detector(image)
        result["surface_mark_review_flagged"] = bool(getattr(surface_marks, "flagged", False))
        if getattr(surface_marks, "flagged", False):
            result["second_pass_verdict"] = "skipped"
            return _review_result_from_surface_marks(result, surface_marks)
    else:
        result["surface_mark_review_flagged"] = False

    try:
        result["second_pass_called"] = True
        try:
            second_pass = reviewer(image, inspection_profile=inspection_profile)
        except TypeError:
            second_pass = reviewer(image)
    except Timeout:
        return _fallback_after_second_pass_timeout(result, speckles)
    except TimeoutError:
        return _fallback_after_second_pass_timeout(result, speckles)

    second_pass_failed = (
        second_pass.get("defect_detected")
        or second_pass.get("severity") != "ok"
        or second_pass.get("action") != "PASS"
    )

    if second_pass_failed:
        reviewed = deepcopy(second_pass)
        reviewed["pass_verification_applied"] = True
        reviewed["pass_verification_reason"] = "strict second-pass review detected visible anomaly"
        reviewed["second_pass_verdict"] = "failed"
        reviewed["second_pass_called"] = True
        reviewed["speckle_review_flagged"] = bool(getattr(speckles, "flagged", False))
        reviewed["final_verdict"] = _verdict_label(reviewed)
        return reviewed

    result["second_pass_verdict"] = "passed"
    result["pass_verification_reason"] = "first and second pass agreed clean"
    result["final_verdict"] = "PASS"
    return result


def _fallback_after_second_pass_timeout(result: dict, speckles: object) -> dict:
    fallback = deepcopy(result)
    fallback["pass_verification_applied"] = True
    fallback["second_pass_verdict"] = "timeout"
    fallback["second_pass_called"] = True
    fallback["speckle_review_flagged"] = bool(getattr(speckles, "flagged", False))
    fallback["pass_verification_reason"] = "second_pass_timeout"

    if getattr(speckles, "flagged", False):
        reviewed = _review_result_from_heuristic(fallback, speckles)
        reviewed["second_pass_verdict"] = "timeout"
        reviewed["pass_verification_reason"] = "second_pass_timeout"
        return reviewed

    if _safe_confidence(fallback) < LOW_CONFIDENCE_PASS_THRESHOLD:
        reviewed = _review_result_from_low_confidence(fallback)
        reviewed["second_pass_verdict"] = "timeout"
        return reviewed

    fallback["final_verdict"] = "PASS"
    return fallback


def _review_result_from_heuristic(result: dict, speckles: object) -> dict:
    reviewed = deepcopy(result)
    reviewed.update(
        {
            "defect_detected": False,
            "defect_type": "contamination",
            "defect_category": "surface contamination",
            "severity": "warning",
            "confidence": min(float(reviewed.get("confidence") or 0.68), 0.78),
            "location": "visible product surface",
            "region": {"horizontal": "unknown", "vertical": "unknown"},
            "action": "ALERT_OPERATOR",
            "visual_explanation": (
                "A visual heuristic detected multiple dark speckles or dirt-like clusters on the bottle surface "
                "during PASS verification."
            ),
            "possible_causes": [
                "surface contamination or residue",
                "dirt-like clusters on the visible bottle surface",
                "inspection review triggered by dark speckle heuristic",
            ],
            "recommended_fix": [
                "route this item to operator review",
                "wipe and re-image the surface if safe to do so",
                "inspect nearby items for similar contamination",
            ],
            "prevention": [
                "improve cleaning and handling before final inspection",
                "stabilize lighting to reduce contamination ambiguity",
                "capture more defect examples for model adaptation",
            ],
            "factory_owner_summary": (
                "Operator review is required because the PASS verification layer detected multiple dark "
                "speckle-like anomalies on the product surface."
            ),
            "pass_verification_reason": "visible_contamination_or_speckle_anomaly",
            "safety_net_applied": True,
            "override_reason": "speckle_contamination_detected",
            "final_verdict": "ALERT_OPERATOR",
            "heuristic_bbox": list(getattr(speckles, "bbox", None) or []),
            "heuristic_confidence": getattr(speckles, "confidence", "medium"),
        }
    )
    return reviewed


def _review_result_from_surface_marks(result: dict, surface_marks: object) -> dict:
    reviewed = deepcopy(result)
    reviewed.update(
        {
            "defect_detected": True,
            "defect_type": "scratch",
            "defect_category": "cosmetic scratch",
            "severity": "warning",
            "confidence": min(float(reviewed.get("confidence") or 0.7), 0.82),
            "location": "visible product surface",
            "region": {"horizontal": "unknown", "vertical": "unknown"},
            "action": "ALERT_OPERATOR",
            "visual_explanation": (
                "PASS verification detected many diagonal scratch-like surface marks on the product body."
            ),
            "possible_causes": [
                "abrasive handling during packing or transport",
                "contact with rough conveyor or tooling surfaces",
                "surface wear on reusable product inventory",
            ],
            "recommended_fix": [
                "route this item to operator review",
                "inspect the surface under stable lighting",
                "check nearby batch items for similar wear",
            ],
            "prevention": [
                "reduce abrasive contact during transfer",
                "add soft guides or separators on the line",
                "monitor packaging and handling fixtures for wear points",
            ],
            "factory_owner_summary": (
                "Operator review is required because the PASS verification layer detected scratch-like "
                "surface wear that may fail cosmetic quality standards."
            ),
            "pass_verification_reason": "visible_scratch_or_surface_wear_anomaly",
            "safety_net_applied": True,
            "override_reason": "surface_mark_anomaly_detected",
            "final_verdict": "ALERT_OPERATOR",
            "heuristic_bbox": list(getattr(surface_marks, "bbox", None) or []),
            "heuristic_confidence": getattr(surface_marks, "confidence", "medium"),
        }
    )
    return reviewed


def _review_result_from_low_confidence(result: dict) -> dict:
    reviewed = deepcopy(result)
    reviewed.update(
        {
            "defect_detected": False,
            "defect_type": "unknown",
            "defect_category": "unknown",
            "severity": "warning",
            "location": "requires operator review",
            "region": {"horizontal": "unknown", "vertical": "unknown"},
            "action": "ALERT_OPERATOR",
            "visual_explanation": "Second-pass verification timed out and the first-pass PASS confidence was low.",
            "factory_owner_summary": "Operator review is required because the verification layer could not confirm a clean PASS.",
            "pass_verification_reason": "second_pass_timeout_low_confidence",
            "safety_net_applied": True,
            "override_reason": "second_pass_timeout_low_confidence",
            "final_verdict": "ALERT_OPERATOR",
        }
    )
    return reviewed


def _safe_confidence(result: dict) -> float:
    try:
        return max(0.0, min(1.0, float(result.get("confidence", 0.0))))
    except Exception:
        return 0.0


def _verdict_label(result: dict | None) -> str | None:
    if not result:
        return None
    if result.get("action") == "STOP_LINE":
        return "STOP_LINE"
    if result.get("action") in {"ALERT_OPERATOR", "LOG_WARNING"}:
        return "ALERT_OPERATOR"
    return "PASS"
