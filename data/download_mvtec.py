from pathlib import Path

import requests
from datasets import Dataset, Image

SAMPLES_URL = "https://huggingface.co/datasets/Voxel51/mvtec-ad/raw/main/samples.json"
FILE_URL_TEMPLATE = "https://huggingface.co/datasets/Voxel51/mvtec-ad/resolve/main/{filepath}"
OUTPUT_DIR = Path("./mvtec_bottle")
IMAGES_DIR = OUTPUT_DIR / "images"


def download_metadata() -> list[dict]:
    response = requests.get(SAMPLES_URL, timeout=120)
    response.raise_for_status()
    payload = response.json()
    return payload["samples"]


def download_file(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        return

    with requests.get(url, stream=True, timeout=120) as response:
        response.raise_for_status()
        with destination.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    handle.write(chunk)


def build_bottle_dataset() -> Dataset:
    print("[VisionGuard] Fetching MVTec metadata...")
    samples = download_metadata()

    bottle_samples = [
        sample
        for sample in samples
        if sample["category"]["label"] == "bottle"
    ]

    if not bottle_samples:
        raise RuntimeError("No bottle samples were found in the MVTec metadata.")

    print(f"[VisionGuard] Downloading {len(bottle_samples)} bottle images...")
    rows = []

    for index, sample in enumerate(bottle_samples, start=1):
        filepath = sample["filepath"]
        split = sample["split"]
        anomaly_class = sample["defect"]["label"]
        source_name = Path(filepath).name
        local_name = f"{split}_{anomaly_class}_{index:03d}_{source_name}"
        local_path = IMAGES_DIR / local_name

        download_file(FILE_URL_TEMPLATE.format(filepath=filepath), local_path)

        rows.append(
            {
                "image": str(local_path),
                "anomaly_class": anomaly_class,
                "split": split,
                "source_path": filepath,
            }
        )

    dataset = Dataset.from_list(rows)
    return dataset.cast_column("image", Image())


def main() -> None:
    dataset = build_bottle_dataset()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    dataset.save_to_disk(str(OUTPUT_DIR))
    print(f"[VisionGuard] Loaded {len(dataset)} bottle images")
    print("[VisionGuard] First sample anomaly class:", dataset[0]["anomaly_class"])


if __name__ == "__main__":
    main()
