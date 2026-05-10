from pathlib import Path


def mock_inference_for_label(label: str) -> dict:
    normalized = label.lower()

    if "broken_large" in normalized:
        return {
            "defect_detected": True,
            "defect_type": "crack",
            "defect_category": "structural crack",
            "severity": "critical",
            "confidence": 0.94,
            "location": "upper-left bottle neck",
            "region": {
                "horizontal": "left",
                "vertical": "upper",
            },
            "action": "STOP_LINE",
            "visual_explanation": "A visible fracture line appears near the upper-left neck region of the bottle.",
            "possible_causes": [
                "thermal stress during cooling",
                "excess pressure during molding",
                "impact during handling",
            ],
            "recommended_fix": [
                "remove this item from the production line",
                "inspect nearby batch items",
                "check molding pressure and cooling temperature",
            ],
            "prevention": [
                "calibrate cooling temperature",
                "reduce mechanical impact during transfer",
                "add automated inspection after cooling",
            ],
            "factory_owner_summary": "A critical structural crack was detected near the bottle neck. Stop the line and inspect the nearby batch before continuing production.",
            "processing_ms": 243,
            "model_name": "Qwen/Qwen2.5-VL-7B-Instruct",
        }

    if "broken_small" in normalized:
        return {
            "defect_detected": True,
            "defect_type": "broken_part",
            "defect_category": "broken edge",
            "severity": "warning",
            "confidence": 0.91,
            "location": "lower-right bottle edge",
            "region": {
                "horizontal": "right",
                "vertical": "lower",
            },
            "action": "ALERT_OPERATOR",
            "visual_explanation": "A localized edge break is visible near the lower-right side of the bottle.",
            "possible_causes": [
                "impact during transfer",
                "insufficient edge strength after molding",
                "contact damage in packaging",
            ],
            "recommended_fix": [
                "remove the damaged item from the batch",
                "inspect adjacent items for edge damage",
                "review transfer and packaging contact points",
            ],
            "prevention": [
                "reduce impact during conveyor transfer",
                "improve handling guards at bottlenecks",
                "add inspection before packaging",
            ],
            "factory_owner_summary": "A warning-level broken edge was detected near the lower-right bottle area. Remove the item and review transfer handling before defects spread through the batch.",
            "processing_ms": 228,
            "model_name": "Qwen/Qwen2.5-VL-7B-Instruct",
        }

    if "contamination" in normalized:
        return {
            "defect_detected": True,
            "defect_type": "contamination",
            "defect_category": "contamination mark",
            "severity": "warning",
            "confidence": 0.89,
            "location": "middle bottle body",
            "region": {
                "horizontal": "center",
                "vertical": "middle",
            },
            "action": "ALERT_OPERATOR",
            "visual_explanation": "Foreign material appears visible inside the middle body region of the bottle.",
            "possible_causes": [
                "residue left during cleaning",
                "airborne contamination during filling",
                "material handling contamination",
            ],
            "recommended_fix": [
                "remove the contaminated item from the line",
                "inspect nearby units from the same batch",
                "check cleaning and filling stations for residue",
            ],
            "prevention": [
                "increase cleaning verification frequency",
                "improve enclosure around filling area",
                "add post-fill automated inspection",
            ],
            "factory_owner_summary": "Contamination was detected in the bottle body. Remove the item, inspect the nearby batch, and review cleaning and filling controls.",
            "processing_ms": 251,
            "model_name": "Qwen/Qwen2.5-VL-7B-Instruct",
        }

    return {
        "defect_detected": False,
        "defect_type": "none",
        "defect_category": "none",
        "severity": "ok",
        "confidence": 0.97,
        "location": "none",
        "region": {
            "horizontal": "none",
            "vertical": "none",
        },
        "action": "PASS",
        "visual_explanation": "No visible manufacturing defect is present in the sample.",
        "possible_causes": [],
        "recommended_fix": [],
        "prevention": [
            "maintain current process controls",
            "continue periodic inspection sampling",
        ],
        "factory_owner_summary": "No visible defect was detected. The product appears suitable to pass while maintaining normal quality controls.",
        "processing_ms": 205,
        "model_name": "Qwen/Qwen2.5-VL-7B-Instruct",
    }


def mock_inference_for_path(image_path: str) -> dict:
    filename = Path(image_path).name.lower()
    return mock_inference_for_label(filename)
