from __future__ import annotations

import csv
import json
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "NanoDefects"
DATASET_DIR = ROOT / "data" / "nano_defects"
RAW_IMAGE_DIR = DATASET_DIR / "raw_unannotated"
ANNOTATED_REFERENCE_DIR = DATASET_DIR / "annotated_reference_only"
SPLIT_DIR = DATASET_DIR / "splits"

TAXONOMY = [
    "small_dent",
    "impact_pit",
    "broad_shallow_dent",
    "reflection_deformation",
    "creased_dent",
    "scratch_scuff",
    "coating_damage",
    "internal_dent",
    "base_region_defect",
    "shoulder_deformation",
    "rim_thread_defect",
    "unknown_defect",
    "clean",
]


def label(
    defect_type: str,
    severity: str,
    action: str,
    region_hint: str,
    notes: str,
    label_confidence: str,
    needs_human_review: bool,
    release_confidence: str | None = None,
) -> dict:
    if release_confidence is None:
        release_confidence = "high" if defect_type == "clean" and not needs_human_review else "low"
    return {
        "product_family": "steel_bottle",
        "product_type": "nanobot_bottle",
        "defect_type": defect_type,
        "severity": severity,
        "action": action,
        "region_hint": region_hint,
        "is_clean": defect_type == "clean",
        "notes": notes,
        "label_confidence": label_confidence,
        "needs_human_review": needs_human_review,
        "release_confidence": release_confidence,
    }


LABELS_BY_INDEX = {
    1: label("unknown_defect", "moderate", "ALERT_OPERATOR", "body / cap", "Uncircled handheld image; possible finish or shape issue is not confidently clean.", "low", True),
    2: label("unknown_defect", "moderate", "ALERT_OPERATOR", "body", "Uncircled steel bottle image with possible subtle reflection deformation.", "low", True),
    3: label("base_region_defect", "moderate", "ALERT_OPERATOR", "lower body / base", "Possible base-region deformation or finish issue; needs operator review.", "medium", True),
    4: label("clean", "minor", "PASS", "none", "No clear visible bottle defect in this pilot image.", "medium", False),
    5: label("clean", "minor", "PASS", "none", "No clear visible jar defect in this pilot image.", "medium", False),
    6: label("broad_shallow_dent", "major", "REJECT", "body", "Large reflection distortion suggests broad body deformation.", "high", False),
    7: label("base_region_defect", "moderate", "ALERT_OPERATOR", "lower body", "Lower body/base defect visible near seam.", "medium", True),
    8: label("scratch_scuff", "moderate", "ALERT_OPERATOR", "body", "Visible scratch/scuff on dark coated bottle surface.", "high", False),
    9: label("unknown_defect", "moderate", "ALERT_OPERATOR", "body", "Uncircled thermos image with possible subtle reflection deformation; not confidently clean.", "low", True),
    10: label("reflection_deformation", "moderate", "ALERT_OPERATOR", "body", "Reflection distortion suggests shallow dent or deformation.", "medium", True),
    11: label("broad_shallow_dent", "moderate", "ALERT_OPERATOR", "body", "Visible reflection distortion on brushed steel body.", "medium", True),
    12: label("unknown_defect", "moderate", "ALERT_OPERATOR", "lower jar / base", "Uncircled jar image; possible base or finish issue is not confidently clean.", "low", True),
    13: label("unknown_defect", "moderate", "ALERT_OPERATOR", "body", "Side-by-side QA image with uncertain visible issue; route to review.", "low", True),
    14: label("internal_dent", "moderate", "ALERT_OPERATOR", "base interior", "Possible internal/base dent visible from bottom view.", "medium", True),
    15: label("internal_dent", "moderate", "ALERT_OPERATOR", "base interior", "Possible internal/base dent visible from bottom view.", "medium", True),
    16: label("unknown_defect", "moderate", "ALERT_OPERATOR", "coating / body", "Uncircled coated bottle image; not enough evidence to mark clean.", "low", True),
    17: label("reflection_deformation", "moderate", "ALERT_OPERATOR", "body", "Reflection distortion suggests shallow dent or deformation.", "medium", True),
    18: label("coating_damage", "major", "REJECT", "lower body", "Coating/finish damage visible on dark bottle surface.", "high", False),
    19: label("clean", "minor", "PASS", "none", "No clear visible thermos defect in this pilot image.", "medium", False),
    20: label("clean", "minor", "PASS", "none", "No clear visible defect in this pilot image.", "medium", False),
    21: label("reflection_deformation", "moderate", "ALERT_OPERATOR", "body", "Reflection distortion suggests shallow dent or deformation.", "medium", True),
    22: label("clean", "minor", "PASS", "none", "No clear visible defect in this pilot image.", "medium", False),
    23: label("scratch_scuff", "major", "REJECT", "body", "Long visible scratch/scuff on dark coating.", "high", False),
    24: label("clean", "minor", "PASS", "none", "No clear visible defect in this pilot image.", "medium", False),
    25: label("small_dent", "moderate", "ALERT_OPERATOR", "lower body", "Human QA mark indicates small dent / reflection break on lower body.", "medium", True),
    26: label("impact_pit", "moderate", "ALERT_OPERATOR", "lower body", "Human QA mark indicates impact pit or localized dent on body.", "medium", True),
    27: label("unknown_defect", "moderate", "ALERT_OPERATOR", "body / base", "Uncircled steel bottle image; subtle lower-body issue cannot be ruled out.", "low", True),
    28: label("broad_shallow_dent", "moderate", "ALERT_OPERATOR", "body", "Human QA mark indicates broad dent or reflection deformation on bottle body.", "medium", True),
    29: label("base_region_defect", "moderate", "ALERT_OPERATOR", "base / lower jar", "Human QA mark indicates base-region defect on jar.", "medium", True),
    30: label("base_region_defect", "moderate", "ALERT_OPERATOR", "lower body / base", "Human QA mark indicates base-region issue on bottle lower body.", "medium", True),
    31: label("creased_dent", "major", "REJECT", "body", "Large creased deformation visible on bottle body.", "high", False),
    32: label("shoulder_deformation", "moderate", "ALERT_OPERATOR", "shoulder", "Human QA mark indicates shoulder deformation or localized reflection break.", "medium", True),
    33: label("base_region_defect", "moderate", "ALERT_OPERATOR", "base / lower jar", "Human QA mark indicates base-region defect on jar.", "medium", True),
    34: label("rim_thread_defect", "moderate", "ALERT_OPERATOR", "upper body / thread region", "Human QA mark indicates upper body or thread-region QA issue.", "medium", True),
    35: label("small_dent", "moderate", "ALERT_OPERATOR", "body", "Human QA mark indicates small dent / reflection deformation.", "medium", True),
    36: label("broad_shallow_dent", "moderate", "ALERT_OPERATOR", "body", "Human QA mark indicates body dent / reflection deformation.", "medium", True),
    37: label("broad_shallow_dent", "moderate", "ALERT_OPERATOR", "body", "Human QA mark indicates broad shallow dent on thermos body.", "medium", True),
    38: label("rim_thread_defect", "moderate", "ALERT_OPERATOR", "rim / thread", "Human QA mark indicates rim/thread-area issue near bottle opening.", "medium", True),
    39: label("broad_shallow_dent", "moderate", "ALERT_OPERATOR", "body", "Human QA mark indicates broad reflection deformation on body.", "medium", True),
    40: label("internal_dent", "moderate", "ALERT_OPERATOR", "base interior", "Human QA mark indicates internal/base dent from bottom view.", "medium", True),
    41: label("creased_dent", "major", "REJECT", "body", "Human QA mark indicates creased dent / sharp reflection break.", "high", False),
    42: label("broad_shallow_dent", "moderate", "ALERT_OPERATOR", "body", "Human QA mark indicates broad shallow dent on bottle body.", "medium", True),
    43: label("base_region_defect", "moderate", "ALERT_OPERATOR", "base interior", "Human QA mark indicates base-region QA issue from bottom view.", "medium", True),
    44: label("coating_damage", "moderate", "ALERT_OPERATOR", "body", "Human QA mark indicates coating or surface damage on dark bottle.", "medium", True),
    45: label("base_region_defect", "moderate", "ALERT_OPERATOR", "lower body / base", "Human QA mark indicates base-region issue on bottle lower body.", "medium", True),
    46: label("base_region_defect", "moderate", "ALERT_OPERATOR", "base / lower jar", "Human QA mark indicates base-region defect on jar.", "medium", True),
    47: label("shoulder_deformation", "moderate", "ALERT_OPERATOR", "shoulder", "Human QA mark indicates shoulder deformation or reflection break.", "medium", True),
    48: label("coating_damage", "major", "REJECT", "lower body", "Human QA mark indicates coating damage on dark bottle lower body.", "high", False),
    49: label("coating_damage", "moderate", "ALERT_OPERATOR", "shoulder / upper body", "Human QA mark indicates coating or surface finish issue.", "medium", True),
    50: label("scratch_scuff", "major", "REJECT", "body", "Long human-marked scratch/scuff on dark coated bottle.", "high", False),
}


def source_images() -> list[Path]:
    try:
        return sorted(path for path in SOURCE_DIR.iterdir() if path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"})
    except OSError as exc:
        raise SystemExit(f"Could not read NanoDefects source folder: {SOURCE_DIR}. {exc}") from exc


def is_annotated_reference(base: dict) -> bool:
    note = base.get("notes", "").lower()
    return "human qa mark" in note or "human-marked" in note


def build_records() -> tuple[list[dict], list[dict]]:
    images = source_images()
    raw_labels = []
    annotated_references = []
    for index, source in enumerate(images, start=1):
        extension = ".jpg" if source.suffix.lower() in {".jpg", ".jpeg"} else source.suffix.lower()
        normalized_name = f"nano_{index:03d}{extension}"
        base = LABELS_BY_INDEX.get(
            index,
            label(
                "unknown_defect",
                "moderate",
                "ALERT_OPERATOR",
                "unknown",
                "Uncertain factory QA image; route to operator review rather than guessing PASS.",
                "low",
                True,
            ),
        )
        if is_annotated_reference(base):
            annotated_references.append(
                {
                    "image": f"annotated_reference_only/{normalized_name}",
                    "source_image": source.name,
                    "excluded_from_evaluation": True,
                    "label_source": "annotated_reference",
                    **base,
                }
            )
            continue
        raw_labels.append(
            {
                "image": f"raw_unannotated/{normalized_name}",
                "source_image": source.name,
                "label_source": "manual_review",
                **base,
            }
        )
    return raw_labels, annotated_references


def write_readme(labels: list[dict], annotated_references: list[dict]) -> None:
    clean_count = sum(1 for item in labels if item["is_clean"])
    defect_count = len(labels) - clean_count
    readme = f"""# NanoDefects Steel Bottle QA Dataset

NanoDefects contains real factory QA images from a steel bottle / thermos / food jar manufacturing line.

## Source

- Origin: real NanoDefects bottle factory QA images
- Product family: steel bottles, thermos bottles, food jars, coated bottles
- Raw evaluation images: {len(labels)}
- Annotated reference-only images: {len(annotated_references)}
- Clean/PASS raw examples: {clean_count}
- Defect/review raw examples: {defect_count}

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

{chr(10).join(f"- {item}" for item in TAXONOMY)}

## Intended Use

This dataset is intended for raw-image VisionGuard baseline evaluation, prompt/safety tuning, adapter readiness analysis, and a future factory-specific LoRA/adapter experiment.

## Limitations

This is a small pilot dataset. The raw-image subset is enough for serious baseline measurement and QA workflow design, but not enough for a reliable conveyor-belt production model. The first target is PASS vs DEFECT/REVIEW with a conservative false-PASS policy, not perfect fine-grained classification.

NanoDefects currently has only {clean_count} raw clean/PASS examples. More raw clean examples are required before reliable auto-release or LoRA training.

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
"""
    DATASET_DIR.joinpath("README.md").write_text(readme, encoding="utf-8")


def write_splits(labels: list[dict]) -> None:
    # The source images are timestamp ordered. Contiguous splits reduce leakage
    # risk for near-duplicate views from the same bottle/defect sequence.
    total = len(labels)
    train_end = max(1, round(total * 0.70))
    val_end = max(train_end + 1, round(total * 0.85)) if total > 2 else train_end
    val_end = min(val_end, total)
    split_map = {
        "train": labels[:train_end],
        "val": labels[train_end:val_end],
        "test": labels[val_end:],
    }
    for split_name, items in split_map.items():
        SPLIT_DIR.joinpath(f"{split_name}.json").write_text(json.dumps(items, indent=2), encoding="utf-8")


def write_label_review(labels: list[dict]) -> None:
    fields = [
        "image_id",
        "source_filename",
        "label_source",
        "expected_action",
        "defect_type",
        "severity",
        "region_hint",
        "notes",
        "label_confidence",
        "needs_human_review",
        "release_confidence",
    ]
    rows = [
        {
            "image_id": item["image"],
            "source_filename": item["source_image"],
            "label_source": item["label_source"],
            "expected_action": item["action"],
            "defect_type": item["defect_type"],
            "severity": item["severity"],
            "region_hint": item["region_hint"],
            "notes": item["notes"],
            "label_confidence": item["label_confidence"],
            "needs_human_review": str(item["needs_human_review"]).lower(),
            "release_confidence": item["release_confidence"],
        }
        for item in labels
    ]
    csv_path = DATASET_DIR / "label_review.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    markdown = [
        "# NanoDefects Label Review",
        "",
        "Conservative human-review label table for raw/unannotated NanoDefects evaluation images only.",
        "",
        "Clean/PASS labels with `release_confidence=high` are the only current candidates for balanced-mode auto-release. The dataset still needs more clean/PASS examples before reliable production auto-release or LoRA training.",
        "",
        "Annotated/circled images are excluded from this table and stored in `annotated_reference_only/` because they are label references, not model evidence.",
        "",
        "| image_id | source_filename | label_source | expected_action | defect_type | severity | region_hint | label_confidence | needs_human_review | release_confidence | notes |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        markdown.append(
            "| {image_id} | {source_filename} | {expected_action} | {defect_type} | {severity} | {region_hint} | {label_confidence} | {needs_human_review} | {release_confidence} | {notes} |".format(
                **{key: str(value).replace("|", "/") for key, value in row.items()}
            )
        )
    (DATASET_DIR / "label_review.md").write_text("\n".join(markdown) + "\n", encoding="utf-8")


def main() -> None:
    if not SOURCE_DIR.exists():
        raise SystemExit(f"NanoDefects source folder not found: {SOURCE_DIR}")

    RAW_IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    ANNOTATED_REFERENCE_DIR.mkdir(parents=True, exist_ok=True)
    SPLIT_DIR.mkdir(parents=True, exist_ok=True)

    labels, annotated_references = build_records()
    copy_warnings = []
    for item in [*labels, *annotated_references]:
        source = SOURCE_DIR / item["source_image"]
        target = DATASET_DIR / item["image"]
        try:
            shutil.copy2(source, target)
        except OSError as exc:
            if target.exists():
                copy_warnings.append(
                    f"Warning: could not refresh `{target}` from `{source}` ({exc}); kept existing normalized image."
                )
                continue
            copy_warnings.append(
                f"Warning: could not copy `{source}` to `{target}` ({exc}); normalized image is missing."
            )

    DATASET_DIR.joinpath("labels.json").write_text(json.dumps(labels, indent=2), encoding="utf-8")
    DATASET_DIR.joinpath("annotated_reference_labels.json").write_text(
        json.dumps(annotated_references, indent=2), encoding="utf-8"
    )
    write_splits(labels)
    write_label_review(labels)
    write_readme(labels, annotated_references)
    for warning in copy_warnings:
        print(warning, file=sys.stderr)
    print(
        f"Prepared {len(labels)} raw NanoDefects images and "
        f"{len(annotated_references)} annotated references at {DATASET_DIR}"
    )


if __name__ == "__main__":
    main()
