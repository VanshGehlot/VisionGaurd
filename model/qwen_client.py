import base64
import io
import time
import json

import requests
from PIL import Image

from config import get_settings
from model.json_parser import parse_model_json
from model.prompts import (
    NANO_DEFECTS_SECOND_PASS_USER_PROMPT,
    NANO_DEFECTS_SYSTEM_PROMPT,
    NANO_DEFECTS_USER_PROMPT,
    SECOND_PASS_USER_PROMPT,
    SYSTEM_PROMPT,
    USER_PROMPT,
    VISIONGUARD_RESPONSE_SCHEMA,
)

MAX_IMAGE_SIDE = 896
JPEG_QUALITY = 90
FIRST_PASS_TIMEOUT_SECONDS = 30
SECOND_PASS_TIMEOUT_SECONDS = 10


def pil_to_base64(image: Image.Image) -> str:
    buffer = io.BytesIO()
    _prepare_image_for_vllm(image).save(buffer, format="JPEG", quality=JPEG_QUALITY)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def _prepare_image_for_vllm(image: Image.Image) -> Image.Image:
    prepared = image.convert("RGB")
    if max(prepared.size) <= MAX_IMAGE_SIDE:
        return prepared

    prepared = prepared.copy()
    prepared.thumbnail((MAX_IMAGE_SIDE, MAX_IMAGE_SIDE), Image.Resampling.LANCZOS)
    return prepared


def inspect_pil_image(image: Image.Image, inspection_profile: str | None = None) -> dict:
    system_prompt, user_prompt = _prompts_for_profile(inspection_profile, second_pass=False)
    result = _inspect_pil_image_with_prompt(
        image,
        system_prompt,
        user_prompt,
        request_timeout=FIRST_PASS_TIMEOUT_SECONDS,
        max_tokens=300,
        temperature=0.1,
    )
    result["primary_model_called"] = True
    result["primary_action"] = result.get("action")
    result["inspection_profile"] = inspection_profile or "generic"
    return result


def inspect_pil_image_second_pass(image: Image.Image, inspection_profile: str | None = None) -> dict:
    system_prompt, user_prompt = _prompts_for_profile(inspection_profile, second_pass=True)
    result = _inspect_pil_image_with_prompt(
        image,
        system_prompt,
        user_prompt,
        request_timeout=SECOND_PASS_TIMEOUT_SECONDS,
        max_tokens=220,
        temperature=0.0,
    )
    result["second_pass_called"] = True
    result["inspection_profile"] = inspection_profile or "generic"
    return result


def _prompts_for_profile(inspection_profile: str | None, second_pass: bool) -> tuple[str, str]:
    if inspection_profile == "nano_defects":
        return (
            NANO_DEFECTS_SYSTEM_PROMPT,
            NANO_DEFECTS_SECOND_PASS_USER_PROMPT if second_pass else NANO_DEFECTS_USER_PROMPT,
        )
    return SYSTEM_PROMPT, SECOND_PASS_USER_PROMPT if second_pass else USER_PROMPT


def _inspect_pil_image_with_prompt(
    image: Image.Image,
    system_prompt: str,
    user_prompt: str,
    request_timeout: int,
    max_tokens: int,
    temperature: float,
) -> dict:
    settings = get_settings()
    image_b64 = pil_to_base64(image)
    start = time.time()

    payload = {
        "model": settings.model_name,
        "messages": [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_b64}",
                        },
                    },
                    {
                        "type": "text",
                        "text": user_prompt,
                    },
                ],
            },
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
        "structured_outputs": {
            "json": VISIONGUARD_RESPONSE_SCHEMA,
        },
    }

    data, structured_output_enforced = _post_vllm_payload(
        settings.vllm_url,
        payload,
        timeout_seconds=request_timeout,
    )
    latency_ms = int((time.time() - start) * 1000)

    raw = _extract_message_content(data)
    result = parse_model_json(raw)
    result["processing_ms"] = latency_ms
    result["model_name"] = settings.model_name
    result["raw_output"] = raw
    result["structured_output_enforced"] = structured_output_enforced
    return result


def _post_vllm_payload(url: str, payload: dict, timeout_seconds: int) -> tuple[dict, bool]:
    response = requests.post(url, json=payload, timeout=timeout_seconds)
    if response.ok:
        return response.json(), True

    error_text = _response_error_text(response)
    if response.status_code == 400 and "structured_outputs" in payload:
        fallback_payload = dict(payload)
        fallback_payload.pop("structured_outputs", None)
        fallback_response = requests.post(url, json=fallback_payload, timeout=timeout_seconds)
        if fallback_response.ok:
            return fallback_response.json(), False
        error_text = f"{error_text}; fallback without structured_outputs also failed: {_response_error_text(fallback_response)}"

    raise RuntimeError(error_text)


def _response_error_text(response: requests.Response) -> str:
    body = response.text.strip()
    if len(body) > 700:
        body = f"{body[:700]}..."
    return f"{response.status_code} {response.reason}: {body}"


def _extract_message_content(data: dict) -> str:
    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(f"Unexpected vLLM response payload: {data}") from exc

    if isinstance(content, str):
        return content

    if isinstance(content, dict):
        return json.dumps(content)

    if isinstance(content, list):
        text_parts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                text_parts.append(str(item.get("text", "")))
        return "\n".join(part for part in text_parts if part).strip()

    return str(content)
