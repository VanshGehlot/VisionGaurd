import base64
from pathlib import Path

import gradio as gr
import pandas as pd
from PIL import Image

from agents.logger import logger_agent
from agents.reporter import (
    build_operations_alert,
    operations_alert_agent,
    reporter_agent,
    summarize_events,
)
from agents.scanner import scanner_agent
from config import get_settings
from db.sqlite_client import get_analytics_summary, get_logs
from ui.components import (
    available_example_paths,
    render_architecture_footer,
    render_error_card,
    render_factory_intelligence_panel,
    render_mode_banner,
    render_operations_alert,
    render_performance_panel,
    render_result_card,
)
from ui.mock_data import mock_inference_for_path
from ui.styles import APP_CSS
from utils.annotation import annotate_image
from utils.video_sampler import sample_video_frames

DEMO_VIDEO_LABELS = [
    "broken_large",
    "broken_small",
    "contamination",
    "good",
]


def _brand_logo_data_url() -> str:
    logo_path = Path(__file__).resolve().parent / "assets" / "visionguard-logo.png"
    encoded = base64.b64encode(logo_path.read_bytes()).decode("utf-8")
    return f"data:image/png;base64,{encoded}"


def _hero_html() -> str:
    badges = [
        "AMD MI300X",
        "ROCm",
        "vLLM",
        "Qwen-VL",
        "MindsDB",
        "Hugging Face",
    ]
    badge_html = "".join([f'<span class="vg-badge">{badge}</span>' for badge in badges])
    logo_src = _brand_logo_data_url()
    return f"""
    <div class="vg-hero">
      <div class="vg-brand-lockup">
        <img class="vg-brand-mark" src="{logo_src}" alt="VisionGuard" />
        <div>
          <p class="vg-subtitle">
            Industrial Defect Detection Agent powered by Qwen-VL on AMD MI300X
          </p>
        </div>
      </div>
      <div class="vg-badge-row">{badge_html}</div>
    </div>
    """.strip()


LOG_COLUMNS = [
    "id",
    "timestamp",
    "image_id",
    "product_type",
    "defect_detected",
    "defect_type",
    "defect_category",
    "severity",
    "confidence",
    "location",
    "region_horizontal",
    "region_vertical",
    "action_taken",
    "line_id",
    "shift",
    "processing_ms",
    "model_name",
    "visual_explanation",
    "possible_causes",
    "recommended_fix",
    "prevention",
    "factory_owner_summary",
]


def inspect_image_ui(image_path, line_id, shift):
    settings = get_settings()
    if image_path is None:
        return _image_failure("Please upload an image before running inspection.")

    try:
        pil_image = Image.open(image_path).convert("RGB")
    except Exception as exc:
        return _image_failure(f"Uploaded file could not be read as an image. Details: {exc}")

    try:
        if settings.demo_mode:
            scan = {**mock_inference_for_path(image_path), "demo_mode": True}
            endpoint_status = "demo_mode"
        else:
            scan = scanner_agent(pil_image)
            endpoint_status = "connected"
        event = logger_agent(
            scan_result=scan,
            product_type="bottle",
            line_id=line_id or None,
            shift=shift or None,
        )
    except Exception as exc:
        return _image_failure(
            "AMD inference endpoint is not connected yet. "
            "Set `VLLM_URL` in `.env` and run `python scripts/validate_vllm.py`. "
            "Inference request failed. Confirm `VLLM_URL` points to a live AMD "
            "MI300X vLLM endpoint, then validate it with "
            "`python scripts/validate_vllm.py`. "
            f"Current VLLM_URL: {settings.vllm_url}. Details: {exc}"
        )

    annotated_image = annotate_image(pil_image, event)
    logs_df = load_logs_df()
    report = reporter_agent()
    performance_html = render_performance_panel(
        get_analytics_summary(),
        endpoint_status=endpoint_status,
        demo_mode=settings.demo_mode,
    )
    operations_html = render_operations_alert(operations_alert_agent())
    return (
        render_result_card(event),
        annotated_image,
        render_factory_intelligence_panel(event),
        performance_html,
        operations_html,
        event,
        logs_df,
        report,
    )


def inspect_video_ui(video_path, sampling_interval, max_frames, line_id, shift):
    settings = get_settings()
    if not video_path:
        yield _video_failure("Please upload a short product video before running batch inspection.")
        return

    try:
        frames = sample_video_frames(
            video_path,
            every_n_seconds=float(sampling_interval),
            max_frames=int(max_frames),
        )
    except Exception as exc:
        yield _video_failure(f"Video sampling failed. Details: {exc}")
        return

    if not frames:
        yield _video_failure("No frames could be extracted from the uploaded video.")
        return

    progress_rows: list[dict] = []
    batch_events: list[dict] = []
    status_html = (
        f"<div class='vg-banner vg-live-banner'>Processing {len(frames)} sampled frames sequentially.</div>"
    )
    empty_df = pd.DataFrame(columns=["frame_id", "timestamp_seconds", "defect_type", "severity", "action", "confidence"])
    yield status_html, empty_df, "No batch report yet.", render_performance_panel(
        get_analytics_summary(), endpoint_status="starting", demo_mode=settings.demo_mode
    ), render_operations_alert(operations_alert_agent())

    for index, frame in enumerate(frames, start=1):
        try:
            pil_image = Image.open(frame["path"]).convert("RGB")
            if settings.demo_mode:
                demo_label = DEMO_VIDEO_LABELS[(index - 1) % len(DEMO_VIDEO_LABELS)]
                scan = {**mock_inference_for_path(f"{demo_label}.jpg"), "demo_mode": True}
            else:
                scan = scanner_agent(pil_image)
            event = logger_agent(
                scan_result=scan,
                product_type="video_frame",
                line_id=line_id or None,
                shift=shift or None,
            )
        except Exception as exc:
            progress_rows.append(
                {
                    "frame_id": frame["frame_id"],
                    "timestamp_seconds": round(frame["timestamp_seconds"], 2),
                    "defect_type": "error",
                    "severity": "error",
                    "action": "inspection_failed",
                    "confidence": 0.0,
                }
            )
            yield (
                f"<div class='vg-banner vg-demo-banner'>Frame {index}/{len(frames)} failed: {exc}</div>",
                pd.DataFrame(progress_rows),
                "Batch inspection is partially complete. Resolve frame-level failures before using this output operationally.",
                render_performance_panel(
                    get_analytics_summary(),
                    endpoint_status="degraded",
                    demo_mode=settings.demo_mode,
                ),
                render_operations_alert(operations_alert_agent()),
            )
            continue

        batch_events.append(event)
        progress_rows.append(
            {
                "frame_id": frame["frame_id"],
                "timestamp_seconds": round(frame["timestamp_seconds"], 2),
                "defect_type": event.get("defect_type"),
                "severity": event.get("severity"),
                "action": event.get("action"),
                "confidence": round(float(event.get("confidence", 0.0)), 2),
            }
        )
        batch_report = summarize_events(batch_events)
        yield (
            f"<div class='vg-banner vg-live-banner'>Processed frame {index}/{len(frames)}.</div>",
            pd.DataFrame(progress_rows),
            batch_report,
            render_performance_panel(
                get_analytics_summary(),
                endpoint_status="connected" if not settings.demo_mode else "demo_mode",
                demo_mode=settings.demo_mode,
            ),
            render_operations_alert(build_operations_alert(batch_events)),
        )


def load_logs_df() -> pd.DataFrame:
    columns, rows = get_logs(limit=50)
    if not rows:
        return pd.DataFrame(columns=LOG_COLUMNS)
    return pd.DataFrame(rows, columns=columns)


def refresh_report():
    settings = get_settings()
    return (
        load_logs_df(),
        reporter_agent(),
        render_performance_panel(
            get_analytics_summary(),
            endpoint_status="idle" if not settings.demo_mode else "demo_mode",
            demo_mode=settings.demo_mode,
        ),
        render_operations_alert(operations_alert_agent()),
    )


def _image_failure(message: str):
    settings = get_settings()
    logs_df = load_logs_df()
    return (
        render_error_card(message),
        None,
        render_error_card("Factory intelligence is unavailable until a valid inspection is completed."),
        render_performance_panel(
            get_analytics_summary(),
            endpoint_status="unavailable",
            demo_mode=settings.demo_mode,
        ),
        render_operations_alert(operations_alert_agent()),
        {},
        logs_df,
        reporter_agent(),
    )


def _video_failure(message: str):
    settings = get_settings()
    return (
        render_error_card(message),
        pd.DataFrame(columns=["frame_id", "timestamp_seconds", "defect_type", "severity", "action", "confidence"]),
        "No batch report available.",
        render_performance_panel(
            get_analytics_summary(),
            endpoint_status="unavailable",
            demo_mode=settings.demo_mode,
        ),
        render_operations_alert(operations_alert_agent()),
    )


with gr.Blocks(title="VisionGuard - Industrial Defect Detection on AMD") as demo:
    current_settings = get_settings()
    gr.Markdown(_hero_html())
    gr.HTML(render_mode_banner(current_settings.demo_mode))

    with gr.Tabs():
        with gr.TabItem("Image Inspection"):
            with gr.Row():
                with gr.Column(scale=1):
                    image_input = gr.Image(label="Upload product image", type="filepath")
                    line_id_input = gr.Textbox(label="Line ID", value=current_settings.default_line_id)
                    shift_input = gr.Dropdown(
                        label="Shift",
                        value=current_settings.default_shift,
                        choices=["morning", "swing", "night"],
                    )
                    inspect_btn = gr.Button("Inspect Product", variant="primary")

                    examples = available_example_paths()
                    if examples:
                        gr.Examples(examples=examples, inputs=image_input)

                with gr.Column(scale=1):
                    annotated_image = gr.Image(label="Annotated Inspection View", type="pil")
                    result_html = gr.HTML(
                        label="Inspection Result",
                        value=render_error_card("No inspection has been run yet."),
                    )
                    intelligence_html = gr.HTML(
                        label="Factory Intelligence",
                        value=render_error_card("Factory intelligence appears after an inspection is run."),
                    )
                    raw_json = gr.JSON(label="Raw Agent Output", value={})

            with gr.Row():
                performance_html = gr.HTML(
                    value=render_performance_panel(
                        get_analytics_summary(),
                        endpoint_status="idle" if not current_settings.demo_mode else "demo_mode",
                        demo_mode=current_settings.demo_mode,
                    )
                )
                operations_html = gr.HTML(value=render_operations_alert(operations_alert_agent()))

        with gr.TabItem("Video / Batch Inspection"):
            with gr.Row():
                with gr.Column(scale=1):
                    video_input = gr.Video(label="Upload product video", format="mp4")
                    sampling_interval = gr.Slider(
                        minimum=0.5,
                        maximum=5.0,
                        value=1.0,
                        step=0.5,
                        label="Sampling interval (seconds)",
                    )
                    max_frames = gr.Slider(
                        minimum=1,
                        maximum=30,
                        value=8,
                        step=1,
                        label="Max sampled frames",
                    )
                    video_line_id = gr.Textbox(label="Line ID", value=current_settings.default_line_id)
                    video_shift = gr.Dropdown(
                        label="Shift",
                        value=current_settings.default_shift,
                        choices=["morning", "swing", "night"],
                    )
                    inspect_video_btn = gr.Button("Inspect Video Batch", variant="primary")
                with gr.Column(scale=1):
                    video_status_html = gr.HTML(
                        value=render_error_card("No batch inspection has been run yet."),
                    )
                    video_progress_df = gr.Dataframe(
                        label="Frame Inspection Progress",
                        interactive=False,
                        value=pd.DataFrame(
                            columns=[
                                "frame_id",
                                "timestamp_seconds",
                                "defect_type",
                                "severity",
                                "action",
                                "confidence",
                            ]
                        ),
                    )
                    video_report_box = gr.Textbox(
                        label="Batch Inspection Report",
                        lines=10,
                        value="No batch report available yet.",
                    )
                    video_performance_html = gr.HTML(
                        value=render_performance_panel(
                            get_analytics_summary(),
                            endpoint_status="idle" if not current_settings.demo_mode else "demo_mode",
                            demo_mode=current_settings.demo_mode,
                        )
                    )
                    video_operations_html = gr.HTML(value=render_operations_alert(operations_alert_agent()))

    gr.Markdown("## Defect Event Log")
    logs_table = gr.Dataframe(label="Latest logged inspections", interactive=False, value=load_logs_df())

    with gr.Row():
        refresh_btn = gr.Button("Refresh Analytics")
        report_box = gr.Textbox(label="AI Shift Report", lines=8, value=reporter_agent())

    gr.HTML(render_architecture_footer())

    inspect_btn.click(
        fn=inspect_image_ui,
        inputs=[image_input, line_id_input, shift_input],
        outputs=[
            result_html,
            annotated_image,
            intelligence_html,
            performance_html,
            operations_html,
            raw_json,
            logs_table,
            report_box,
        ],
    )

    inspect_video_btn.click(
        fn=inspect_video_ui,
        inputs=[video_input, sampling_interval, max_frames, video_line_id, video_shift],
        outputs=[
            video_status_html,
            video_progress_df,
            video_report_box,
            video_performance_html,
            video_operations_html,
        ],
    )

    refresh_btn.click(
        fn=refresh_report,
        outputs=[logs_table, report_box, performance_html, operations_html],
    )


if __name__ == "__main__":
    demo.launch(
        server_name=current_settings.visionguard_host,
        server_port=current_settings.visionguard_port,
        css=APP_CSS,
        theme=gr.themes.Soft(),
    )
