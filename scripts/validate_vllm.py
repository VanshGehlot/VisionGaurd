import base64
import io
import json
import sys
import time
from pathlib import Path

import requests
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import get_settings
from model.prompts import VISIONGUARD_RESPONSE_SCHEMA

# Use a public image host that vLLM can fetch server-side without Wikimedia 403s.
TEST_IMAGE_URL = "http://images.cocodataset.org/val2017/000000039769.jpg"
LOCAL_EXAMPLE = Path("examples/bottle_good_0.jpg")


def post(payload: dict) -> dict:
    start = time.time()
    response = requests.post(get_settings().vllm_url, json=payload, timeout=120)
    response.raise_for_status()
    return {
        "latency_ms": int((time.time() - start) * 1000),
        "data": response.json(),
    }


def print_pass(step: str, details: str, latency_ms: int | None = None) -> None:
    print(f"{step}: PASS")
    latency = f" | latency={latency_ms}ms" if latency_ms is not None else ""
    print(f"  {details}{latency}")


def encode_example() -> str:
    if not LOCAL_EXAMPLE.exists():
        raise FileNotFoundError(f"Local example image not found: {LOCAL_EXAMPLE}")
    image = Image.open(LOCAL_EXAMPLE).convert("RGB")
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=95)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def main() -> None:
    settings = get_settings()
    text_payload = {
        "model": settings.model_name,
        "messages": [
            {"role": "user", "content": "Reply with exactly: visionguard-ok"}
        ],
        "max_tokens": 32,
        "temperature": 0.0,
    }

    text_response = post(text_payload)
    print_pass(
        "[1/4] Text request",
        "endpoint accepted a text-only chat completion",
        text_response["latency_ms"],
    )

    remote_image_payload = {
        "model": settings.model_name,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": TEST_IMAGE_URL},
                    },
                    {
                        "type": "text",
                        "text": "Describe this image in one sentence.",
                    },
                ],
            }
        ],
        "max_tokens": 128,
        "temperature": 0.1,
    }

    remote_image_response = post(remote_image_payload)
    print_pass(
        "[2/4] Remote image request",
        "endpoint accepted a remote image URL",
        remote_image_response["latency_ms"],
    )

    local_image_b64 = encode_example()
    local_image_payload = {
        "model": settings.model_name,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{local_image_b64}"},
                    },
                    {
                        "type": "text",
                        "text": "Describe whether the bottle appears normal or defective.",
                    },
                ],
            }
        ],
        "max_tokens": 128,
        "temperature": 0.1,
    }
    local_image_response = post(local_image_payload)
    print_pass(
        "[3/4] Local image request",
        f"endpoint accepted base64 image input from {LOCAL_EXAMPLE}",
        local_image_response["latency_ms"],
    )

    defect_json_payload = {
        "model": settings.model_name,
        "messages": [
            {
                "role": "system",
                "content": "Return only valid JSON matching the provided schema.",
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{local_image_b64}"},
                    },
                    {
                        "type": "text",
                        "text": "Inspect this bottle image for manufacturing defects and return only JSON.",
                    },
                ],
            },
        ],
        "max_tokens": 300,
        "temperature": 0.1,
        "structured_outputs": {
            "json": VISIONGUARD_RESPONSE_SCHEMA,
        },
    }
    defect_json_response = post(defect_json_payload)
    structured_content = defect_json_response["data"]["choices"][0]["message"]["content"]
    structured_parsed = (
        json.loads(structured_content) if isinstance(structured_content, str) else structured_content
    )
    required_keys = set(VISIONGUARD_RESPONSE_SCHEMA["required"])
    missing = required_keys - set(structured_parsed.keys())
    if missing:
        raise RuntimeError(f"Structured response is missing required keys: {sorted(missing)}")
    print_pass(
        "[4/4] Defect JSON request",
        "endpoint returned a schema-constrained defect response",
        defect_json_response["latency_ms"],
    )

    latencies = [
        text_response["latency_ms"],
        remote_image_response["latency_ms"],
        local_image_response["latency_ms"],
        defect_json_response["latency_ms"],
    ]
    avg_latency = int(sum(latencies) / len(latencies))

    print("\nVLLM endpoint is ready.")
    print(f"Model: {settings.model_name}")
    print(f"Endpoint: {settings.vllm_url}")
    print(f"Average latency across validation requests: {avg_latency}ms")
    print("\nSample outputs:")
    print(json.dumps(
        {
            "text_request": text_response["data"]["choices"][0]["message"]["content"],
            "remote_image_request": remote_image_response["data"]["choices"][0]["message"]["content"],
            "local_image_request": local_image_response["data"]["choices"][0]["message"]["content"],
            "defect_json_request": structured_parsed,
        },
        indent=2,
    ))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"VLLM endpoint validation failed: {exc}")
        print("If this fails:")
        print("- confirm vLLM is running")
        print("- confirm port 8000 is open")
        print("- confirm VLLM_URL is correct")
        print("- confirm model name matches the served model")
        raise
