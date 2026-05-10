# NanoDefects Baseline Evaluation

- Evaluation mode: `raw_unannotated_deterministic_local_visual_heuristic_baseline`
- Evaluation policy: Only raw/unannotated images are evaluated. Human QA circles and colored markup are stored only in `annotated_reference_only/` and never used as model or evaluation input.
- Live Qwen-VL used: `False`
- Total images: 26
- Clean/PASS images: 6
- Defect/review images: 20
- Clean PASS accuracy: 0.8333
- DEFECT/REVIEW recall: 0.35
- Operational binary accuracy: 0.4615
- Exact action accuracy: 0.3077
- False PASS count: 13
- False reject count: 1
- Severe action miss count: 3
- Average confidence: 0.6538
- Metric change explanation: Earlier runs mixed raw images with annotated/circled references. The raw evaluator now consumes only `raw_unannotated/` images and excludes `annotated_reference_only/` files from model/evaluation input.

## Readiness

- Adapter experiment ready: `False`
- Recommended target: PASS vs DEFECT/REVIEW with conservative false-PASS policy
- Warning: Pilot dataset is usable for baseline and adapter prototype planning, but has too few clean/PASS examples for reliable auto-release or LoRA training.

## Missed Defect Examples

- `raw_unannotated/nano_001.jpg` expected `ALERT_OPERATOR` / `unknown_defect`, predicted `PASS`.
- `raw_unannotated/nano_002.jpg` expected `ALERT_OPERATOR` / `unknown_defect`, predicted `PASS`.
- `raw_unannotated/nano_006.jpg` expected `REJECT` / `broad_shallow_dent`, predicted `PASS`.
- `raw_unannotated/nano_007.jpg` expected `ALERT_OPERATOR` / `base_region_defect`, predicted `PASS`.
- `raw_unannotated/nano_009.jpg` expected `ALERT_OPERATOR` / `unknown_defect`, predicted `PASS`.
- `raw_unannotated/nano_010.jpg` expected `ALERT_OPERATOR` / `reflection_deformation`, predicted `PASS`.
- `raw_unannotated/nano_011.jpg` expected `ALERT_OPERATOR` / `broad_shallow_dent`, predicted `PASS`.
- `raw_unannotated/nano_013.jpg` expected `ALERT_OPERATOR` / `unknown_defect`, predicted `PASS`.
- `raw_unannotated/nano_016.jpg` expected `ALERT_OPERATOR` / `unknown_defect`, predicted `PASS`.
- `raw_unannotated/nano_017.jpg` expected `ALERT_OPERATOR` / `reflection_deformation`, predicted `PASS`.
- `raw_unannotated/nano_018.jpg` expected `REJECT` / `coating_damage`, predicted `PASS`.
- `raw_unannotated/nano_021.jpg` expected `ALERT_OPERATOR` / `reflection_deformation`, predicted `PASS`.
- `raw_unannotated/nano_027.jpg` expected `ALERT_OPERATOR` / `unknown_defect`, predicted `PASS`.

## Per-Defect-Type Summary

- `base_region_defect`: total=2, binary_accuracy=0.5, exact_action_accuracy=0.0
- `broad_shallow_dent`: total=2, binary_accuracy=0.0, exact_action_accuracy=0.0
- `clean`: total=6, binary_accuracy=0.8333, exact_action_accuracy=0.8333
- `coating_damage`: total=1, binary_accuracy=0.0, exact_action_accuracy=0.0
- `creased_dent`: total=1, binary_accuracy=1.0, exact_action_accuracy=0.0
- `internal_dent`: total=2, binary_accuracy=1.0, exact_action_accuracy=0.5
- `reflection_deformation`: total=3, binary_accuracy=0.0, exact_action_accuracy=0.0
- `scratch_scuff`: total=2, binary_accuracy=1.0, exact_action_accuracy=1.0
- `unknown_defect`: total=7, binary_accuracy=0.1429, exact_action_accuracy=0.0
