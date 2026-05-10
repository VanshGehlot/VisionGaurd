from pathlib import Path

import cv2
from PIL import Image


def sample_video_frames(
    video_path: str,
    output_dir: str = "outputs/frames",
    every_n_seconds: float = 1,
    max_frames: int | None = None,
) -> list[dict]:
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    if not fps or fps <= 0:
        fps = 25

    frame_interval = max(1, int(fps * every_n_seconds))
    frames: list[dict] = []
    frame_count = 0
    saved_count = 0
    video_stem = Path(video_path).stem.replace(" ", "_")

    while True:
        success, frame = cap.read()
        if not success:
            break

        if frame_count % frame_interval == 0:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image = Image.fromarray(rgb)
            frame_path = f"{output_dir}/{video_stem}_frame_{saved_count:04d}.jpg"
            image.save(frame_path)

            frames.append(
                {
                    "frame_id": f"frame_{saved_count:04d}",
                    "path": frame_path,
                    "timestamp_seconds": frame_count / fps,
                }
            )
            saved_count += 1
            if max_frames is not None and saved_count >= max_frames:
                break

        frame_count += 1

    cap.release()
    return frames
