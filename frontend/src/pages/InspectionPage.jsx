import { useEffect, useMemo, useRef, useState } from "react";
import ErrorState from "../components/ErrorState";
import FactoryIntelligencePanel from "../components/FactoryIntelligencePanel";
import InspectionResultCard from "../components/InspectionResultCard";
import LoadingState from "../components/LoadingState";
import StatusBadge from "../components/StatusBadge";
import { fetchExampleAsFile, getHealth, inspectImage, inspectVideo } from "../lib/api";
import { useAppContext } from "../state/AppContext";
import { getRuntimeStatus, sanitizeOperatorError } from "../lib/ui";

const samples = [
  { label: "Dented Bottle", path: "/examples/dented_stainless_steel_water_bottle.png", filename: "dented_stainless_steel_water_bottle.png", type: "Structural review" },
  { label: "Surface Crack", path: "/examples/bottle_broken_large_1.jpg", filename: "broken_large.jpg", type: "Operator alert" },
  { label: "Neck Crack", path: "/examples/bottle_broken_small_1.jpg", filename: "broken_small_1.jpg", type: "Structural issue" },
  { label: "Contamination", path: "/examples/bottle_contamination_1.jpg", filename: "contamination_1.jpg", type: "Operator review" },
];

const inspectionModelOptions = [
  { value: "base_visionguard", label: "Base VisionGuard Model", meta: "Generic visual QA route" },
  { value: "factory_finetuned", label: "Factory Fine-Tuned Model", meta: "Uses active factory route" },
  { value: "pcb_adapter_v1", label: "PCB Adapter v1", meta: "DeepPCB demo adapter" },
  { value: "nano_defects_eval", label: "NanoDefects Bottle QA — Evaluation Route", meta: "Baseline evaluated; adapter training pending" },
];

const acceptedImageExtension = /\.(avif|bmp|gif|heic|heif|jpe?g|png|tiff?|webp)$/i;
const heifImageExtension = /\.(heic|heif)$/i;

function isHeifImageFile(file) {
  if (!file) return false;
  const type = (file.type || "").toLowerCase();
  return type === "image/heic" || type === "image/heif" || heifImageExtension.test(file.name || "");
}

function isPotentialImageFile(file) {
  if (!file) return false;
  return file.type?.startsWith("image/") || acceptedImageExtension.test(file.name || "");
}

function canDecodeImageFile(file) {
  return new Promise((resolve) => {
    const url = URL.createObjectURL(file);
    const image = new Image();
    image.onload = () => {
      URL.revokeObjectURL(url);
      resolve(true);
    };
    image.onerror = () => {
      URL.revokeObjectURL(url);
      resolve(false);
    };
    image.src = url;
  });
}

function isManualReview(result) {
  return result?.action === "ALERT_OPERATOR" && !result?.defect_detected;
}

function actionTone(result) {
  if (!result) return "neutral";
  if (result.action === "STOP_LINE" || result.severity === "critical") return "critical";
  if (result.action === "ALERT_OPERATOR" || result.action === "LOG_WARNING" || result.severity === "warning") return "warning";
  return "ok";
}

function customerAction(result) {
  if (!result) {
    return {
      eyebrow: "Inspection workspace",
      title: "Turn a product frame into a line decision.",
      copy: "Select a product image, run inspection on AMD MI300X, and receive one clear plant action with evidence and follow-up guidance.",
      label: "Awaiting inspection",
      actionCopy: "Upload or select a frame to receive one release decision, supporting evidence, and the recommended next step.",
    };
  }
  if (result.action === "STOP_LINE") {
    return {
      eyebrow: "Latest inspection decision",
      title: "Stop line and contain the batch.",
      copy: "A likely defect was found with critical enough risk to interrupt automatic release and trigger immediate containment.",
      label: "Immediate next step",
      actionCopy: "Remove this item, inspect nearby units, and verify the upstream process before resuming full-speed production.",
    };
  }
  if (isManualReview(result)) {
    return {
      eyebrow: "Latest inspection decision",
      title: "Manual review required before release.",
      copy: "The model did not confirm a visible defect strongly enough to auto-release this unit, so the system held it for operator review.",
      label: "Immediate next step",
      actionCopy: "Route this item to operator review, capture a clearer confirmation frame if available, and keep similar uncertain units out of silent release.",
    };
  }
  if (result.action === "ALERT_OPERATOR" || result.action === "LOG_WARNING") {
    return {
      eyebrow: "Latest inspection decision",
      title: "Warning-level issue detected.",
      copy: "A likely defect or process anomaly was found, but the line can continue while the operator reviews this item and nearby units.",
      label: "Immediate next step",
      actionCopy: "Send the item to operator review, inspect similar units in the same batch, and watch for repeated warning patterns.",
    };
  }
  return {
    eyebrow: "Latest inspection decision",
    title: "Release approved.",
    copy: "No visible defect was confirmed and the frame met the threshold for automatic release.",
    label: "Immediate next step",
    actionCopy: "Continue production, log this pass decision, and keep sampling quality stable for the next items.",
  };
}

function evidenceHeading(result) {
  if (!result) return { eyebrow: "Evidence panel", title: "Frame ready for inspection" };
  if (isManualReview(result)) {
    return {
      eyebrow: "Evidence for manual review",
      title: "No confirmed defect region. Release confidence stayed below threshold.",
    };
  }
  if (result.annotation_mode === "heuristic_bbox") {
    return { eyebrow: "Evidence panel", title: "Review the highlighted region before acting." };
  }
  if (result.annotation_mode === "approximate_region") {
    return { eyebrow: "Evidence panel", title: "Approximate defect region from the model output." };
  }
  if (result.defect_detected) {
    return { eyebrow: "Evidence panel", title: "Visual evidence supporting the defect decision." };
  }
  return { eyebrow: "Evidence panel", title: "No visible defect signal was confirmed." };
}

function evidenceSummary(result) {
  if (!result) {
    return "Once inspection completes, this panel will show the model overlay, the source frame, and the reason the line decision was made.";
  }
  if (isManualReview(result)) {
    return "This frame was held because the system could not safely auto-release it. Use the original frame and confidence readout to decide whether to approve, rescan, or route to review.";
  }
  if (result.defect_detected) {
    return result.visual_explanation || "Review the highlighted region, the detected category, and the recommended action before releasing the item.";
  }
  return "The model did not confirm a visible defect. Use this frame as the release evidence for the logged PASS decision.";
}

function isEndpointUnavailableError(message) {
  const copy = String(message || "").toLowerCase();
  return (
    copy.includes("inference endpoint unavailable") ||
    copy.includes("live amd inference is unavailable") ||
    copy.includes("runtime endpoint") ||
    copy.includes("localhost:8000") ||
    copy.includes("connection refused")
  );
}

const LIVE_OFFLINE_MESSAGE = "Live AMD inference is unavailable. Reconnect the runtime endpoint or switch to demo mode.";

async function isLiveRuntimeUnavailable() {
  try {
    const status = await getHealth();
    return !status?.demo_mode && status?.vllm_reachable === false;
  } catch {
    return true;
  }
}

export default function InspectionPage() {
  const { frontendDemoMode, setFrontendDemoMode, refreshSystemData, health, metrics, loading: systemLoading } = useAppContext();
  const [activeTab, setActiveTab] = useState("image");
  const [lineId, setLineId] = useState("LINE-A1");
  const [shift, setShift] = useState("morning");
  const [modelRoute, setModelRoute] = useState(() => {
    const requested = new URLSearchParams(window.location.search).get("model");
    return inspectionModelOptions.some((option) => option.value === requested) ? requested : "base_visionguard";
  });
  const [imagePreview, setImagePreview] = useState(samples[0].path);
  const [imageFile, setImageFile] = useState(null);
  const [selectedSample, setSelectedSample] = useState(samples[0]);
  const [result, setResult] = useState(null);
  const [videoFile, setVideoFile] = useState(null);
  const [videoInterval, setVideoInterval] = useState(1);
  const [maxFrames, setMaxFrames] = useState(6);
  const [videoBatch, setVideoBatch] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [isImageDragging, setIsImageDragging] = useState(false);
  const [isVideoDragging, setIsVideoDragging] = useState(false);
  const fileInputRef = useRef(null);
  const selectedModelOption = useMemo(
    () => inspectionModelOptions.find((option) => option.value === modelRoute) || inspectionModelOptions[0],
    [modelRoute],
  );

  useEffect(() => {
    return () => {
      if (imagePreview?.startsWith("blob:")) {
        URL.revokeObjectURL(imagePreview);
      }
    };
  }, [imagePreview]);

  const runtimeStatus = getRuntimeStatus({ health, metrics, frontendDemoMode, loading: systemLoading });
  const inferenceBadgeTone = runtimeStatus.tone;
  const inferenceBadgeLabel = runtimeStatus.badge;
  const action = customerAction(result);
  const tone = actionTone(result);
  const evidence = useMemo(() => evidenceHeading(result), [result]);

  function resetInspectionState() {
    setResult(null);
    setError("");
    setVideoBatch(null);
  }

  async function selectImageFile(file) {
    if (!file) return;
    if (!isPotentialImageFile(file)) {
      resetInspectionState();
      setError("Please choose a valid image file such as PNG, JPEG, WEBP, HEIC, HEIF, or TIFF.");
      return;
    }
    const canDecode = isHeifImageFile(file) || (await canDecodeImageFile(file));
    if (!canDecode) {
      resetInspectionState();
      setError("This file could not be opened as an image. Please choose a valid product image and try again.");
      return;
    }
    resetInspectionState();
    setSelectedSample(null);
    setImageFile(file);
    setImagePreview((currentPreview) => {
      if (currentPreview?.startsWith("blob:")) {
        URL.revokeObjectURL(currentPreview);
      }
      return URL.createObjectURL(file);
    });
  }

  function handleImageFileChange(event) {
    selectImageFile(event.target.files?.[0]);
  }

  function handleImageDrop(event) {
    event.preventDefault();
    event.stopPropagation();
    setIsImageDragging(false);
    const file = Array.from(event.dataTransfer?.files || []).find(isPotentialImageFile);
    if (!file) {
      setError("Please drop a valid image file.");
      return;
    }
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
    selectImageFile(file);
  }

  function handleDragOver(event, setDragging) {
    event.preventDefault();
    event.stopPropagation();
    setDragging(true);
  }

  function handleDragLeave(event, setDragging) {
    event.preventDefault();
    event.stopPropagation();
    if (!event.currentTarget.contains(event.relatedTarget)) {
      setDragging(false);
    }
  }

  function selectVideoFile(file) {
    if (!file) return;
    setError("");
    setVideoBatch(null);
    setVideoFile(file);
  }

  function handleVideoDrop(event) {
    event.preventDefault();
    event.stopPropagation();
    setIsVideoDragging(false);
    const file = Array.from(event.dataTransfer?.files || []).find((item) => item.type.startsWith("video/"));
    if (!file) {
      setError("Please drop a valid video file.");
      return;
    }
    selectVideoFile(file);
  }

  function handleSampleSelect(sample) {
    resetInspectionState();
    setSelectedSample(sample);
    setImageFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
    setImagePreview((currentPreview) => {
      if (currentPreview?.startsWith("blob:")) {
        URL.revokeObjectURL(currentPreview);
      }
      return sample.path;
    });
  }

  async function handleInspectImage() {
    if (!frontendDemoMode && (runtimeStatus.id === "offline" || await isLiveRuntimeUnavailable())) {
      setResult(null);
      setVideoBatch(null);
      setError(LIVE_OFFLINE_MESSAGE);
      return;
    }
    setLoading(true);
    setError("");
    setResult(null);
    setVideoBatch(null);
    try {
      const file = imageFile
        ? imageFile
        : await fetchExampleAsFile(selectedSample?.path || samples[0].path, selectedSample?.filename || samples[0].filename);

      const payload = await inspectImage({
        file,
        lineId,
        shift,
        modelRoute,
        forceDemo: frontendDemoMode,
      });

      setResult({ ...payload, inspected_source_url: imagePreview });
      setError("");
      refreshSystemData().catch((refreshError) => {
        console.error("VisionGuard refresh after image inspection failed", refreshError);
      });
    } catch (err) {
      console.error("VisionGuard image inspection failed", err);
      setError(sanitizeOperatorError(err?.message || err, "VisionGuard could not complete the image inspection."));
    } finally {
      setLoading(false);
    }
  }

  async function handleInspectVideo() {
    if (!frontendDemoMode && (runtimeStatus.id === "offline" || await isLiveRuntimeUnavailable())) {
      setResult(null);
      setVideoBatch(null);
      setError(LIVE_OFFLINE_MESSAGE);
      return;
    }
    if (!videoFile) {
      setError("Please upload a short product video before batch inspection.");
      return;
    }
    setLoading(true);
    setError("");
    setResult(null);
    setVideoBatch(null);
    try {
      const payload = await inspectVideo({
        file: videoFile,
        lineId,
        shift,
        modelRoute,
        samplingInterval: videoInterval,
        maxFrames,
        forceDemo: frontendDemoMode,
      });
      setVideoBatch(payload);
      setError("");
      refreshSystemData().catch((refreshError) => {
        console.error("VisionGuard refresh after video inspection failed", refreshError);
      });
    } catch (err) {
      console.error("VisionGuard video inspection failed", err);
      setError(sanitizeOperatorError(err?.message || err, "VisionGuard could not complete the batch inspection."));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page-shell inspection-page-shell">
      <section className={`inspection-hero-v2 inspection-hero-${tone} ${result ? "has-result" : ""}`}>
        <div>
          <p className="eyebrow">{action.eyebrow}</p>
          <h1>{action.title}</h1>
          <p>{action.copy}</p>
        </div>
        <div className="inspection-action-summary">
          <span className={`inspection-action-dot ${tone}`} />
          <div>
            <strong>{action.label}</strong>
            <p>{action.actionCopy}</p>
          </div>
        </div>
      </section>

      <div className="inspection-toolbar-v2">
        <div className="tab-row inspection-tab-row">
          <button className={`tab-button ${activeTab === "image" ? "is-active" : ""}`} onClick={() => setActiveTab("image")}>
            Image Inspection
          </button>
          <button className={`tab-button ${activeTab === "video" ? "is-active" : ""}`} onClick={() => setActiveTab("video")}>
            Video / Batch
          </button>
        </div>
        <div className="inspection-mode-row">
          <StatusBadge tone={inferenceBadgeTone}>{inferenceBadgeLabel}</StatusBadge>
          <button
            className="button button-secondary"
            onClick={() => setFrontendDemoMode((value) => !value)}
          >
            {frontendDemoMode ? "Disable local demo override" : "Enable local demo override"}
          </button>
        </div>
      </div>

      {activeTab === "image" ? (
        <>
          <section className="inspection-cockpit-grid">
            <article className="content-card inspection-intake-card">
              <div>
                <p className="eyebrow">1. Select frame</p>
                <h3>Choose a sample or upload any product image.</h3>
              </div>
              <label
                className={`dropzone dropzone-premium ${isImageDragging ? "is-dragging" : ""}`}
                onDragEnter={(event) => handleDragOver(event, setIsImageDragging)}
                onDragOver={(event) => handleDragOver(event, setIsImageDragging)}
                onDragLeave={(event) => handleDragLeave(event, setIsImageDragging)}
                onDrop={handleImageDrop}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*,.heic,.heif"
                  onClick={(event) => {
                    event.currentTarget.value = "";
                  }}
                  onChange={handleImageFileChange}
                />
                <span>{isImageDragging ? "Release to upload image" : "Drop product image here"}</span>
                <small>{imageFile ? `Selected file: ${imageFile.name}` : "Works best with clear product or factory camera frames."}</small>
              </label>

              <div className="sample-grid-v2">
                {samples.map((sample) => (
                  <button
                    key={sample.path}
                    className={`sample-card-v2 ${selectedSample?.path === sample.path ? "is-active" : ""}`}
                    onClick={() => handleSampleSelect(sample)}
                    type="button"
                  >
                    <span>{sample.label}</span>
                    <small>{sample.type}</small>
                  </button>
                ))}
              </div>

              <div className="form-grid inspection-form-grid">
                <label>
                  <span>Line ID</span>
                  <input value={lineId} onChange={(event) => setLineId(event.target.value)} />
                </label>
                <label>
                  <span>Shift</span>
                  <select value={shift} onChange={(event) => setShift(event.target.value)}>
                    <option value="morning">Morning</option>
                    <option value="afternoon">Afternoon</option>
                    <option value="night">Night</option>
                  </select>
                </label>
              </div>

              <div className="inspection-model-selector">
                <div className="inspection-model-selector-top">
                  <span>Inspection model</span>
                  <strong>
                    {modelRoute === "pcb_adapter_v1"
                      ? "PCB route"
                      : modelRoute === "nano_defects_eval"
                      ? "NanoDefects route"
                      : modelRoute === "factory_finetuned"
                      ? "Factory route"
                      : "Base route"}
                  </strong>
                </div>
                <label className="inspection-model-select-wrap">
                  <select
                    aria-label="Inspection model"
                    value={modelRoute}
                    onChange={(event) => setModelRoute(event.target.value)}
                  >
                    {inspectionModelOptions.map((option) => (
                      <option value={option.value} key={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </label>
                <div className="inspection-model-meta-row">
                  <span className="inspection-model-dot" aria-hidden="true" />
                  <p>{selectedModelOption.meta}</p>
                </div>
              </div>

              <button className="button button-primary inspection-run-button" onClick={handleInspectImage} disabled={loading}>
                {loading ? "Inspecting..." : runtimeStatus.id === "offline" && !frontendDemoMode ? "Run in Demo Mode or reconnect runtime" : "Run Inspection"}
              </button>
            </article>

            <section className="inspection-visual-stage">
              <article className="content-card inspection-stage-card">
                <div className="card-heading-row">
                  <div>
                    <p className="eyebrow">{evidence.eyebrow}</p>
                    <h3>{evidence.title}</h3>
                  </div>
                  <div className="inspection-stage-actions">
                    {result ? (
                      <>
                        <StatusBadge tone={tone}>
                          {isManualReview(result) ? "MANUAL_REVIEW_REQUIRED" : result.action || "PASS"}
                        </StatusBadge>
                        <a
                          className="button button-secondary inspection-download-button"
                          href={result.annotated_image}
                          download={`visionguard-${result.action || "inspection"}-${result.image_id || "annotated"}.png`}
                        >
                          Download image
                        </a>
                      </>
                    ) : null}
                  </div>
                </div>
                <div className="inspection-stage-image-shell">
                  <img
                    src={result?.annotated_image || imagePreview}
                    key={result?.image_id || imagePreview}
                    alt="Inspection overlay"
                    className="inspection-stage-image"
                  />
                </div>
                <div className={`inspection-evidence-note inspection-evidence-note-${tone}`}>
                  <strong>{result ? "Why this frame was classified this way" : "What will appear after inspection"}</strong>
                  <p>{evidenceSummary(result)}</p>
                </div>
                <div className="inspection-route-strip">
                  <span>Model route</span>
                  <strong>{result?.model_route_label || inspectionModelOptions.find((option) => option.value === modelRoute)?.label}</strong>
                  <small>
                    {result?.routing_metadata
                      ? `Active: ${result.routing_metadata.active_model} · Factory: ${result.routing_metadata.factory_id} · Product line: ${result.routing_metadata.product_line_id} · Fallback: ${result.routing_metadata.fallback_model || "none"}`
                      : "Selected route will be attached to the inspection event."}
                  </small>
                </div>
                <div className="inspection-source-strip">
                  <span>{result ? "Original frame" : "Selected frame"}</span>
                  <img src={imagePreview} alt="Uploaded source" />
                </div>
              </article>
            </section>

            <aside className="inspection-decision-rail">
              {loading ? <LoadingState title="Inspecting with Qwen-VL on AMD MI300X…" /> : null}
              {error ? (
                <ErrorState
                  message={error}
                  actionLabel={!frontendDemoMode && isEndpointUnavailableError(error) ? "Run in Demo Mode" : undefined}
                  onAction={() => setFrontendDemoMode(true)}
                />
              ) : null}
              {result ? (
                <InspectionResultCard
                  result={result}
                  onRerun={handleInspectImage}
                  onReset={resetInspectionState}
                />
              ) : (
                <article className="content-card inspection-empty-card">
                  <p className="eyebrow">2. Inspect</p>
                  <h3>Decision appears here.</h3>
                  <p className="report-text">
                    VisionGuard will return one release decision, the supporting evidence, the confidence context, and the next step for the operator.
                  </p>
                  <div className="inspection-empty-steps">
                    <span>Release approved</span>
                    <span>Manual review required</span>
                    <span>Stop line</span>
                  </div>
                </article>
              )}
            </aside>
          </section>

          {result ? <FactoryIntelligencePanel result={result} /> : (
            <section className="inspection-customer-value-grid">
              <article className="content-card">
                <p className="eyebrow">3. Explain</p>
                <h3>Factory intelligence after every scan</h3>
                <p className="report-text">After inspection, this area shows visual evidence, likely causes, recommended fix, and prevention steps.</p>
              </article>
              <article className="content-card">
                <p className="eyebrow">4. Log</p>
                <h3>Every decision updates reports</h3>
                <p className="report-text">The event log, operations alert, shift report, and AMD runtime metrics update after each check.</p>
              </article>
            </section>
          )}
        </>
      ) : (
        <section className="inspection-cockpit-grid inspection-video-grid">
          <article className="content-card inspection-intake-card">
            <div>
              <p className="eyebrow">Video / Batch inspection</p>
              <h3>Sample frames safely and inspect them sequentially.</h3>
            </div>
            <label
              className={`dropzone dropzone-premium ${isVideoDragging ? "is-dragging" : ""}`}
              onDragEnter={(event) => handleDragOver(event, setIsVideoDragging)}
              onDragOver={(event) => handleDragOver(event, setIsVideoDragging)}
              onDragLeave={(event) => handleDragLeave(event, setIsVideoDragging)}
              onDrop={handleVideoDrop}
            >
              <input
                type="file"
                accept="video/*"
                onChange={(event) => {
                  selectVideoFile(event.target.files?.[0]);
                }}
              />
              <span>{isVideoDragging ? "Release to upload video" : "Drop a short product video"}</span>
              <small>{videoFile ? `Selected file: ${videoFile.name}` : "No video selected yet."}</small>
            </label>
            <div className="form-grid inspection-form-grid">
              <label>
                <span>Inspection model</span>
                <select value={modelRoute} onChange={(event) => setModelRoute(event.target.value)}>
                  {inspectionModelOptions.map((option) => (
                    <option value={option.value} key={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                <span>Sampling interval</span>
                <input
                  type="number"
                  min="0.5"
                  step="0.5"
                  value={videoInterval}
                  onChange={(event) => setVideoInterval(Number(event.target.value))}
                />
              </label>
              <label>
                <span>Max frames</span>
                <input
                  type="number"
                  min="1"
                  max="20"
                  value={maxFrames}
                  onChange={(event) => setMaxFrames(Number(event.target.value))}
                />
              </label>
            </div>
            <button className="button button-primary inspection-run-button" onClick={handleInspectVideo} disabled={loading}>
              {loading ? "Inspecting..." : runtimeStatus.id === "offline" && !frontendDemoMode ? "Run in Demo Mode or reconnect runtime" : "Start Batch Inspection"}
            </button>
          </article>

          <div className="inspection-preview-stack inspection-batch-results">
            {loading ? <LoadingState title="Inspecting video frames on AMD MI300X…" /> : null}
            {error ? (
              <ErrorState
                message={error}
                actionLabel={!frontendDemoMode && isEndpointUnavailableError(error) ? "Run in Demo Mode" : undefined}
                onAction={() => setFrontendDemoMode(true)}
              />
            ) : null}
            {videoBatch ? (
              <>
                <article className="content-card">
                  <p className="eyebrow">Batch report</p>
                  <h3>Frame-level inspection summary</h3>
                  <p className="report-text">{videoBatch.batch_report}</p>
                </article>
                <article className="content-card content-card-alert">
                  <p className="eyebrow">Batch operations alert</p>
                  <h3>Operational recommendation</h3>
                  <p className="report-text">{videoBatch.operations_alert}</p>
                </article>
                <div className="table-shell">
                  <table className="event-table">
                    <thead>
                      <tr>
                        <th>Frame</th>
                        <th>Timestamp</th>
                        <th>Defect Category</th>
                        <th>Severity</th>
                        <th>Action</th>
                        <th>Confidence</th>
                      </tr>
                    </thead>
                    <tbody>
                      {videoBatch.frames.map((frame) => (
                        <tr key={frame.frame_id}>
                          <td>{frame.frame_id}</td>
                          <td>{frame.timestamp_seconds}s</td>
                          <td>{frame.defect_category}</td>
                          <td>{frame.severity}</td>
                          <td>{frame.action}</td>
                          <td>{Math.round((frame.confidence || 0) * 100)}%</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </>
            ) : (
              <article className="content-card inspection-empty-card">
                <p className="eyebrow">Optional demo path</p>
                <h3>Image inspection remains the primary flow.</h3>
                <p className="report-text">Use video only for short clips. The app samples frames and sends them sequentially to the same VisionGuard engine.</p>
              </article>
            )}
          </div>
        </section>
      )}
    </div>
  );
}
