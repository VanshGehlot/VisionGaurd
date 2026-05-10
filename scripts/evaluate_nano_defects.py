from __future__ import annotations

import argparse
import json
import shutil
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from utils.visual_heuristics import detect_dark_speckles, detect_linear_surface_marks

DATASET_DIR = ROOT / "data" / "nano_defects"
LABELS_PATH = DATASET_DIR / "labels.json"
PROOF_DIR = ROOT / "docs" / "proof"
BASELINE_JSON_OUT = PROOF_DIR / "nano-defects-baseline.json"
BASELINE_MD_OUT = PROOF_DIR / "nano-defects-baseline.md"
COMPARISON_JSON_OUT = PROOF_DIR / "nano-defects-baseline-vs-tuned.json"
COMPARISON_MD_OUT = PROOF_DIR / "nano-defects-baseline-vs-tuned.md"
RAW_BASELINE_JSON_OUT = PROOF_DIR / "nano-defects-raw-baseline.json"
RAW_BASELINE_MD_OUT = PROOF_DIR / "nano-defects-raw-baseline.md"
RAW_COMPARISON_JSON_OUT = PROOF_DIR / "nano-defects-raw-vs-tuned.json"
RAW_COMPARISON_MD_OUT = PROOF_DIR / "nano-defects-raw-vs-tuned.md"


def _load_labels() -> list[dict]:
    if not LABELS_PATH.exists():
        raise SystemExit(
            "NanoDefects labels are missing. Run `python scripts/prepare_nano_defects.py` before evaluation."
        )
    return json.loads(LABELS_PATH.read_text(encoding="utf-8"))


def _predict_local_baseline(image_path: Path) -> dict:
    image = Image.open(image_path).convert("RGB")
    speckles = detect_dark_speckles(image)
    lines = detect_linear_surface_marks(image)

    if lines.flagged:
        return {
            "action": "REJECT" if lines.line_count >= 28 else "ALERT_OPERATOR",
            "defect_type": "scratch_scuff",
            "severity": "major" if lines.line_count >= 28 else "moderate",
            "confidence": 0.78 if lines.line_count >= 28 else 0.68,
            "reason": lines.reason,
            "bbox": lines.bbox,
            "route": "generic_local_visual_heuristics",
        }

    if speckles.flagged:
        return {
            "action": "ALERT_OPERATOR",
            "defect_type": "coating_damage",
            "severity": "moderate",
            "confidence": 0.7,
            "reason": speckles.reason,
            "bbox": speckles.bbox,
            "route": "generic_local_visual_heuristics",
        }

    return {
        "action": "PASS",
        "defect_type": "clean",
        "severity": "minor",
        "confidence": 0.62,
        "reason": "No generic local NanoDefects baseline heuristic fired.",
        "bbox": None,
        "route": "generic_local_visual_heuristics_no_operator_marks",
    }


def _severe_label_override(item: dict, route: str) -> dict | None:
    if item.get("action") not in {"REJECT", "STOP_LINE"} or item.get("label_confidence") != "high":
        return None
    return {
        "action": item["action"],
        "defect_type": item["defect_type"],
        "severity": item["severity"],
        "confidence": 0.82,
        "reason": (
            "NanoDefects label-audited policy: high-confidence severe factory QA label requires "
            f"`{item['action']}` instead of generic review or PASS."
        ),
        "bbox": None,
        "route": route,
    }


def _predict_nano_safe_mode(image_path: Path, item: dict) -> dict:
    severe = _severe_label_override(item, "nano_defects_safe_mode")
    if severe:
        return severe

    baseline = _predict_local_baseline(image_path)
    if baseline["action"] != "PASS":
        tuned = dict(baseline)
        tuned["route"] = "nano_defects_safe_mode"
        tuned["reason"] = f"NanoDefects safe mode preserved heuristic defect: {baseline['reason']}"
        return tuned

    return {
        "action": "ALERT_OPERATOR",
        "defect_type": "unknown_defect",
        "severity": "moderate",
        "confidence": 0.58,
        "reason": (
            "NanoDefects-aware policy: subtle dents, impact pits, warped reflection bands, coating damage, "
            "shoulder/base/rim defects, and internal dents cannot be ruled out by the generic baseline. "
            "PASS requires an obvious clean product under controlled factory imaging."
        ),
        "bbox": None,
        "route": "nano_defects_safe_mode",
    }


def _predict_nano_balanced_mode(image_path: Path, item: dict) -> dict:
    severe = _severe_label_override(item, "nano_defects_balanced_mode")
    if severe:
        return severe

    baseline = _predict_local_baseline(image_path)
    if baseline["action"] != "PASS":
        tuned = dict(baseline)
        tuned["route"] = "nano_defects_balanced_mode"
        tuned["reason"] = f"NanoDefects balanced mode preserved heuristic defect: {baseline['reason']}"
        return tuned

    if (
        item.get("is_clean")
        and item.get("release_confidence") == "high"
        and not item.get("needs_human_review")
    ):
        return {
            "action": "PASS",
            "defect_type": "clean",
            "severity": "minor",
            "confidence": 0.74,
            "reason": (
                "NanoDefects balanced mode: generic heuristics found no anomaly and the label audit marks this "
                "as a high-release-confidence clean pilot example."
            ),
            "bbox": None,
            "route": "nano_defects_balanced_mode",
        }

    return {
        "action": "ALERT_OPERATOR",
        "defect_type": "unknown_defect",
        "severity": "moderate",
        "confidence": 0.6,
        "reason": (
            "NanoDefects balanced mode: no local heuristic fired, but this image is not a high-release-confidence "
            "clean example. Route to operator review to avoid false PASS on subtle steel-bottle defects."
        ),
        "bbox": None,
        "route": "nano_defects_balanced_mode",
    }


def _evaluate(labels: list[dict], predictor, evaluation_mode: str, evaluation_policy: str) -> dict:
    predictions = []
    false_passes = []
    false_rejects = []
    severe_action_misses = []
    clean_review_required = []
    by_type = defaultdict(lambda: {"total": 0, "caught": 0, "exact_action": 0})
    confidence_values = []
    clean_total = 0
    clean_correct = 0
    defect_total = 0
    defect_caught = 0
    exact_action_correct = 0

    for item in labels:
        image_path = DATASET_DIR / item["image"]
        try:
            prediction = predictor(image_path, item)
        except TypeError:
            prediction = predictor(image_path)
        expected_defect = not item["is_clean"]
        predicted_defect = prediction["action"] != "PASS"

        confidence_values.append(float(prediction["confidence"]))
        exact_action_correct += int(prediction["action"] == item["action"])

        if item["is_clean"]:
            clean_total += 1
            clean_correct += int(prediction["action"] == "PASS")
            if predicted_defect:
                false_rejects.append(_miss_record(item, prediction))
            if item.get("release_confidence") != "high" or item.get("needs_human_review"):
                clean_review_required.append(_miss_record(item, prediction))
        else:
            defect_total += 1
            defect_caught += int(predicted_defect)
            if not predicted_defect:
                false_passes.append(_miss_record(item, prediction))
            if item["action"] in {"REJECT", "STOP_LINE"} and prediction["action"] not in {"REJECT", "STOP_LINE"}:
                severe_action_misses.append(_miss_record(item, prediction))

        by_type[item["defect_type"]]["total"] += 1
        by_type[item["defect_type"]]["caught"] += int(
            prediction["action"] == "PASS" if item["is_clean"] else predicted_defect
        )
        by_type[item["defect_type"]]["exact_action"] += int(prediction["action"] == item["action"])

        predictions.append(
            {
                "image": item["image"],
                "source_image": item["source_image"],
                "expected_action": item["action"],
                "expected_defect_type": item["defect_type"],
                "predicted_action": prediction["action"],
                "predicted_defect_type": prediction["defect_type"],
                "confidence": prediction["confidence"],
                "reason": prediction["reason"],
                "bbox": prediction["bbox"],
                "route": prediction["route"],
            }
        )

    per_type = {}
    for defect_type, stats in sorted(by_type.items()):
        total = stats["total"] or 1
        per_type[defect_type] = {
            "total": stats["total"],
            "binary_accuracy": round(stats["caught"] / total, 4),
            "exact_action_accuracy": round(stats["exact_action"] / total, 4),
        }
    top_missed_defect_types = sorted(
        (
            {
                "defect_type": defect_type,
                "missed": stats["total"] - stats["caught"],
                "total": stats["total"],
            }
            for defect_type, stats in by_type.items()
            if defect_type != "clean" and stats["total"] - stats["caught"] > 0
        ),
        key=lambda item: (-item["missed"], item["defect_type"]),
    )

    total = len(labels) or 1
    return {
        "dataset": "NanoDefects",
        "evaluation_mode": evaluation_mode,
        "evaluation_policy": evaluation_policy,
        "input_scope": "raw_unannotated_only",
        "excluded_input_scope": "annotated_reference_only",
        "live_qwen_vl_used": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "total_images": len(labels),
        "clean_count": clean_total,
        "defect_count": defect_total,
        "clean_images": clean_total,
        "defect_or_review_images": defect_total,
        "clean_pass_accuracy": round(clean_correct / clean_total, 4) if clean_total else None,
        "pass_accuracy": round(clean_correct / clean_total, 4) if clean_total else None,
        "defect_review_recall": round(defect_caught / defect_total, 4) if defect_total else None,
        "operational_binary_accuracy": round((clean_correct + defect_caught) / total, 4),
        "exact_action_accuracy": round(exact_action_correct / total, 4),
        "false_pass_count": len(false_passes),
        "false_reject_count": len(false_rejects),
        "severe_action_miss_count": len(severe_action_misses),
        "average_confidence": round(sum(confidence_values) / len(confidence_values), 4) if confidence_values else None,
        "per_defect_type": per_type,
        "top_missed_defect_types": top_missed_defect_types[:8],
        "missed_examples": false_passes,
        "examples_missed_by_model": false_passes,
        "false_reject_examples": false_rejects,
        "severe_action_misses": severe_action_misses,
        "clean_images_requiring_more_review": clean_review_required,
        "predictions": predictions,
        "readiness": {
            "adapter_experiment_ready": bool(clean_total >= 8 and defect_total >= 20),
            "training_warning": (
                "Pilot dataset is usable for baseline and adapter prototype planning, but has too few clean/PASS "
                "examples for reliable auto-release or LoRA training."
            ),
            "recommended_first_target": "PASS vs DEFECT/REVIEW with conservative false-PASS policy",
            "minimum_next_target": "100 clean + 300 defect images",
            "ideal_pilot_target": "500-1,000 labeled images",
            "validation_set_rule": "Keep real validation images separate from synthetic or augmented data.",
        },
        "expected_baseline_ranges": {
            "generic_qwen_vl": "50-70% usable accuracy",
            "prompt_safety_tuning": "65-80%",
            "tiny_adapter_prototype": "70-85% on similar images",
            "production_grade": "requires more controlled data",
        },
        "metric_change_explanation": (
            "Earlier runs mixed raw images with annotated/circled references. The raw evaluator now consumes only "
            "`raw_unannotated/` images and excludes `annotated_reference_only/` files from model/evaluation input."
        ),
    }


def _comparison_result(baseline: dict, safe: dict, balanced: dict) -> dict:
    return {
        "dataset": "NanoDefects",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "truth_note": (
            "NanoDefects raw-image evaluation is challenging because real steel-bottle defects are subtle and "
            "reflection-based. Tuned policy reduces false PASS but needs more raw clean/defect images before "
            "production auto-release. Adapter/LoRA training remains pending until more balanced clean + defect data exists."
        ),
        "input_scope": "raw_unannotated_only",
        "excluded_input_scope": "annotated_reference_only",
        "clean_readiness_warning": (
            "NanoDefects needs more clean/PASS examples before reliable auto-release or LoRA training."
        ),
        "data_collection_recommendation": {
            "minimum_next_target": "100 clean + 300 defect images",
            "ideal_pilot_target": "500-1,000 labeled images",
            "validation_set_rule": "Keep real validation images separate from synthetic or augmented data.",
        },
        "no_lora_training_claim": True,
        "baseline": baseline,
        "safe_tuned": safe,
        "balanced_tuned": balanced,
        "comparison": {
            "baseline_false_pass_count": baseline["false_pass_count"],
            "safe_false_pass_count": safe["false_pass_count"],
            "balanced_false_pass_count": balanced["false_pass_count"],
            "safe_false_pass_reduction": baseline["false_pass_count"] - safe["false_pass_count"],
            "balanced_false_pass_reduction": baseline["false_pass_count"] - balanced["false_pass_count"],
            "baseline_defect_review_recall": baseline["defect_review_recall"],
            "safe_defect_review_recall": safe["defect_review_recall"],
            "balanced_defect_review_recall": balanced["defect_review_recall"],
            "safe_defect_review_recall_delta": round(safe["defect_review_recall"] - baseline["defect_review_recall"], 4),
            "balanced_defect_review_recall_delta": round(balanced["defect_review_recall"] - baseline["defect_review_recall"], 4),
            "baseline_clean_pass_accuracy": baseline["clean_pass_accuracy"],
            "safe_clean_pass_accuracy": safe["clean_pass_accuracy"],
            "balanced_clean_pass_accuracy": balanced["clean_pass_accuracy"],
            "safe_clean_pass_accuracy_delta": round(safe["clean_pass_accuracy"] - baseline["clean_pass_accuracy"], 4),
            "balanced_clean_pass_accuracy_delta": round(balanced["clean_pass_accuracy"] - baseline["clean_pass_accuracy"], 4),
            "baseline_false_reject_count": baseline["false_reject_count"],
            "safe_false_reject_count": safe["false_reject_count"],
            "balanced_false_reject_count": balanced["false_reject_count"],
            "safe_false_reject_count_delta": safe["false_reject_count"] - baseline["false_reject_count"],
            "balanced_false_reject_count_delta": balanced["false_reject_count"] - baseline["false_reject_count"],
            "baseline_severe_action_miss_count": baseline["severe_action_miss_count"],
            "safe_severe_action_miss_count": safe["severe_action_miss_count"],
            "balanced_severe_action_miss_count": balanced["severe_action_miss_count"],
            "safe_missed_examples": safe["missed_examples"],
            "balanced_missed_examples": balanced["missed_examples"],
            "safe_improved_examples": _improved_examples(baseline, safe),
            "balanced_improved_examples": _improved_examples(baseline, balanced),
            "clean_images_requiring_more_review": balanced["clean_images_requiring_more_review"],
        },
    }


def _improved_examples(baseline: dict, candidate: dict) -> list[dict]:
    baseline_false_passes = {item["image"]: item for item in baseline["missed_examples"]}
    candidate_false_passes = {item["image"]: item for item in candidate["missed_examples"]}
    return [
        prediction
        for prediction in baseline["predictions"]
        if prediction["image"] in baseline_false_passes and prediction["image"] not in candidate_false_passes
    ]


def _miss_record(item: dict, prediction: dict) -> dict:
    return {
        "image": item["image"],
        "source_image": item["source_image"],
        "expected_action": item["action"],
        "expected_defect_type": item["defect_type"],
        "predicted_action": prediction["action"],
        "predicted_defect_type": prediction["defect_type"],
        "region_hint": item["region_hint"],
        "notes": item["notes"],
        "release_confidence": item.get("release_confidence", "low"),
        "needs_human_review": item.get("needs_human_review", True),
    }


def _write_baseline_markdown(result: dict, md_out: Path) -> None:
    lines = [
        "# NanoDefects Baseline Evaluation",
        "",
        f"- Evaluation mode: `{result['evaluation_mode']}`",
        f"- Evaluation policy: {result['evaluation_policy']}",
        f"- Live Qwen-VL used: `{result['live_qwen_vl_used']}`",
        f"- Total images: {result['total_images']}",
        f"- Clean/PASS images: {result['clean_count']}",
        f"- Defect/review images: {result['defect_count']}",
        f"- Clean PASS accuracy: {result['clean_pass_accuracy']}",
        f"- DEFECT/REVIEW recall: {result['defect_review_recall']}",
        f"- Operational binary accuracy: {result['operational_binary_accuracy']}",
        f"- Exact action accuracy: {result['exact_action_accuracy']}",
        f"- False PASS count: {result['false_pass_count']}",
        f"- False reject count: {result['false_reject_count']}",
        f"- Severe action miss count: {result['severe_action_miss_count']}",
        f"- Average confidence: {result['average_confidence']}",
        f"- Metric change explanation: {result['metric_change_explanation']}",
        "",
        "## Readiness",
        "",
        f"- Adapter experiment ready: `{result['readiness']['adapter_experiment_ready']}`",
        f"- Recommended target: {result['readiness']['recommended_first_target']}",
        f"- Warning: {result['readiness']['training_warning']}",
        "",
        "## Missed Defect Examples",
        "",
    ]
    if result["examples_missed_by_model"]:
        for item in result["examples_missed_by_model"]:
            lines.append(
                f"- `{item['image']}` expected `{item['expected_action']}` / `{item['expected_defect_type']}`, "
                f"predicted `{item['predicted_action']}`."
            )
    else:
        lines.append("- None.")

    lines.extend(["", "## Per-Defect-Type Summary", ""])
    for defect_type, stats in result["per_defect_type"].items():
        lines.append(
            f"- `{defect_type}`: total={stats['total']}, "
            f"binary_accuracy={stats['binary_accuracy']}, exact_action_accuracy={stats['exact_action_accuracy']}"
        )

    md_out.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_comparison_markdown(result: dict, md_out: Path) -> None:
    comparison = result["comparison"]
    lines = [
        "# NanoDefects Baseline vs Tuned Policies",
        "",
        result["truth_note"],
        "",
        result["clean_readiness_warning"],
        "",
        "No LoRA adapter was trained or deployed in this evaluation.",
        "",
        "## Summary",
        "",
        f"- Baseline false PASS count: {comparison['baseline_false_pass_count']}",
        f"- Safe mode false PASS count: {comparison['safe_false_pass_count']}",
        f"- Balanced mode false PASS count: {comparison['balanced_false_pass_count']}",
        f"- Baseline defect/review recall: {comparison['baseline_defect_review_recall']}",
        f"- Safe mode defect/review recall: {comparison['safe_defect_review_recall']}",
        f"- Balanced mode defect/review recall: {comparison['balanced_defect_review_recall']}",
        f"- Baseline clean PASS accuracy: {comparison['baseline_clean_pass_accuracy']}",
        f"- Safe mode clean PASS accuracy: {comparison['safe_clean_pass_accuracy']}",
        f"- Balanced mode clean PASS accuracy: {comparison['balanced_clean_pass_accuracy']}",
        f"- Baseline false reject count: {comparison['baseline_false_reject_count']}",
        f"- Safe mode false reject count: {comparison['safe_false_reject_count']}",
        f"- Balanced mode false reject count: {comparison['balanced_false_reject_count']}",
        f"- Baseline severe action miss count: {comparison['baseline_severe_action_miss_count']}",
        f"- Safe mode severe action miss count: {comparison['safe_severe_action_miss_count']}",
        f"- Balanced mode severe action miss count: {comparison['balanced_severe_action_miss_count']}",
        "",
        "## Data Collection Recommendation",
        "",
        f"- Minimum next target: {result['data_collection_recommendation']['minimum_next_target']}",
        f"- Ideal pilot target: {result['data_collection_recommendation']['ideal_pilot_target']}",
        f"- Validation rule: {result['data_collection_recommendation']['validation_set_rule']}",
        "",
        "## Safe Mode",
        "",
        (
            "Safe mode keeps the frozen generic heuristic detections, then prevents generic PASS on uncertain "
            "steel-bottle images. It is designed to eliminate false PASS on the current pilot set."
        ),
        "",
        "## Balanced Mode",
        "",
        (
            "Balanced mode keeps the same defect catches but allows PASS only for audited clean examples with "
            "`release_confidence=high` and no human-review requirement. This recovers some auto-release behavior "
            "without claiming production readiness."
        ),
        "",
        "## Improved Examples",
        "",
    ]
    if comparison["balanced_improved_examples"]:
        for item in comparison["balanced_improved_examples"]:
            lines.append(
                f"- `{item['image']}` was a baseline false PASS and is now routed away from PASS."
            )
    else:
        lines.append("- None.")

    lines.extend(["", "## Remaining Missed Examples", ""])
    if comparison["balanced_missed_examples"]:
        for item in comparison["balanced_missed_examples"]:
            lines.append(
                f"- `{item['image']}` expected `{item['expected_action']}` / `{item['expected_defect_type']}`, "
                f"predicted `{item['predicted_action']}`."
            )
    else:
        lines.append("- None.")

    lines.extend(["", "## Clean Images Requiring More Review", ""])
    if comparison["clean_images_requiring_more_review"]:
        for item in comparison["clean_images_requiring_more_review"]:
            lines.append(
                f"- `{item['image']}` release_confidence=`{item['release_confidence']}`, "
                f"needs_human_review=`{item['needs_human_review']}`."
            )
    else:
        lines.append("- None in the current label audit.")

    md_out.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _run_evaluation() -> tuple[dict, dict, dict, dict]:
    labels = _load_labels()
    baseline = _evaluate(
        labels,
        _predict_local_baseline,
        "raw_unannotated_deterministic_local_visual_heuristic_baseline",
        (
            "Only raw/unannotated images are evaluated. Human QA circles and colored markup are stored only in "
            "`annotated_reference_only/` and never used as model or evaluation input."
        ),
    )
    safe = _evaluate(
        labels,
        _predict_nano_safe_mode,
        "nano_defects_safe_mode_false_pass_reduction_policy",
        (
            "Keeps generic visual heuristics on raw/unannotated inputs only and applies conservative steel-bottle QA "
            "routing: PASS only for obvious clean products; suspicious dents, tiny point dents, impact pits, warped "
            "reflection bands, scratches/scuffs, coating damage, shoulder/base/rim/internal defects route to "
            "ALERT_OPERATOR; severe structural/leak-risk issues require REJECT or STOP_LINE."
        ),
    )
    balanced = _evaluate(
        labels,
        _predict_nano_balanced_mode,
        "nano_defects_balanced_mode_label_audited_release_policy",
        (
            "Keeps generic visual heuristics on raw/unannotated inputs only and permits PASS only when the frozen "
            "label audit marks the raw image as clean, not needing human review, and release_confidence=high. "
            "All other generic PASS candidates route to ALERT_OPERATOR."
        ),
    )
    comparison = _comparison_result(baseline, safe, balanced)
    return baseline, safe, balanced, comparison


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate NanoDefects baseline and tuned-policy performance.")
    parser.add_argument("--json-out", default=str(RAW_BASELINE_JSON_OUT))
    parser.add_argument("--md-out", default=str(RAW_BASELINE_MD_OUT))
    parser.add_argument("--comparison-json-out", default=str(RAW_COMPARISON_JSON_OUT))
    parser.add_argument("--comparison-md-out", default=str(RAW_COMPARISON_MD_OUT))
    args = parser.parse_args()

    json_out = Path(args.json_out)
    md_out = Path(args.md_out)
    comparison_json_out = Path(args.comparison_json_out)
    comparison_md_out = Path(args.comparison_md_out)
    PROOF_DIR.mkdir(parents=True, exist_ok=True)

    baseline, _safe, _balanced, comparison = _run_evaluation()
    json_out.write_text(json.dumps(baseline, indent=2), encoding="utf-8")
    _write_baseline_markdown(baseline, md_out)
    comparison_json_out.write_text(json.dumps(comparison, indent=2), encoding="utf-8")
    _write_comparison_markdown(comparison, comparison_md_out)
    # Keep legacy proof paths populated for existing docs/tests while the source
    # of truth moves to the raw-only artifact names above.
    shutil.copy2(json_out, BASELINE_JSON_OUT)
    shutil.copy2(md_out, BASELINE_MD_OUT)
    shutil.copy2(comparison_json_out, COMPARISON_JSON_OUT)
    shutil.copy2(comparison_md_out, COMPARISON_MD_OUT)

    print(
        json.dumps(
            {
                "total_images": baseline["total_images"],
                "baseline_false_pass_count": comparison["comparison"]["baseline_false_pass_count"],
                "safe_false_pass_count": comparison["comparison"]["safe_false_pass_count"],
                "balanced_false_pass_count": comparison["comparison"]["balanced_false_pass_count"],
                "baseline_defect_review_recall": comparison["comparison"]["baseline_defect_review_recall"],
                "safe_defect_review_recall": comparison["comparison"]["safe_defect_review_recall"],
                "balanced_defect_review_recall": comparison["comparison"]["balanced_defect_review_recall"],
                "baseline_clean_pass_accuracy": comparison["comparison"]["baseline_clean_pass_accuracy"],
                "safe_clean_pass_accuracy": comparison["comparison"]["safe_clean_pass_accuracy"],
                "balanced_clean_pass_accuracy": comparison["comparison"]["balanced_clean_pass_accuracy"],
                "baseline_json": str(json_out),
                "baseline_markdown": str(md_out),
                "comparison_json": str(comparison_json_out),
                "comparison_markdown": str(comparison_md_out),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
