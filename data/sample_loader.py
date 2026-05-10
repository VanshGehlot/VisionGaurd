from pathlib import Path

from datasets import load_from_disk


def export_examples(
    dataset_path: str = "./mvtec_bottle",
    output_dir: str = "./examples",
    limit_per_class: int = 2,
) -> None:
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    dataset = load_from_disk(dataset_path)
    counts: dict[str, int] = {}

    for sample in dataset:
        label = str(sample["anomaly_class"])
        counts.setdefault(label, 0)

        if counts[label] >= limit_per_class:
            continue

        image = sample["image"]
        safe_label = label.replace("/", "_").replace(" ", "_")
        path = Path(output_dir) / f"bottle_{safe_label}_{counts[label]}.jpg"
        image.save(path)
        counts[label] += 1

    print("[VisionGuard] Exported examples:", counts)


if __name__ == "__main__":
    export_examples()
