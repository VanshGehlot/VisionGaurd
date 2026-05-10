export function getRuntimeStatus({
  health,
  metrics,
  frontendDemoMode = false,
  loading = false,
}) {
  const demoMode =
    frontendDemoMode ||
    health?.demo_mode ||
    metrics?.demo_mode ||
    health?.vllm_endpoint === "demo_mode" ||
    metrics?.endpoint_status === "demo_mode" ||
    health?.last_mode === "demo";
  const live =
    !demoMode &&
    (health?.vllm_reachable ||
      (metrics?.endpoint_status === "connected" && metrics?.vllm_reachable !== false) ||
      (health?.vllm_endpoint === "connected" && health?.vllm_reachable !== false));

  if (loading && !health && !metrics) {
    return {
      id: "checking",
      tone: "info",
      label: "Checking",
      badge: "Inference: Checking",
      description: "VisionGuard is checking whether the live AMD inference runtime is reachable.",
    };
  }

  if (demoMode) {
    return {
      id: "demo",
      tone: "warning",
      label: "Demo",
      badge: "Inference: Demo",
      description: "Demo responses are enabled. Do not treat these decisions as live plant output.",
    };
  }

  if (live) {
    return {
      id: "live",
      tone: "ok",
      label: "Live AMD",
      badge: "Inference: Live AMD",
      description: "The AMD MI300X runtime is reachable and serving inspection requests.",
    };
  }

  return {
    id: "offline",
    tone: "neutral",
    label: "Offline",
    badge: "Inference: Offline",
    description: "The live AMD runtime is unavailable. Inspections will need demo mode or runtime recovery.",
  };
}

export function getDataStatus({
  serviceStatus,
  loading = false,
}) {
  const values = Object.values(serviceStatus || {});
  const okCount = values.filter((value) => value === "ok").length;
  const errorCount = values.filter((value) => value === "error").length;

  if (loading && okCount === 0 && errorCount === 0) {
    return {
      id: "loading",
      tone: "info",
      label: "Loading",
      badge: "System data: Loading",
      description: "VisionGuard is loading live quality, event, and reporting data.",
    };
  }

  if (okCount > 0 && errorCount > 0) {
    return {
      id: "partial",
      tone: "warning",
      label: "Partial",
      badge: "System data: Partial",
      description: "Some live system panels are unavailable. Data shown below may be incomplete.",
    };
  }

  if (okCount === 0 && errorCount > 0) {
    return {
      id: "unavailable",
      tone: "critical",
      label: "Unavailable",
      badge: "System data: Unavailable",
      description: "VisionGuard could not load live system data. The UI is in a degraded state.",
    };
  }

  return {
    id: "live",
    tone: "ok",
    label: "Live",
    badge: "System data: Live",
    description: "Quality data, event history, and reporting signals are available.",
  };
}

export function formatDecisionLabel(action) {
  const normalized = String(action || "PASS").toUpperCase();
  if (normalized === "STOP_LINE") return "Stop line";
  if (normalized === "ALERT_OPERATOR") return "Manual review required";
  if (normalized === "LOG_WARNING") return "Warning logged";
  return "Release approved";
}

export function formatSeverityLabel(severity) {
  const normalized = String(severity || "ok").toLowerCase();
  if (normalized === "critical") return "Critical";
  if (normalized === "warning") return "Warning";
  return "Clear";
}

export function formatConfidence(value) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return "N/A";
  return `${Math.round(numeric * 100)}%`;
}

export function formatTimestamp(value) {
  if (!value) return "No timestamp";
  return String(value).replace("T", " ").slice(0, 19);
}

export function truncateIdentifier(value, visible = 8) {
  const stringValue = String(value || "");
  if (!stringValue) return "—";
  if (stringValue.length <= visible * 2 + 1) return stringValue;
  return `${stringValue.slice(0, visible)}...${stringValue.slice(-visible)}`;
}

export function sanitizeOperatorError(message, fallback = "VisionGuard could not complete the request.") {
  const copy = String(message || "").toLowerCase();

  if (
    copy.includes("inference endpoint unavailable") ||
    copy.includes("localhost:8000") ||
    copy.includes("connection refused") ||
    copy.includes("pool") ||
    copy.includes("503")
  ) {
    return "Live AMD inference is unavailable. Reconnect the runtime endpoint or switch to demo mode.";
  }

  if (
    copy.includes("valid image") ||
    copy.includes("parsed as an image") ||
    copy.includes("could not be opened as an image")
  ) {
    return "This file could not be read as a product image. Upload a clear PNG, JPEG, WEBP, or TIFF frame.";
  }

  if (copy.includes("video")) {
    return "VisionGuard could not process this video. Upload a shorter supported clip and try again.";
  }

  if (copy.includes("failed to fetch") || copy.includes("network")) {
    return "VisionGuard could not reach the inspection service. Check the API connection and try again.";
  }

  return fallback;
}
