import base64
import io
import json
import tempfile
from pathlib import Path

import requests
from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from PIL import Image, UnidentifiedImageError

try:
    import pillow_heif

    pillow_heif.register_heif_opener()
    HEIF_SUPPORT_ENABLED = True
except Exception:
    HEIF_SUPPORT_ENABLED = False

from agents.logger import logger_agent
from agents.reporter import (
    build_operations_alert,
    operations_alert_agent,
    reporter_agent,
    summarize_events,
)
from agents.scanner import scanner_agent
from agents.adaptation import (
    add_operator_feedback,
    analyze_dataset,
    create_training_job,
    deploy_model,
    get_adaptation_overview,
    get_baseline_evaluation,
    get_datasets,
    get_feedback_summary,
    get_factory_profile,
    get_inference_routing,
    get_model_options,
    get_model_registry,
    get_training_jobs,
    resolve_model_route,
)
from config import get_settings
from db.sqlite_client import get_analytics_summary, get_logs
from ui.demo_state import demo_events, demo_metrics
from ui.mock_data import mock_inference_for_path
from utils.annotation import annotate_image_with_metadata
from utils.safety_net import apply_safety_net
from utils.video_sampler import sample_video_frames

APP_ROOT = Path(__file__).resolve().parent
FRONTEND_DIST = APP_ROOT / "frontend" / "dist"
FRONTEND_ASSETS = FRONTEND_DIST / "assets"
RUNTIME_STRING = "AMD MI300X · ROCm · vLLM"
DEMO_VIDEO_LABELS = ["broken_large", "broken_small", "contamination", "good"]

runtime_state = {
    "endpoint_status": "pending",
    "last_error": None,
    "last_mode": "live",
}


def _looks_like_heif_upload(upload: UploadFile) -> bool:
    content_type = (upload.content_type or "").lower()
    filename = (upload.filename or "").lower()
    return content_type in {"image/heic", "image/heif", "image/heic-sequence", "image/heif-sequence"} or filename.endswith(
        (".heic", ".heif")
    )

app = FastAPI(title="VisionGuard API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/examples", StaticFiles(directory=str(APP_ROOT / "examples")), name="examples")
if FRONTEND_ASSETS.exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_ASSETS)), name="frontend-assets")

def _frontend_index_response() -> Response:
    if FRONTEND_DIST.joinpath("index.html").exists():
        return FileResponse(FRONTEND_DIST / "index.html")
    return Response(
        content=(
            "<!doctype html><html><head><title>VisionGuard frontend build missing</title>"
            "<meta name='viewport' content='width=device-width, initial-scale=1' />"
            "<style>body{font-family:Inter,system-ui,sans-serif;background:#f7f8fa;color:#0b0d10;padding:40px;}"
            "main{max-width:780px;margin:0 auto;background:#fff;border:1px solid #e5e7eb;border-radius:24px;padding:32px;"
            "box-shadow:0 18px 50px rgba(15,23,42,0.06)}code{background:#f3f4f6;padding:2px 6px;border-radius:8px}</style>"
            "</head><body><main><h1>VisionGuard frontend build is missing.</h1>"
            "<p>Build the React frontend before loading the premium product shell:</p>"
            "<p><code>cd frontend && npm install && npm run build</code></p>"
            "<p>The FastAPI backend and Gradio fallback remain available.</p></main></body></html>"
        ),
        media_type="text/html",
        status_code=503,
    )


@app.get("/favicon.ico")
def favicon():
    return Response(status_code=204)


@app.get("/health")
def health():
    settings = get_settings()
    reachable = _vllm_reachable(settings)
    return {
        "api": "online",
        "vllm_endpoint": _truthful_endpoint_status(settings, reachable),
        "vllm_reachable": reachable,
        "database": "connected",
        "mindsdb": "optional",
        "demo_mode": settings.demo_mode,
        "last_mode": runtime_state["last_mode"],
        "last_error": runtime_state["last_error"],
    }


@app.post("/inspect-image")
async def inspect_image(
    image: UploadFile = File(...),
    line_id: str | None = Form(None),
    shift: str | None = Form(None),
    model_route: str | None = Form(None),
    force_demo: bool = Query(False),
):
    try:
        contents = await image.read()
        if not contents:
            raise HTTPException(status_code=400, detail="Invalid image upload. The uploaded file is empty.")
        pil_image = Image.open(io.BytesIO(contents)).convert("RGB")
    except HTTPException:
        raise
    except UnidentifiedImageError as exc:
        if _looks_like_heif_upload(image) and not HEIF_SUPPORT_ENABLED:
            raise HTTPException(
                status_code=415,
                detail=(
                    "HEIC/HEIF image support is not installed in this environment. "
                    "Install pillow-heif and restart VisionGuard, or upload PNG/JPEG/WEBP."
                ),
            ) from exc
        raise HTTPException(
            status_code=400,
            detail="Invalid image upload. Please upload a valid PNG, JPEG, WEBP, HEIC, HEIF, TIFF, or BMP image file.",
        ) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Uploaded file could not be parsed as an image: {exc}") from exc

    try:
        event = _run_inspection(
            pil_image=pil_image,
            source_name=image.filename or "uploaded_image.jpg",
            product_type="bottle",
            line_id=line_id,
            shift=shift,
            model_route=model_route,
            force_demo=force_demo,
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Inference endpoint unavailable. Set VLLM_URL and validate the AMD vLLM server before live inspection. "
                f"Details: {exc}"
            ),
        ) from exc

    annotated, annotation_meta = annotate_image_with_metadata(pil_image, event)
    vllm_reachable = _vllm_reachable(get_settings()) or bool(event.get("primary_model_called"))
    metrics_payload = _metrics_payload()
    if event.get("primary_model_called"):
        metrics_payload["vllm_reachable"] = True
        metrics_payload["endpoint_status"] = "connected"
    return {
        **event,
        **annotation_meta,
        "demo_mode": get_settings().demo_mode,
        "vllm_reachable": vllm_reachable,
        "runtime": RUNTIME_STRING,
        "annotated_image": pil_to_data_url(annotated, image_format="PNG"),
        "report": reporter_agent(),
        "operations_alert": operations_alert_agent(),
        "metrics": metrics_payload,
    }


@app.post("/inspect-video")
async def inspect_video(
    video: UploadFile = File(...),
    line_id: str | None = Form(None),
    shift: str | None = Form(None),
    model_route: str | None = Form(None),
    sampling_interval: float = Form(1.0),
    max_frames: int = Form(8),
    force_demo: bool = Query(False),
):
    suffix = Path(video.filename or "upload.mp4").suffix or ".mp4"
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_video = Path(temp_dir) / f"upload{suffix}"
        temp_video.write_bytes(await video.read())
        frames = sample_video_frames(
            str(temp_video),
            output_dir=str(Path(temp_dir) / "frames"),
            every_n_seconds=sampling_interval,
            max_frames=max_frames,
        )

        if not frames:
            raise HTTPException(status_code=400, detail="No frames could be extracted from the uploaded video.")

        frame_results = []
        batch_events = []
        for index, frame in enumerate(frames):
            pil_image = Image.open(frame["path"]).convert("RGB")
            source_name = f"{DEMO_VIDEO_LABELS[index % len(DEMO_VIDEO_LABELS)]}.jpg" if force_demo or get_settings().demo_mode else frame["path"]
            try:
                event = _run_inspection(
                    pil_image=pil_image,
                    source_name=source_name,
                    product_type="video_frame",
                    line_id=line_id,
                    shift=shift,
                    model_route=model_route,
                    force_demo=force_demo,
                )
            except RuntimeError as exc:
                raise HTTPException(
                    status_code=503,
                    detail=(
                        "Inference endpoint unavailable. Set VLLM_URL and validate the AMD vLLM server before live inspection. "
                        f"Details: {exc}"
                    ),
                ) from exc

            batch_events.append(event)
            frame_results.append(
                {
                    "frame_id": frame["frame_id"],
                    "timestamp_seconds": round(frame["timestamp_seconds"], 2),
                    "defect_type": event["defect_type"],
                    "defect_category": event["defect_category"],
                    "severity": event["severity"],
                    "action": event["action"],
                    "confidence": event["confidence"],
                    "runtime": RUNTIME_STRING,
                }
            )

    return {
        "frames": frame_results,
        "batch_report": summarize_events(batch_events),
        "operations_alert": build_operations_alert(batch_events),
        "demo_mode": get_settings().demo_mode,
        "vllm_reachable": _vllm_reachable(get_settings()),
        "metrics": _metrics_payload(),
    }


@app.get("/events")
def events(limit: int = Query(50, ge=1, le=200)):
    columns, rows = get_logs(limit=limit)
    if get_settings().demo_mode:
        return {
            "events": demo_events()[:limit],
        }
    if not rows and _demo_surface_enabled():
        return {
            "events": demo_events()[:limit],
        }
    return {
        "events": [_serialize_log_row(columns, row) for row in rows],
    }


@app.get("/report")
def report():
    if get_settings().demo_mode:
        return {
            "report": summarize_events(demo_events()),
        }
    if _demo_surface_enabled() and not get_logs(limit=1)[1]:
        return {
            "report": summarize_events(demo_events()),
        }
    return {
        "report": reporter_agent(),
    }


@app.get("/metrics")
def metrics():
    return _metrics_payload()


@app.get("/operations-alert")
def operations_alert():
    if get_settings().demo_mode:
        return {
            "alert": build_operations_alert(demo_events()),
        }
    if _demo_surface_enabled() and not get_logs(limit=1)[1]:
        return {
            "alert": build_operations_alert(demo_events()),
        }
    return {
        "alert": operations_alert_agent(),
    }


@app.get("/adaptation/overview")
def adaptation_overview():
    return get_adaptation_overview()


@app.get("/adaptation/factory")
def adaptation_factory():
    return {"factory": get_factory_profile()}


@app.get("/adaptation/datasets")
def adaptation_datasets():
    return {"datasets": get_datasets()}


@app.get("/adaptation/baseline-evaluation")
def adaptation_baseline_evaluation():
    return {"evaluation": get_baseline_evaluation()}


@app.get("/adaptation/training-jobs")
def adaptation_training_jobs():
    return {"training_jobs": get_training_jobs()}


@app.get("/adaptation/model-registry")
def adaptation_model_registry():
    return {"models": get_model_registry()}


@app.get("/adaptation/model-options")
def adaptation_model_options():
    return {"model_options": get_model_options()}


@app.get("/adaptation/routing")
def adaptation_routing():
    return {"routing": get_inference_routing()}


@app.get("/adaptation/feedback")
def adaptation_feedback():
    return {"feedback": get_feedback_summary()}


@app.post("/adaptation/feedback")
def adaptation_submit_feedback(payload: dict):
    return add_operator_feedback(payload)


@app.post("/adaptation/analyze-dataset")
def adaptation_analyze_dataset(payload: dict):
    return analyze_dataset(payload)


@app.post("/adaptation/train")
def adaptation_train():
    return create_training_job()


@app.post("/adaptation/deploy")
def adaptation_deploy(payload: dict):
    model_id = payload.get("model_id")
    if not model_id:
        raise HTTPException(status_code=400, detail="model_id is required")
    try:
        return deploy_model(model_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/adaptation/deploy-model")
def adaptation_deploy_model(payload: dict):
    return adaptation_deploy(payload)


def _run_inspection(
    pil_image: Image.Image,
    source_name: str,
    product_type: str,
    line_id: str | None,
    shift: str | None,
    model_route: str | None,
    force_demo: bool,
) -> dict:
    settings = get_settings()
    effective_demo = force_demo or settings.demo_mode

    try:
        if effective_demo:
            scan = {
                **mock_inference_for_path(source_name),
                "demo_mode": True,
                "primary_model_called": False,
                "primary_action": "DEMO",
                "pass_verification_applied": False,
                "second_pass_called": False,
                "second_pass_verdict": "skipped",
                "speckle_review_flagged": False,
                "final_verdict": "DEMO",
            }
            runtime_state["endpoint_status"] = "demo_mode"
            runtime_state["last_mode"] = "demo"
            runtime_state["last_error"] = None
        else:
            inspection_profile = "nano_defects" if model_route == "nano_defects_eval" else None
            scan = scanner_agent(pil_image, inspection_profile=inspection_profile)
            scan = apply_safety_net(scan, source_name)
            runtime_state["endpoint_status"] = "connected"
            runtime_state["last_mode"] = "live"
            runtime_state["last_error"] = None
    except Exception as exc:
        runtime_state["endpoint_status"] = "unavailable"
        runtime_state["last_mode"] = "live"
        runtime_state["last_error"] = str(exc)
        raise RuntimeError(str(exc)) from exc

    event = logger_agent(
        scan_result=scan,
        product_type=product_type,
        line_id=line_id or None,
        shift=shift or None,
    )
    routing_metadata = resolve_model_route(model_route)
    event.update(
        {
            "selected_model_route": routing_metadata["selected_model_route"],
            "model_route_label": routing_metadata["model_route_label"],
            "routing_metadata": routing_metadata,
        }
    )
    event["runtime"] = RUNTIME_STRING
    return event


def _metrics_payload() -> dict:
    settings = get_settings()
    if settings.demo_mode:
        payload = demo_metrics()
        payload["endpoint_status"] = "demo_mode"
        payload["demo_mode"] = True
        payload["runtime"] = RUNTIME_STRING
        return payload
    if _demo_surface_enabled() and not get_logs(limit=1)[1]:
        payload = demo_metrics()
        payload["endpoint_status"] = "demo_mode"
        payload["demo_mode"] = True
        payload["runtime"] = RUNTIME_STRING
        return payload
    payload = get_analytics_summary()
    reachable = _vllm_reachable(settings)
    payload["endpoint_status"] = _truthful_endpoint_status(settings, reachable)
    payload["demo_mode"] = settings.demo_mode or runtime_state["last_mode"] == "demo"
    payload["runtime"] = RUNTIME_STRING
    payload["vllm_reachable"] = reachable
    return payload


def _demo_surface_enabled() -> bool:
    settings = get_settings()
    return settings.demo_mode or runtime_state["last_mode"] == "demo"


def _vllm_reachable(settings) -> bool:
    try:
        response = requests.get(_vllm_models_url(settings.vllm_url), timeout=1.5)
        return response.ok
    except Exception:
        return False


def _truthful_endpoint_status(settings, reachable: bool) -> str:
    if settings.demo_mode or runtime_state["last_mode"] == "demo":
        return "demo_mode"
    if reachable:
        return "connected"
    if runtime_state["endpoint_status"] == "pending":
        return "pending"
    return "unavailable"


def _vllm_models_url(vllm_url: str) -> str:
    if "/v1/chat/completions" in vllm_url:
        return vllm_url.replace("/v1/chat/completions", "/v1/models")
    return vllm_url.rstrip("/") + "/v1/models"


def _serialize_log_row(columns: list[str], row: tuple) -> dict:
    record = dict(zip(columns, row))
    for key in ("possible_causes", "recommended_fix", "prevention"):
        raw = record.get(key)
        if isinstance(raw, str):
            try:
                record[key] = json.loads(raw)
            except Exception:
                record[key] = []
    record["defect_detected"] = bool(record.get("defect_detected"))
    record["action"] = record.get("action_taken")
    return record


def pil_to_data_url(image: Image.Image, image_format: str = "JPEG") -> str:
    buffer = io.BytesIO()
    normalized_format = image_format.upper()
    if normalized_format == "PNG":
        image.save(buffer, format="PNG", optimize=True)
        mime_type = "image/png"
    else:
        image.convert("RGB").save(buffer, format="JPEG", quality=95)
        mime_type = "image/jpeg"
    encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}"


@app.get("/")
def frontend_root():
    return _frontend_index_response()


@app.get("/{full_path:path}")
def frontend_routes(full_path: str):
    api_exact_paths = {
        "health",
        "inspect-image",
        "inspect-video",
        "events",
        "report",
        "metrics",
        "operations-alert",
        "favicon.ico",
    }
    if full_path in api_exact_paths or full_path.startswith(("examples/", "assets/")):
        raise HTTPException(status_code=404, detail="Not found")
    return _frontend_index_response()
