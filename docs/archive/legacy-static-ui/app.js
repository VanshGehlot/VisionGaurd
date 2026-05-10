const state = {
  frontendDemoMode: false,
  apiUnavailable: false,
  activeMode: "image",
  selectedImageFile: null,
  selectedImageSample: "./examples/bottle_good_0.jpg",
  selectedVideoFile: null,
  latestResult: null,
  metrics: null,
  events: [],
  report: "",
  operationsAlert: "",
  health: null,
};

const els = {
  systemHealthPill: document.querySelector("#system-health-pill"),
  systemHealthDot: document.querySelector("#system-health-dot"),
  systemHealthLabel: document.querySelector("#system-health-label"),
  frontendDemoBadge: document.querySelector("#frontend-demo-badge"),
  frontendEndpointBadge: document.querySelector("#frontend-endpoint-badge"),
  heroLatency: document.querySelector("#hero-latency"),
  heroRuntime: document.querySelector("#hero-runtime"),
  heroModel: document.querySelector("#hero-model"),
  heroActionEngine: document.querySelector("#hero-action-engine"),
  heroPreviewImage: document.querySelector("#hero-preview-image"),
  heroPreviewStatus: document.querySelector("#hero-preview-status"),
  heroPreviewText: document.querySelector("#hero-preview-text"),
  heroPreviewLatency: document.querySelector("#hero-preview-latency"),
  heroPreviewReport: document.querySelector("#hero-preview-report"),
  imageInput: document.querySelector("#image-input"),
  imageDropzone: document.querySelector("#image-dropzone"),
  imageSelectionLabel: document.querySelector("#image-selection-label"),
  imageLineId: document.querySelector("#image-line-id"),
  imageShift: document.querySelector("#image-shift"),
  videoInput: document.querySelector("#video-input"),
  videoSelectionLabel: document.querySelector("#video-selection-label"),
  videoLineId: document.querySelector("#video-line-id"),
  videoShift: document.querySelector("#video-shift"),
  videoInterval: document.querySelector("#video-interval"),
  videoIntervalLabel: document.querySelector("#video-interval-label"),
  videoFrames: document.querySelector("#video-frames"),
  videoFramesLabel: document.querySelector("#video-frames-label"),
  inspectImageButton: document.querySelector("#inspect-image-button"),
  inspectVideoButton: document.querySelector("#inspect-video-button"),
  toggleDemoButton: document.querySelector("#toggle-demo-button"),
  refreshEventsButton: document.querySelector("#refresh-events-button"),
  inspectionImage: document.querySelector("#inspection-image"),
  annotatedImage: document.querySelector("#annotated-image"),
  annotatedCaption: document.querySelector("#annotated-caption"),
  inspectionLoading: document.querySelector("#inspection-loading"),
  inspectionError: document.querySelector("#inspection-error"),
  resultHeadline: document.querySelector("#result-headline"),
  resultStatusBadge: document.querySelector("#result-status-badge"),
  detailStatus: document.querySelector("#detail-status"),
  detailDefectType: document.querySelector("#detail-defect-type"),
  detailDefectCategory: document.querySelector("#detail-defect-category"),
  detailSeverity: document.querySelector("#detail-severity"),
  detailConfidence: document.querySelector("#detail-confidence"),
  detailLocation: document.querySelector("#detail-location"),
  detailAction: document.querySelector("#detail-action"),
  detailLatency: document.querySelector("#detail-latency"),
  detailModel: document.querySelector("#detail-model"),
  detailRuntime: document.querySelector("#detail-runtime"),
  visualExplanation: document.querySelector("#visual-explanation"),
  possibleCauses: document.querySelector("#possible-causes"),
  recommendedFix: document.querySelector("#recommended-fix"),
  preventionList: document.querySelector("#prevention-list"),
  ownerSummary: document.querySelector("#owner-summary"),
  opsTotalInspected: document.querySelector("#ops-total-inspected"),
  opsDefectsFound: document.querySelector("#ops-defects-found"),
  opsDefectRate: document.querySelector("#ops-defect-rate"),
  opsCriticalEvents: document.querySelector("#ops-critical-events"),
  opsAverageLatency: document.querySelector("#ops-average-latency"),
  shiftReport: document.querySelector("#shift-report"),
  operationsAlert: document.querySelector("#operations-alert"),
  eventTableBody: document.querySelector("#event-table-body"),
  perfEndpointStatus: document.querySelector("#perf-endpoint-status"),
  perfModelName: document.querySelector("#perf-model-name"),
  perfLatestLatency: document.querySelector("#perf-latest-latency"),
  perfAverageLatency: document.querySelector("#perf-average-latency"),
  perfThroughput: document.querySelector("#perf-throughput"),
  perfTotalImages: document.querySelector("#perf-total-images"),
  perfRuntime: document.querySelector("#perf-runtime"),
  healthApi: document.querySelector("#health-api"),
  healthVllm: document.querySelector("#health-vllm"),
  healthDb: document.querySelector("#health-db"),
  healthMindsdb: document.querySelector("#health-mindsdb"),
  healthDemoMode: document.querySelector("#health-demo-mode"),
  modeImage: document.querySelector("#mode-image"),
  modeVideo: document.querySelector("#mode-video"),
  imageModePanel: document.querySelector("#image-mode-panel"),
  videoModePanel: document.querySelector("#video-mode-panel"),
  videoBatchStatus: document.querySelector("#video-batch-status"),
  videoBatchTable: document.querySelector("#video-batch-table"),
  videoBatchReport: document.querySelector("#video-batch-report"),
  sampleChips: [...document.querySelectorAll(".sample-chip")],
  jumpButtons: [...document.querySelectorAll("[data-jump]")],
};

function apiUrl(path) {
  return path;
}

async function fetchJson(path, options = {}) {
  const response = await fetch(apiUrl(path), options);
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const payload = await response.json();
      detail = payload.detail || payload.message || detail;
    } catch {
      // ignore
    }
    throw new Error(detail);
  }
  return response.json();
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function formatPercent(value) {
  return `${Math.round((Number(value) || 0) * 100)}%`;
}

function formatSeverityClass(value) {
  const severity = String(value || "info").toLowerCase();
  if (severity === "critical") return "critical";
  if (severity === "warning") return "warning";
  if (severity === "ok") return "ok";
  return "info";
}

function formatActionClass(value) {
  return String(value || "pass").toLowerCase();
}

function formatTitleCase(value) {
  return String(value || "")
    .replaceAll("_", " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

function setMode(mode) {
  state.activeMode = mode;
  const imageActive = mode === "image";
  els.modeImage.classList.toggle("active", imageActive);
  els.modeVideo.classList.toggle("active", !imageActive);
  els.imageModePanel.classList.toggle("active", imageActive);
  els.videoModePanel.classList.toggle("active", !imageActive);
}

function updateDemoBadge() {
  const label = state.frontendDemoMode ? "Demo Mode — simulated inference output" : "Live Mode";
  els.frontendDemoBadge.textContent = label;
  els.toggleDemoButton.textContent = state.frontendDemoMode ? "Return to Live Mode" : "Run in Demo Mode";
  els.healthDemoMode.textContent = state.frontendDemoMode ? "On" : "Off";
}

function setSample(samplePath) {
  state.selectedImageSample = samplePath;
  state.selectedImageFile = null;
  els.inspectionImage.src = samplePath;
  els.annotatedImage.src = samplePath;
  const label = samplePath.split("/").pop();
  els.imageSelectionLabel.textContent = `Selected sample: ${label}`;
  els.sampleChips.forEach((chip) => {
    chip.classList.toggle("active", chip.dataset.sample === samplePath);
  });
}

function attachDropzone(dropzone, input, onFile) {
  dropzone.addEventListener("dragover", (event) => {
    event.preventDefault();
    dropzone.classList.add("dragover");
  });
  dropzone.addEventListener("dragleave", () => dropzone.classList.remove("dragover"));
  dropzone.addEventListener("drop", (event) => {
    event.preventDefault();
    dropzone.classList.remove("dragover");
    const file = event.dataTransfer?.files?.[0];
    if (file) onFile(file);
  });
  input.addEventListener("change", (event) => {
    const file = event.target.files?.[0];
    if (file) onFile(file);
  });
}

function setImageFile(file) {
  state.selectedImageFile = file;
  els.imageSelectionLabel.textContent = `Selected file: ${file.name}`;
  els.inspectionImage.src = URL.createObjectURL(file);
  els.sampleChips.forEach((chip) => chip.classList.remove("active"));
}

function setVideoFile(file) {
  state.selectedVideoFile = file;
  els.videoSelectionLabel.textContent = `Selected file: ${file.name}`;
}

function renderList(target, items, emptyText) {
  if (!items || items.length === 0) {
    target.innerHTML = `<li>${escapeHtml(emptyText)}</li>`;
    return;
  }
  target.innerHTML = items.map((item) => `<li>${escapeHtml(item)}</li>`).join("");
}

function setLoading(active, message = "Inspecting with Qwen-VL on AMD MI300X…") {
  els.inspectionLoading.textContent = message;
  els.inspectionLoading.classList.toggle("hidden", !active);
}

function setInspectionError(message, showDemoAction = false) {
  if (!message) {
    els.inspectionError.classList.add("hidden");
    els.inspectionError.innerHTML = "";
    return;
  }
  const button = showDemoAction
    ? `<button class="button button-secondary small" id="inline-demo-button">Run in Demo Mode</button>`
    : "";
  els.inspectionError.innerHTML = `
    <div>${escapeHtml(message)}</div>
    ${button}
  `;
  els.inspectionError.classList.remove("hidden");
  const inlineButton = document.querySelector("#inline-demo-button");
  if (inlineButton) {
    inlineButton.addEventListener("click", () => {
      state.frontendDemoMode = true;
      updateDemoBadge();
      setInspectionError("");
    });
  }
}

function renderResult(result) {
  state.latestResult = result;
  const defectDetected = Boolean(result.defect_detected);
  const severityClass = defectDetected ? formatSeverityClass(result.severity) : "ok";
  const statusLabel = defectDetected ? "Defect Detected" : "Product OK";
  const actionLabel = String(result.action || "PASS");
  const severityLabel = defectDetected
    ? String(result.severity || "warning").toUpperCase()
    : "PASS";

  els.resultHeadline.textContent = defectDetected ? "Defect Detected" : "Product OK";
  els.resultStatusBadge.textContent = severityLabel;
  els.resultStatusBadge.className = `status-badge status-${severityClass}`;
  els.detailStatus.textContent = statusLabel;
  els.detailDefectType.textContent = formatTitleCase(result.defect_type || "none");
  els.detailDefectCategory.textContent = formatTitleCase(result.defect_category || "none");
  els.detailSeverity.textContent = formatTitleCase(result.severity || "ok");
  els.detailConfidence.textContent = formatPercent(result.confidence || 0);
  els.detailLocation.textContent = result.location || "unknown";
  els.detailAction.textContent = actionLabel;
  els.detailLatency.textContent = `${result.processing_ms || 0}ms`;
  els.detailModel.textContent = result.model_name || "Qwen/Qwen2.5-VL-7B-Instruct";
  els.detailRuntime.textContent = result.runtime || "AMD MI300X · ROCm · vLLM";
  if (result.annotated_image) {
    els.annotatedImage.src = result.annotated_image;
  }
  els.annotatedCaption.textContent = defectDetected ? "Approximate defect region" : "PASS confirmation";

  els.visualExplanation.textContent = result.visual_explanation || "No visual explanation available.";
  renderList(els.possibleCauses, result.possible_causes, "No active causes yet.");
  renderList(els.recommendedFix, result.recommended_fix, "No active fix guidance yet.");
  renderList(els.preventionList, result.prevention, "No prevention guidance yet.");
  els.ownerSummary.textContent =
    result.factory_owner_summary || "No owner summary available.";

  els.heroPreviewStatus.textContent = actionLabel;
  els.heroPreviewText.textContent =
    result.factory_owner_summary || result.visual_explanation || "No inspection summary available.";
  els.heroPreviewLatency.textContent = `${result.processing_ms || 0}ms`;
  els.heroPreviewImage.src = els.inspectionImage.src;
  els.heroModel.textContent = (result.model_name || "Qwen-VL").replace("Qwen/", "");
  els.heroLatency.textContent = `${result.processing_ms || 0}ms`;
}

function renderMetrics(metrics = state.metrics, events = state.events) {
  if (!metrics) return;
  state.metrics = metrics;

  const criticalCount = (events || []).filter((event) => String(event.severity).toLowerCase() === "critical").length;
  els.opsTotalInspected.textContent = String(metrics.total_inspected ?? 0);
  els.opsDefectsFound.textContent = String(metrics.defects_found ?? 0);
  els.opsDefectRate.textContent = `${Number(metrics.defect_rate ?? 0).toFixed(1)}%`;
  els.opsCriticalEvents.textContent = String(criticalCount);
  els.opsAverageLatency.textContent = `${Math.round(Number(metrics.avg_latency_ms ?? 0))}ms`;

  els.perfEndpointStatus.textContent = formatTitleCase(metrics.endpoint_status || "pending");
  els.perfModelName.textContent = metrics.model_name || "Qwen/Qwen2.5-VL-7B-Instruct";
  els.perfLatestLatency.textContent = `${metrics.latest_latency_ms ?? 0}ms`;
  els.perfAverageLatency.textContent = `${Math.round(Number(metrics.avg_latency_ms ?? 0))}ms`;
  els.perfThroughput.textContent = String(metrics.estimated_images_per_min ?? 0);
  els.perfTotalImages.textContent = String(metrics.total_inspected ?? 0);
  els.perfRuntime.textContent = metrics.runtime || "AMD MI300X · ROCm · vLLM";

  els.heroRuntime.textContent = metrics.runtime ? metrics.runtime.split(" · ")[0] : "AMD MI300X";
  els.frontendEndpointBadge.textContent = `Endpoint ${formatTitleCase(metrics.endpoint_status || "pending")}`;
}

function renderReport(reportText) {
  els.shiftReport.textContent = reportText || "Shift Quality Report pending.";
  els.heroPreviewReport.textContent = reportText
    ? reportText.split("\n").slice(0, 2).join(" ")
    : "Shift report pending.";
}

function renderOperationsAlert(alertText) {
  els.operationsAlert.innerHTML = escapeHtml(alertText || "No operations alert available.").replaceAll("\n", "<br/>");
}

function renderHealth(health) {
  state.health = health;
  const endpoint = String(health.vllm_endpoint || "pending");
  const dotClass =
    endpoint === "connected" ? "connected" : endpoint === "unavailable" ? "critical" : "pending";
  els.systemHealthDot.className = `health-dot ${dotClass}`;
  els.systemHealthLabel.textContent =
    endpoint === "connected" ? "System online" : endpoint === "demo_mode" ? "Demo mode active" : "System pending";
  els.healthApi.textContent = formatTitleCase(health.api || "online");
  els.healthVllm.textContent = formatTitleCase(endpoint);
  els.healthDb.textContent = formatTitleCase(health.database || "connected");
  els.healthMindsdb.textContent = formatTitleCase(health.mindsdb || "optional");
  if (!state.frontendDemoMode) {
    els.healthDemoMode.textContent = health.demo_mode ? "On" : "Off";
  }
}

function renderEvents(events) {
  state.events = events || [];
  if (!events || events.length === 0) {
    els.eventTableBody.innerHTML = `<tr><td colspan="7" class="empty-cell">No inspection events yet.</td></tr>`;
    return;
  }

  els.eventTableBody.innerHTML = events
    .map((event) => {
      const severityClass = formatSeverityClass(event.severity);
      const actionClass = formatActionClass(event.action || event.action_taken || "pass");
      return `
        <tr>
          <td>${escapeHtml(String(event.timestamp || "").replace("T", " ").slice(0, 19))}</td>
          <td>${escapeHtml(event.image_id || "unknown")}</td>
          <td>${escapeHtml(formatTitleCase(event.defect_type || "none"))}</td>
          <td><span class="severity-pill ${severityClass}">${escapeHtml(formatTitleCase(event.severity || "ok"))}</span></td>
          <td>${Math.round(Number(event.confidence || 0) * 100)}%</td>
          <td><span class="action-pill ${actionClass}">${escapeHtml(event.action || event.action_taken || "PASS")}</span></td>
          <td>${escapeHtml(String(event.processing_ms || 0))}ms</td>
        </tr>
      `;
    })
    .join("");
}

function renderVideoBatch(response) {
  if (!response || !response.frames) return;
  els.videoBatchStatus.textContent = `Processed ${response.frames.length} sampled frames.`;
  els.videoBatchReport.textContent = response.batch_report || "No batch report available.";
  els.videoBatchTable.innerHTML = response.frames
    .map(
      (frame) => `
        <tr>
          <td>${escapeHtml(frame.frame_id)}</td>
          <td>${Number(frame.timestamp_seconds).toFixed(2)}s</td>
          <td>${escapeHtml(formatTitleCase(frame.defect_type))}</td>
          <td><span class="severity-pill ${formatSeverityClass(frame.severity)}">${escapeHtml(formatTitleCase(frame.severity))}</span></td>
          <td><span class="action-pill ${formatActionClass(frame.action)}">${escapeHtml(frame.action)}</span></td>
        </tr>
      `
    )
    .join("");
}

async function getSelectedImageFile() {
  if (state.selectedImageFile) {
    return state.selectedImageFile;
  }
  if (state.selectedImageSample) {
    const response = await fetch(state.selectedImageSample);
    const blob = await response.blob();
    return new File([blob], state.selectedImageSample.split("/").pop(), { type: blob.type || "image/jpeg" });
  }
  throw new Error("Select an image or sample before inspection.");
}

async function refreshDashboard() {
  const [health, metrics, eventsPayload, reportPayload, alertPayload] = await Promise.all([
    fetchJson("/health"),
    fetchJson("/metrics"),
    fetchJson("/events"),
    fetchJson("/report"),
    fetchJson("/operations-alert"),
  ]);
  state.apiUnavailable = false;
  renderHealth(health);
  renderEvents(eventsPayload.events || []);
  renderMetrics(metrics, eventsPayload.events || []);
  renderReport(reportPayload.report);
  renderOperationsAlert(alertPayload.alert);
}

async function inspectImage() {
  setLoading(true, "Inspecting product frame… Running Qwen-VL inference on AMD MI300X…");
  setInspectionError("");
  try {
    const file = await getSelectedImageFile();
    const formData = new FormData();
    formData.append("image", file);
    formData.append("line_id", els.imageLineId.value.trim() || "LINE-A1");
    formData.append("shift", els.imageShift.value);

    const result = await fetchJson(`/inspect-image?force_demo=${state.frontendDemoMode}`, {
      method: "POST",
      body: formData,
    });

    renderResult(result);
    renderMetrics(result.metrics);
    renderReport(result.report);
    renderOperationsAlert(result.operations_alert);
    await refreshEventsOnly();
  } catch (error) {
    state.apiUnavailable = true;
    setInspectionError(
      error.message || "Inference endpoint unavailable. Set VLLM_URL and validate the AMD vLLM server before live inspection.",
      true
    );
  } finally {
    setLoading(false);
  }
}

async function inspectVideo() {
  if (!state.selectedVideoFile) {
    els.videoBatchStatus.textContent = "Select a short video before batch inspection.";
    return;
  }

  els.videoBatchStatus.textContent = "Inspecting product frame… Running Qwen-VL inference on AMD MI300X…";
  els.videoBatchReport.textContent = "Generating defect intelligence and batch report…";
  try {
    const formData = new FormData();
    formData.append("video", state.selectedVideoFile);
    formData.append("line_id", els.videoLineId.value.trim() || "LINE-A1");
    formData.append("shift", els.videoShift.value);
    formData.append("sampling_interval", els.videoInterval.value);
    formData.append("max_frames", els.videoFrames.value);
    const result = await fetchJson(`/inspect-video?force_demo=${state.frontendDemoMode}`, {
      method: "POST",
      body: formData,
    });
    renderVideoBatch(result);
    renderMetrics(result.metrics);
    renderOperationsAlert(result.operations_alert);
    if (result.batch_report) {
      els.shiftReport.textContent = result.batch_report;
    }
    await refreshEventsOnly();
  } catch (error) {
    els.videoBatchStatus.textContent =
      error.message || "Video inspection failed. Keep the image workflow as the primary demo path.";
  }
}

async function refreshEventsOnly() {
  const [eventsPayload, health] = await Promise.all([fetchJson("/events"), fetchJson("/health")]);
  renderEvents(eventsPayload.events || []);
  renderHealth(health);
  if (state.metrics) {
    renderMetrics(state.metrics, eventsPayload.events || []);
  }
}

function bindEvents() {
  els.jumpButtons.forEach((button) => {
    button.addEventListener("click", () => {
      const target = document.querySelector(button.dataset.jump);
      target?.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  });

  els.modeImage.addEventListener("click", () => setMode("image"));
  els.modeVideo.addEventListener("click", () => setMode("video"));

  els.sampleChips.forEach((chip) => {
    chip.addEventListener("click", () => setSample(chip.dataset.sample));
  });

  attachDropzone(els.imageDropzone, els.imageInput, setImageFile);
  attachDropzone(els.videoInput.parentElement, els.videoInput, setVideoFile);

  els.inspectImageButton.addEventListener("click", inspectImage);
  els.inspectVideoButton.addEventListener("click", inspectVideo);
  els.toggleDemoButton.addEventListener("click", () => {
    state.frontendDemoMode = !state.frontendDemoMode;
    updateDemoBadge();
    setInspectionError("");
  });
  els.refreshEventsButton.addEventListener("click", refreshDashboard);
  els.videoInterval.addEventListener("input", () => {
    els.videoIntervalLabel.textContent = `${Number(els.videoInterval.value).toFixed(1)}s`;
  });
  els.videoFrames.addEventListener("input", () => {
    els.videoFramesLabel.textContent = `${els.videoFrames.value} frames`;
  });
}

function renderFileProtocolFallback() {
  state.apiUnavailable = true;
  renderHealth({
    api: "pending",
    vllm_endpoint: "pending",
    database: "connected",
    mindsdb: "optional",
    demo_mode: false,
  });
  setInspectionError(
    "This premium frontend is designed to run through the FastAPI wrapper. Start the API server and open VisionGuard over HTTP for live inspection.",
    false
  );
}

async function bootstrap() {
  bindEvents();
  updateDemoBadge();
  setSample(state.selectedImageSample);

  if (window.location.protocol === "file:") {
    renderFileProtocolFallback();
    return;
  }

  try {
    await refreshDashboard();
  } catch (error) {
    state.apiUnavailable = true;
    setInspectionError(
      error.message || "Inference endpoint unavailable. Set VLLM_URL and validate the AMD vLLM server before live inspection.",
      true
    );
  }
}

bootstrap();
