from pathlib import Path

from datasets import load_from_disk

from agents.logger import logger_agent
from agents.reporter import reporter_agent, summarize_events
from agents.scanner import scanner_agent
from config import get_settings
from ui.mock_data import mock_inference_for_label
from utils.video_sampler import sample_video_frames

DEMO_VIDEO_LABELS = ["broken_large", "broken_small", "contamination", "good"]


def _select_diverse_samples(dataset, limit: int):
    if "anomaly_class" not in dataset.column_names:
        return dataset.select(range(min(limit, len(dataset))))

    grouped_indices: dict[str, list[int]] = {}
    for index, label in enumerate(dataset["anomaly_class"]):
        grouped_indices.setdefault(str(label), []).append(index)

    ordered_labels = sorted(grouped_indices.keys(), key=lambda label: (label == "good", label))
    selected_indices: list[int] = []
    position = 0

    while len(selected_indices) < min(limit, len(dataset)):
        progressed = False
        for label in ordered_labels:
            indices = grouped_indices[label]
            if position < len(indices):
                selected_indices.append(indices[position])
                progressed = True
                if len(selected_indices) >= limit:
                    break
        if not progressed:
            break
        position += 1

    return dataset.select(selected_indices[:limit])


def run_dataset_inspection(dataset_path: str = "./mvtec_bottle", limit: int = 20) -> None:
    settings = get_settings()
    dataset_dir = Path(dataset_path)
    if not dataset_dir.exists():
        raise FileNotFoundError(
            f"Dataset path '{dataset_path}' was not found. Run data/download_mvtec.py first."
        )

    dataset = load_from_disk(dataset_path)
    total = min(limit, len(dataset))
    selected_dataset = _select_diverse_samples(dataset, total)
    mode = "DEMO_MODE" if settings.demo_mode else "LIVE_MODE"
    print(f"[VisionGuard] Starting inspection on {total} images ({mode})")

    for index, sample in enumerate(selected_dataset):
        image = sample["image"]
        true_label = sample.get("anomaly_class", "unknown")

        if settings.demo_mode:
            scan = {**mock_inference_for_label(str(true_label)), "demo_mode": True}
        else:
            scan = scanner_agent(image)
        event = logger_agent(scan, product_type="bottle")
        status = "DEFECT" if event["defect_detected"] else "OK"

        print(
            f"[{index + 1:03d}] true={true_label} | "
            f"status={status} | "
            f"type={event['defect_type']} | "
            f"severity={event['severity']} | "
            f"action={event['action']} | "
            f"latency={event['processing_ms']}ms"
        )

    print("\n[VisionGuard] Shift Report")
    print(reporter_agent())


def run_video_inspection(video_path: str, sampling_interval: float = 1.0, max_frames: int = 8) -> None:
    settings = get_settings()
    if not Path(video_path).exists():
        raise FileNotFoundError(f"Video path '{video_path}' was not found.")

    frames = sample_video_frames(video_path, every_n_seconds=sampling_interval, max_frames=max_frames)
    if not frames:
        raise RuntimeError("No frames could be extracted from the video.")

    events: list[dict] = []
    print(f"[VisionGuard] Starting video inspection on {len(frames)} sampled frames")

    for index, frame in enumerate(frames, start=1):
        image = Path(frame["path"])
        if settings.demo_mode:
            demo_label = DEMO_VIDEO_LABELS[(index - 1) % len(DEMO_VIDEO_LABELS)]
            scan = {**mock_inference_for_label(demo_label), "demo_mode": True}
        else:
            from PIL import Image

            scan = scanner_agent(Image.open(image).convert("RGB"))
        event = logger_agent(scan, product_type="video_frame")
        events.append(event)
        print(
            f"[{index:03d}] frame={frame['frame_id']} | ts={frame['timestamp_seconds']:.2f}s | "
            f"type={event['defect_type']} | severity={event['severity']} | action={event['action']}"
        )

    print("\n[VisionGuard] Batch Report")
    print(summarize_events(events))


if __name__ == "__main__":
    run_dataset_inspection()
