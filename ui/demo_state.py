from __future__ import annotations

from datetime import datetime, timedelta, timezone

from ui.mock_data import mock_inference_for_label


DEMO_SEQUENCE = [
    ("broken_large", "bottle_demo_critical_01", 0),
    ("contamination", "bottle_demo_warning_02", 4),
    ("good", "bottle_demo_pass_03", 8),
    ("broken_small", "bottle_demo_warning_04", 12),
    ("good", "bottle_demo_pass_05", 16),
    ("broken_large", "bottle_demo_critical_06", 20),
]


def demo_events() -> list[dict]:
    now = datetime.now(timezone.utc)
    events = []
    for label, image_id, minutes_ago in DEMO_SEQUENCE:
        event = mock_inference_for_label(label)
        event.update(
            {
                "timestamp": (now - timedelta(minutes=minutes_ago)).isoformat(),
                "image_id": image_id,
                "product_type": "bottle",
                "line_id": "LINE-A1",
                "shift": "morning",
                "runtime": "AMD MI300X · ROCm · vLLM",
            }
        )
        events.append(event)
    return events


def demo_metrics() -> dict:
    events = demo_events()
    total = len(events)
    defects = [event for event in events if event["defect_detected"]]
    critical = [event for event in events if event["severity"] == "critical"]
    latencies = [int(event["processing_ms"]) for event in events]
    avg_latency = sum(latencies) / len(latencies)
    return {
        "total_inspected": total,
        "defects_found": len(defects),
        "critical_events": len(critical),
        "avg_latency_ms": avg_latency,
        "latest_latency_ms": int(events[0]["processing_ms"]),
        "defect_rate": len(defects) / total * 100,
        "estimated_images_per_min": int(60000 / avg_latency),
        "model_name": "Qwen/Qwen2.5-VL-7B-Instruct",
        "runtime": "AMD MI300X · ROCm · vLLM",
        "endpoint_status": "demo_mode",
        "demo_mode": True,
    }
