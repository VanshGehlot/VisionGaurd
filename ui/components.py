from pathlib import Path
from html import escape


def severity_color(severity: str) -> str:
    if severity == "critical":
        return "#ef4444"
    if severity == "warning":
        return "#f59e0b"
    return "#22c55e"


def action_color(action: str) -> str:
    if action == "STOP_LINE":
        return "#ef4444"
    if action == "ALERT_OPERATOR":
        return "#f59e0b"
    return "#22c55e"


def action_label(action: str) -> str:
    return {
        "STOP_LINE": "Stop Line",
        "ALERT_OPERATOR": "Alert Operator",
        "LOG_WARNING": "Log Warning",
        "PASS": "Pass",
    }.get(action, action)


def render_result_card(event: dict) -> str:
    color = severity_color(str(event.get("severity", "ok")))
    action = str(event.get("action", "PASS"))
    action_text = action_label(action)
    action_style = action_color(action)
    status = action_text.upper() if action != "PASS" else "PRODUCT OK"
    severity = str(event.get("severity", "ok")).upper()
    defect_detected = "YES" if event.get("defect_detected") else "NO"
    mode_badge = (
        '<div class="vg-banner vg-demo-banner">Demo Mode: simulated inference result</div>'
        if event.get("demo_mode")
        else ""
    )

    return f"""
    <div class="vg-card">
      {mode_badge}
      <div class="vg-label">VisionGuard Inspection Result</div>
      <div class="vg-status" style="color:{color};">{status}</div>
      <div class="vg-chip-row">
        <span class="vg-chip" style="background:{action_style}; color:#ffffff;">{action_text}</span>
        <span class="vg-chip vg-chip-muted">{event.get("model_name", "Qwen/Qwen2.5-VL-7B-Instruct")}</span>
      </div>
        <div class="vg-grid">
        <div><b>Defect detected:</b> {defect_detected}</div>
        <div><b>Defect type:</b> {event.get("defect_type", "unknown")}</div>
        <div><b>Defect category:</b> {event.get("defect_category", "unknown")}</div>
        <div><b>Severity:</b> {severity}</div>
        <div><b>Confidence:</b> {float(event.get("confidence", 0.0)):.0%}</div>
        <div><b>Location:</b> {event.get("location", "unknown")}</div>
        <div><b>Recommended action:</b> {action_text}</div>
        <div><b>AMD MI300X latency:</b> {int(event.get("processing_ms", 0))}ms</div>
        <div><b>Model name:</b> {event.get("model_name", "Qwen/Qwen2.5-VL-7B-Instruct")}</div>
      </div>
      <div class="vg-explanation">{event.get("visual_explanation", "")}</div>
    </div>
    """.strip()


def render_error_card(message: str) -> str:
    return f"""
    <div class="vg-card vg-error">
      <div class="vg-label">VisionGuard Error</div>
      <div class="vg-status" style="color:#ef4444;">INSPECTION FAILED</div>
      <div class="vg-explanation">{message}</div>
    </div>
    """.strip()


def render_mode_banner(demo_mode: bool) -> str:
    if demo_mode:
        return """
        <div class="vg-banner vg-demo-banner">
          Demo Mode: simulated inference results are enabled.
        </div>
        """.strip()

    return """
    <div class="vg-banner vg-live-banner">
      Live Mode: waiting for AMD MI300X vLLM inference through VLLM_URL.
    </div>
    """.strip()


def render_architecture_footer() -> str:
    return """
    <div class="vg-footer">
      Image → Scanner Agent → AMD MI300X/vLLM → Qwen-VL → Logger Agent →
      MindsDB/SQLite → Reporter Agent
    </div>
    """.strip()


def render_factory_intelligence_panel(event: dict) -> str:
    return f"""
    <div class="vg-card">
      <div class="vg-label">Factory Intelligence</div>
      <div class="vg-status" style="font-size:22px; color:#0f172a;">Operational Guidance</div>
      <div class="vg-intel-section">
        <b>Visual Explanation</b>
        <p>{escape(str(event.get("visual_explanation", "")))}</p>
      </div>
      <div class="vg-intel-section">
        <b>Possible Causes</b>
        {_render_list(event.get("possible_causes", []))}
      </div>
      <div class="vg-intel-section">
        <b>Recommended Fix</b>
        {_render_list(event.get("recommended_fix", []))}
      </div>
      <div class="vg-intel-section">
        <b>Prevention Suggestions</b>
        {_render_list(event.get("prevention", []))}
      </div>
      <div class="vg-intel-section">
        <b>Factory Owner Summary</b>
        <p>{escape(str(event.get("factory_owner_summary", "")))}</p>
      </div>
    </div>
    """.strip()


def render_performance_panel(metrics: dict, endpoint_status: str, demo_mode: bool) -> str:
    model_name = metrics.get("model_name", "Qwen/Qwen2.5-VL-7B-Instruct")
    runtime = metrics.get("runtime", "AMD MI300X + ROCm + vLLM")
    latest_latency = int(metrics.get("latest_latency_ms", 0) or 0)
    avg_latency = float(metrics.get("avg_latency_ms", 0.0) or 0.0)
    images_per_min = int(metrics.get("estimated_images_per_min", 0) or 0)
    total = int(metrics.get("total_inspected", 0) or 0)
    defects = int(metrics.get("defects_found", 0) or 0)
    defect_rate = float(metrics.get("defect_rate", 0.0) or 0.0)
    status_label = endpoint_status if not demo_mode else "demo_mode"
    return f"""
    <div class="vg-card">
      <div class="vg-label">AMD Inference Status</div>
      <div class="vg-status" style="font-size:22px; color:#0f172a;">Powered by AMD MI300X · ROCm · vLLM · Qwen-VL</div>
      <div class="vg-grid">
        <div><b>Endpoint:</b> {escape(status_label)}</div>
        <div><b>Model:</b> {escape(str(model_name))}</div>
        <div><b>Latest latency:</b> {latest_latency}ms</div>
        <div><b>Average latency:</b> {avg_latency:.0f}ms</div>
        <div><b>Images inspected:</b> {total}</div>
        <div><b>Defects found:</b> {defects}</div>
        <div><b>Defect rate:</b> {defect_rate:.1f}%</div>
        <div><b>Estimated throughput:</b> {images_per_min} images/min</div>
        <div><b>Runtime:</b> {escape(str(runtime))}</div>
      </div>
    </div>
    """.strip()


def render_operations_alert(alert_text: str) -> str:
    paragraphs = "<br/><br/>".join(escape(part).replace("\n", "<br/>") for part in alert_text.split("\n\n"))
    return f"""
    <div class="vg-card">
      <div class="vg-label">Operations Alert</div>
      <div class="vg-status" style="font-size:22px; color:#0f172a;">Factory Operations Intelligence</div>
      <div class="vg-explanation">{paragraphs}</div>
    </div>
    """.strip()


def _render_list(items: list[str]) -> str:
    if not items:
        return "<p>No additional guidance available.</p>"
    rendered = "".join(f"<li>{escape(str(item))}</li>" for item in items)
    return f"<ul class=\"vg-list\">{rendered}</ul>"


def available_example_paths() -> list[list[str]]:
    candidates = [
        "examples/bottle_good_0.jpg",
        "examples/bottle_broken_large_0.jpg",
        "examples/bottle_broken_small_0.jpg",
        "examples/bottle_contamination_0.jpg",
    ]
    return [[path] for path in candidates if Path(path).exists()]
