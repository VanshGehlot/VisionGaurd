# NanoDefects Live Qwen/AMD Baseline

- Live Qwen-VL used: `True`
- Total images: 50
- Completed images: 50
- Error count: 0
- False PASS count: 12
- False reject count: 2
- Severe action miss count: 7
- Defect/review recall: 0.7273
- Clean PASS accuracy: 0.6667

No LoRA adapter was trained or deployed in this evaluation.

## False PASS Examples

- `images/nano_001.jpg` expected `ALERT_OPERATOR` / `unknown_defect`, predicted `PASS` / `none`.
- `images/nano_003.jpg` expected `ALERT_OPERATOR` / `base_region_defect`, predicted `PASS` / `none`.
- `images/nano_006.jpg` expected `REJECT` / `broad_shallow_dent`, predicted `PASS` / `none`.
- `images/nano_009.jpg` expected `ALERT_OPERATOR` / `unknown_defect`, predicted `PASS` / `none`.
- `images/nano_010.jpg` expected `ALERT_OPERATOR` / `reflection_deformation`, predicted `PASS` / `none`.
- `images/nano_011.jpg` expected `ALERT_OPERATOR` / `broad_shallow_dent`, predicted `PASS` / `none`.
- `images/nano_013.jpg` expected `ALERT_OPERATOR` / `unknown_defect`, predicted `PASS` / `none`.
- `images/nano_014.jpg` expected `ALERT_OPERATOR` / `internal_dent`, predicted `PASS` / `none`.
- `images/nano_017.jpg` expected `ALERT_OPERATOR` / `reflection_deformation`, predicted `PASS` / `none`.
- `images/nano_021.jpg` expected `ALERT_OPERATOR` / `reflection_deformation`, predicted `PASS` / `none`.
- `images/nano_040.jpg` expected `ALERT_OPERATOR` / `internal_dent`, predicted `PASS` / `none`.
- `images/nano_043.jpg` expected `ALERT_OPERATOR` / `base_region_defect`, predicted `PASS` / `none`.
