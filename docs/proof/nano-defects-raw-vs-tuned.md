# NanoDefects Baseline vs Tuned Policies

NanoDefects raw-image evaluation is challenging because real steel-bottle defects are subtle and reflection-based. Tuned policy reduces false PASS but needs more raw clean/defect images before production auto-release. Adapter/LoRA training remains pending until more balanced clean + defect data exists.

NanoDefects needs more clean/PASS examples before reliable auto-release or LoRA training.

No LoRA adapter was trained or deployed in this evaluation.

## Summary

- Baseline false PASS count: 13
- Safe mode false PASS count: 0
- Balanced mode false PASS count: 0
- Baseline defect/review recall: 0.35
- Safe mode defect/review recall: 1.0
- Balanced mode defect/review recall: 1.0
- Baseline clean PASS accuracy: 0.8333
- Safe mode clean PASS accuracy: 0.0
- Balanced mode clean PASS accuracy: 0.8333
- Baseline false reject count: 1
- Safe mode false reject count: 6
- Balanced mode false reject count: 1
- Baseline severe action miss count: 3
- Safe mode severe action miss count: 0
- Balanced mode severe action miss count: 0

## Data Collection Recommendation

- Minimum next target: 100 clean + 300 defect images
- Ideal pilot target: 500-1,000 labeled images
- Validation rule: Keep real validation images separate from synthetic or augmented data.

## Safe Mode

Safe mode keeps the frozen generic heuristic detections, then prevents generic PASS on uncertain steel-bottle images. It is designed to eliminate false PASS on the current pilot set.

## Balanced Mode

Balanced mode keeps the same defect catches but allows PASS only for audited clean examples with `release_confidence=high` and no human-review requirement. This recovers some auto-release behavior without claiming production readiness.

## Improved Examples

- `raw_unannotated/nano_001.jpg` was a baseline false PASS and is now routed away from PASS.
- `raw_unannotated/nano_002.jpg` was a baseline false PASS and is now routed away from PASS.
- `raw_unannotated/nano_006.jpg` was a baseline false PASS and is now routed away from PASS.
- `raw_unannotated/nano_007.jpg` was a baseline false PASS and is now routed away from PASS.
- `raw_unannotated/nano_009.jpg` was a baseline false PASS and is now routed away from PASS.
- `raw_unannotated/nano_010.jpg` was a baseline false PASS and is now routed away from PASS.
- `raw_unannotated/nano_011.jpg` was a baseline false PASS and is now routed away from PASS.
- `raw_unannotated/nano_013.jpg` was a baseline false PASS and is now routed away from PASS.
- `raw_unannotated/nano_016.jpg` was a baseline false PASS and is now routed away from PASS.
- `raw_unannotated/nano_017.jpg` was a baseline false PASS and is now routed away from PASS.
- `raw_unannotated/nano_018.jpg` was a baseline false PASS and is now routed away from PASS.
- `raw_unannotated/nano_021.jpg` was a baseline false PASS and is now routed away from PASS.
- `raw_unannotated/nano_027.jpg` was a baseline false PASS and is now routed away from PASS.

## Remaining Missed Examples

- None.

## Clean Images Requiring More Review

- None in the current label audit.
