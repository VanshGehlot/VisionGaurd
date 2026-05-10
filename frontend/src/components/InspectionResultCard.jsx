import StatusBadge from "./StatusBadge";

function severityTone(severity, detected) {
  if (!detected) return "ok";
  if (severity === "critical") return "critical";
  if (severity === "warning") return "warning";
  return "neutral";
}

function isOperatorReview(result) {
  return (
    result?.action === "ALERT_OPERATOR" &&
    !result?.defect_detected
  );
}

function decisionPresentation(result) {
  const detected = Boolean(result?.defect_detected);
  const reviewOnly = isOperatorReview(result);
  const tone = reviewOnly ? "warning" : severityTone(result?.severity, detected);

  if (result?.action === "STOP_LINE" || result?.severity === "critical") {
    return {
      tone,
      badgeLabel: "STOP_LINE",
      title: "Stop line required",
      summary:
        result?.factory_owner_summary ||
        "A likely critical defect was detected. Hold the item, inspect adjacent units, and verify the upstream process immediately.",
      primaryAction: "Inspect another frame",
      secondaryAction: "Clear result",
    };
  }

  if (reviewOnly) {
    return {
      tone,
      badgeLabel: "MANUAL_REVIEW_REQUIRED",
      title: "Manual review required",
      summary:
        "No visible defect was confirmed strongly enough for automatic release. This item should be reviewed by an operator before it moves forward.",
      primaryAction: "Re-run same frame",
      secondaryAction: "Inspect another frame",
    };
  }

  if (detected) {
    return {
      tone,
      badgeLabel: "WARNING",
      title: "Defect detected",
      summary:
        result?.factory_owner_summary ||
        result?.visual_explanation ||
        "A likely defect was detected. Review the evidence and route the item according to plant policy.",
      primaryAction: "Inspect another frame",
      secondaryAction: "Clear result",
    };
  }

  return {
    tone,
    badgeLabel: "RELEASE_APPROVED",
    title: "Release approved",
    summary:
      result?.factory_owner_summary ||
      "No visible defect was confirmed, and the frame met the threshold for automatic release.",
    primaryAction: "Scan next product",
    secondaryAction: "Re-run same frame",
  };
}

function confidenceLabel(result) {
  if (isOperatorReview(result)) return "Auto-release confidence";
  return "Decision confidence";
}

function classificationLabel(result) {
  if (!result?.defect_detected) return "No defect confirmed";
  return result?.defect_category || result?.defect_type || "Defect detected";
}

function regionLabel(result) {
  if (isOperatorReview(result)) return "No defect region confirmed";
  return result?.location || "Region not provided";
}

function systemActionLabel(result) {
  if (isOperatorReview(result)) return "Hold for manual review";
  if (result?.action === "STOP_LINE") return "Stop line and contain batch";
  if (result?.action === "ALERT_OPERATOR" || result?.action === "LOG_WARNING") {
    return "Send to manual review";
  }
  return "Release to production";
}

export default function InspectionResultCard({ result, onRerun, onReset }) {
  const detected = Boolean(result?.defect_detected);
  const reviewOnly = isOperatorReview(result);
  const decision = decisionPresentation(result);

  return (
    <article className={`content-card result-card result-card-${decision.tone}`}>
      <div className="result-card-hero">
        <div>
          <p className="eyebrow">Inspection verdict</p>
          <h3 className="result-card-title">{decision.title}</h3>
          <p className="result-card-summary">{decision.summary}</p>
        </div>
        <div className="result-card-badge-stack">
          <StatusBadge tone={decision.tone}>{decision.badgeLabel}</StatusBadge>
          <div className="result-action-chip">{systemActionLabel(result)}</div>
        </div>
      </div>
      <div className="result-card-cta-row">
        <button className="button button-primary result-card-button" onClick={onRerun} type="button">
          {decision.primaryAction}
        </button>
        <button className="button button-secondary result-card-button" onClick={onReset} type="button">
          {decision.secondaryAction}
        </button>
      </div>
      <div className="detail-grid">
        <div>
          <span className="detail-label">Classification</span>
          <strong>{classificationLabel(result)}</strong>
        </div>
        <div>
          <span className="detail-label">System action</span>
          <strong>{systemActionLabel(result)}</strong>
        </div>
        <div>
          <span className="detail-label">Severity</span>
          <strong>{reviewOnly ? "review required" : result?.severity || "ok"}</strong>
        </div>
        <div>
          <span className="detail-label">{confidenceLabel(result)}</span>
          <strong>{Math.round((Number(result?.confidence) || 0) * 100)}%</strong>
        </div>
        <div>
          <span className="detail-label">Evidence region</span>
          <strong>{regionLabel(result)}</strong>
        </div>
        <div>
          <span className="detail-label">Latency</span>
          <strong>{result?.processing_ms || 0}ms</strong>
        </div>
        <div>
          <span className="detail-label">Model</span>
          <strong>{result?.model_name || "Qwen/Qwen2.5-VL-7B-Instruct"}</strong>
        </div>
        <div>
          <span className="detail-label">Original classifier action</span>
          <strong>{result?.action || (detected ? "ALERT_OPERATOR" : "PASS")}</strong>
        </div>
      </div>
      <div className="runtime-note">{result?.runtime || "AMD MI300X · ROCm · vLLM"}</div>
    </article>
  );
}
