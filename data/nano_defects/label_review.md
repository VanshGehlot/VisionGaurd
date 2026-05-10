# NanoDefects Label Review

Conservative human-review label table for raw/unannotated NanoDefects evaluation images only.

Clean/PASS labels with `release_confidence=high` are the only current candidates for balanced-mode auto-release. The dataset still needs more clean/PASS examples before reliable production auto-release or LoRA training.

Annotated/circled images are excluded from this table and stored in `annotated_reference_only/` because they are label references, not model evidence.

| image_id | source_filename | label_source | expected_action | defect_type | severity | region_hint | label_confidence | needs_human_review | release_confidence | notes |
|---|---|---|---|---|---|---|---|---|---|---|
| raw_unannotated/nano_001.jpg | WhatsApp Image 2026-05-09 at 15.21.16.jpeg | ALERT_OPERATOR | unknown_defect | moderate | body / cap | low | true | low | Uncircled handheld image; possible finish or shape issue is not confidently clean. |
| raw_unannotated/nano_002.jpg | WhatsApp Image 2026-05-09 at 15.21.17 (1).jpeg | ALERT_OPERATOR | unknown_defect | moderate | body | low | true | low | Uncircled steel bottle image with possible subtle reflection deformation. |
| raw_unannotated/nano_003.jpg | WhatsApp Image 2026-05-09 at 15.21.17 (2).jpeg | ALERT_OPERATOR | base_region_defect | moderate | lower body / base | medium | true | low | Possible base-region deformation or finish issue; needs operator review. |
| raw_unannotated/nano_004.jpg | WhatsApp Image 2026-05-09 at 15.21.17.jpeg | PASS | clean | minor | none | medium | false | high | No clear visible bottle defect in this pilot image. |
| raw_unannotated/nano_005.jpg | WhatsApp Image 2026-05-09 at 15.21.18 (1).jpeg | PASS | clean | minor | none | medium | false | high | No clear visible jar defect in this pilot image. |
| raw_unannotated/nano_006.jpg | WhatsApp Image 2026-05-09 at 15.21.18.jpeg | REJECT | broad_shallow_dent | major | body | high | false | low | Large reflection distortion suggests broad body deformation. |
| raw_unannotated/nano_007.jpg | WhatsApp Image 2026-05-09 at 15.21.19 (1).jpeg | ALERT_OPERATOR | base_region_defect | moderate | lower body | medium | true | low | Lower body/base defect visible near seam. |
| raw_unannotated/nano_008.jpg | WhatsApp Image 2026-05-09 at 15.21.19 (2).jpeg | ALERT_OPERATOR | scratch_scuff | moderate | body | high | false | low | Visible scratch/scuff on dark coated bottle surface. |
| raw_unannotated/nano_009.jpg | WhatsApp Image 2026-05-09 at 15.21.19.jpeg | ALERT_OPERATOR | unknown_defect | moderate | body | low | true | low | Uncircled thermos image with possible subtle reflection deformation; not confidently clean. |
| raw_unannotated/nano_010.jpg | WhatsApp Image 2026-05-09 at 15.21.20 (1).jpeg | ALERT_OPERATOR | reflection_deformation | moderate | body | medium | true | low | Reflection distortion suggests shallow dent or deformation. |
| raw_unannotated/nano_011.jpg | WhatsApp Image 2026-05-09 at 15.21.20.jpeg | ALERT_OPERATOR | broad_shallow_dent | moderate | body | medium | true | low | Visible reflection distortion on brushed steel body. |
| raw_unannotated/nano_012.jpg | WhatsApp Image 2026-05-09 at 15.21.21 (1).jpeg | ALERT_OPERATOR | unknown_defect | moderate | lower jar / base | low | true | low | Uncircled jar image; possible base or finish issue is not confidently clean. |
| raw_unannotated/nano_013.jpg | WhatsApp Image 2026-05-09 at 15.21.21 (2).jpeg | ALERT_OPERATOR | unknown_defect | moderate | body | low | true | low | Side-by-side QA image with uncertain visible issue; route to review. |
| raw_unannotated/nano_014.jpg | WhatsApp Image 2026-05-09 at 15.21.21.jpeg | ALERT_OPERATOR | internal_dent | moderate | base interior | medium | true | low | Possible internal/base dent visible from bottom view. |
| raw_unannotated/nano_015.jpg | WhatsApp Image 2026-05-09 at 15.21.22 (1).jpeg | ALERT_OPERATOR | internal_dent | moderate | base interior | medium | true | low | Possible internal/base dent visible from bottom view. |
| raw_unannotated/nano_016.jpg | WhatsApp Image 2026-05-09 at 15.21.22 (2).jpeg | ALERT_OPERATOR | unknown_defect | moderate | coating / body | low | true | low | Uncircled coated bottle image; not enough evidence to mark clean. |
| raw_unannotated/nano_017.jpg | WhatsApp Image 2026-05-09 at 15.21.22.jpeg | ALERT_OPERATOR | reflection_deformation | moderate | body | medium | true | low | Reflection distortion suggests shallow dent or deformation. |
| raw_unannotated/nano_018.jpg | WhatsApp Image 2026-05-09 at 15.21.23 (1).jpeg | REJECT | coating_damage | major | lower body | high | false | low | Coating/finish damage visible on dark bottle surface. |
| raw_unannotated/nano_019.jpg | WhatsApp Image 2026-05-09 at 15.21.23.jpeg | PASS | clean | minor | none | medium | false | high | No clear visible thermos defect in this pilot image. |
| raw_unannotated/nano_020.jpg | WhatsApp Image 2026-05-09 at 15.21.24 (1).jpeg | PASS | clean | minor | none | medium | false | high | No clear visible defect in this pilot image. |
| raw_unannotated/nano_021.jpg | WhatsApp Image 2026-05-09 at 15.21.24 (2).jpeg | ALERT_OPERATOR | reflection_deformation | moderate | body | medium | true | low | Reflection distortion suggests shallow dent or deformation. |
| raw_unannotated/nano_022.jpg | WhatsApp Image 2026-05-09 at 15.21.24.jpeg | PASS | clean | minor | none | medium | false | high | No clear visible defect in this pilot image. |
| raw_unannotated/nano_023.jpg | WhatsApp Image 2026-05-09 at 15.21.25 (1).jpeg | REJECT | scratch_scuff | major | body | high | false | low | Long visible scratch/scuff on dark coating. |
| raw_unannotated/nano_024.jpg | WhatsApp Image 2026-05-09 at 15.21.25.jpeg | PASS | clean | minor | none | medium | false | high | No clear visible defect in this pilot image. |
| raw_unannotated/nano_027.jpg | WhatsApp Image 2026-05-09 at 15.21.26.jpeg | ALERT_OPERATOR | unknown_defect | moderate | body / base | low | true | low | Uncircled steel bottle image; subtle lower-body issue cannot be ruled out. |
| raw_unannotated/nano_031.jpg | WhatsApp Image 2026-05-09 at 15.21.28 (1).jpeg | REJECT | creased_dent | major | body | high | false | low | Large creased deformation visible on bottle body. |
