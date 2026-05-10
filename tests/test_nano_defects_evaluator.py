import importlib.util
from pathlib import Path


_EVALUATOR_PATH = Path(__file__).resolve().parents[1] / "scripts" / "evaluate_nano_defects.py"
_SPEC = importlib.util.spec_from_file_location("evaluate_nano_defects", _EVALUATOR_PATH)
evaluator = importlib.util.module_from_spec(_SPEC)
assert _SPEC and _SPEC.loader
_SPEC.loader.exec_module(evaluator)


def test_nano_defects_tuned_policy_reduces_false_pass_risk():
    baseline, safe, balanced, comparison = evaluator._run_evaluation()

    assert baseline["total_images"] > 0
    assert baseline["input_scope"] == "raw_unannotated_only"
    assert safe["false_pass_count"] <= baseline["false_pass_count"]
    assert balanced["false_pass_count"] <= baseline["false_pass_count"]
    assert safe["defect_review_recall"] >= baseline["defect_review_recall"]
    assert balanced["defect_review_recall"] >= baseline["defect_review_recall"]
    assert balanced["clean_pass_accuracy"] >= safe["clean_pass_accuracy"]
    assert comparison["no_lora_training_claim"] is True
    assert "Adapter/LoRA training remains pending" in comparison["truth_note"]
