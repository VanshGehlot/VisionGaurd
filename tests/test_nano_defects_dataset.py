import json
from pathlib import Path


DATASET_DIR = Path("data/nano_defects")


def test_nano_defects_dataset_files_exist():
    assert DATASET_DIR.joinpath("labels.json").exists()
    assert DATASET_DIR.joinpath("annotated_reference_labels.json").exists()
    assert DATASET_DIR.joinpath("README.md").exists()
    assert DATASET_DIR.joinpath("splits/train.json").exists()
    assert DATASET_DIR.joinpath("splits/val.json").exists()
    assert DATASET_DIR.joinpath("splits/test.json").exists()
    assert DATASET_DIR.joinpath("label_review.csv").exists()
    assert DATASET_DIR.joinpath("label_review.md").exists()


def test_nano_defects_labels_cover_all_images():
    labels = json.loads(DATASET_DIR.joinpath("labels.json").read_text())
    annotated_refs = json.loads(DATASET_DIR.joinpath("annotated_reference_labels.json").read_text())
    image_paths = [item["image"] for item in labels]

    assert len(labels) > 0
    assert len(labels) + len(annotated_refs) == 50
    assert len(set(image_paths)) == len(labels)
    assert all(item["image"].startswith("raw_unannotated/") for item in labels)
    assert all(item["label_source"] == "manual_review" for item in labels)
    assert all(item["image"].startswith("annotated_reference_only/") for item in annotated_refs)
    assert all(item["excluded_from_evaluation"] is True for item in annotated_refs)
    assert all(DATASET_DIR.joinpath(image).exists() for image in image_paths)
    assert any(item["is_clean"] and item["action"] == "PASS" for item in labels)
    assert any(item["action"] in {"ALERT_OPERATOR", "REJECT", "STOP_LINE"} for item in labels)
    assert all(item["label_confidence"] in {"high", "medium", "low"} for item in labels)
    assert all(item["release_confidence"] in {"high", "medium", "low"} for item in labels)
    assert all(isinstance(item["needs_human_review"], bool) for item in labels)


def test_nano_defects_splits_are_disjoint_and_complete():
    labels = json.loads(DATASET_DIR.joinpath("labels.json").read_text())
    all_labeled = {item["image"] for item in labels}
    split_sets = []
    for split_name in ["train", "val", "test"]:
        split = json.loads(DATASET_DIR.joinpath(f"splits/{split_name}.json").read_text())
        split_sets.append({item["image"] for item in split})

    assert set.union(*split_sets) == all_labeled
    assert split_sets[0].isdisjoint(split_sets[1])
    assert split_sets[0].isdisjoint(split_sets[2])
    assert split_sets[1].isdisjoint(split_sets[2])


def test_nano_defects_label_review_has_all_rows():
    labels = json.loads(DATASET_DIR.joinpath("labels.json").read_text())
    csv_lines = DATASET_DIR.joinpath("label_review.csv").read_text().strip().splitlines()
    markdown = DATASET_DIR.joinpath("label_review.md").read_text()

    assert len(csv_lines) == len(labels) + 1
    assert "needs_human_review" in csv_lines[0]
    assert "release_confidence" in csv_lines[0]
    assert "raw/unannotated NanoDefects evaluation images only" in markdown
    assert "| raw_unannotated/" in markdown
