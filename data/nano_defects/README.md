# NanoDefects Steel Bottle QA Dataset

NanoDefects contains real factory QA images from a steel bottle / thermos / food jar manufacturing line.

## Source

- Origin: real NanoDefects bottle factory QA images
- Product family: steel bottles, thermos bottles, food jars, coated bottles
- Raw evaluation images: 26
- Annotated reference-only images: 24
- Clean/PASS raw examples: 6
- Defect/review raw examples: 20

## Folder Structure

```text
raw_unannotated/              # model and evaluation input
annotated_reference_only/     # human-marked/circled references; never used as model input
labels.json                   # labels for raw_unannotated only
annotated_reference_labels.json
splits/
```

Annotated/circled QA images are retained only as label references. They are excluded from `labels.json`, train/val/test splits, and all baseline/tuned evaluations because using markup as visual evidence inflates defect recall and fails on real raw factory images.

## Defect Taxonomy

- small_dent
- impact_pit
- broad_shallow_dent
- reflection_deformation
- creased_dent
- scratch_scuff
- coating_damage
- internal_dent
- base_region_defect
- shoulder_deformation
- rim_thread_defect
- unknown_defect
- clean

## Intended Use

This dataset is intended for raw-image VisionGuard baseline evaluation, prompt/safety tuning, adapter readiness analysis, and a future factory-specific LoRA/adapter experiment.

## Limitations

This is a small pilot dataset. The raw-image subset is enough for serious baseline measurement and QA workflow design, but not enough for a reliable conveyor-belt production model. The first target is PASS vs DEFECT/REVIEW with a conservative false-PASS policy, not perfect fine-grained classification.

NanoDefects currently has only 6 raw clean/PASS examples. More raw clean examples are required before reliable auto-release or LoRA training.

Raw steel-bottle evaluation is challenging because many real defects are subtle and reflection-based: warped reflection bands, tiny point dents, impact pits, shoulder dents, base defects, rim/thread/internal dents, scratches/scuffs, and coating damage.

## Data Collection Recommendation

- Minimum next target: 100 clean + 300 defect images.
- Ideal pilot target: 500-1,000 labeled images.
- Keep the real validation set separate from synthetic or augmented data.

## Product Path

- Version 1: operator-assisted QA assistant using NanoDefects baseline.
- Version 2: factory-specific adapter/detector after collecting 300-500 labeled images.
- Version 3: conveyor deployment with fixed camera, controlled lighting, auto-reject, and feedback loop.

## Training Readiness

Adapter training should not start blindly. Validate that clean/PASS examples are sufficient and that duplicate images of the same bottle are kept in the same split where possible. If clean images remain underrepresented, collect more PASS examples before training a PASS/FAIL model.
