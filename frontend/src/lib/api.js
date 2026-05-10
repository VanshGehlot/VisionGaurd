const JSON_HEADERS = {
  Accept: "application/json",
};

async function unwrap(responsePromise) {
  const response = await responsePromise;
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const payload = await response.json();
      detail = payload.detail || payload.message || detail;
    } catch {
      // ignore parse errors
    }
    throw new Error(detail);
  }
  return response.json();
}

export async function getHealth() {
  return unwrap(fetch("/health", { headers: JSON_HEADERS }));
}

export async function getMetrics() {
  return unwrap(fetch("/metrics", { headers: JSON_HEADERS }));
}

export async function getEvents(limit = 12) {
  return unwrap(fetch(`/events?limit=${limit}`, { headers: JSON_HEADERS }));
}

export async function getReport() {
  return unwrap(fetch("/report", { headers: JSON_HEADERS }));
}

export async function getOperationsAlert() {
  return unwrap(fetch("/operations-alert", { headers: JSON_HEADERS }));
}

export async function getAdaptationOverview() {
  return unwrap(fetch("/adaptation/overview", { headers: JSON_HEADERS }));
}

export async function getAdaptationDatasets() {
  return unwrap(fetch("/adaptation/datasets", { headers: JSON_HEADERS }));
}

export async function getAdaptationBaselineEvaluation() {
  return unwrap(fetch("/adaptation/baseline-evaluation", { headers: JSON_HEADERS }));
}

export async function getAdaptationTrainingJobs() {
  return unwrap(fetch("/adaptation/training-jobs", { headers: JSON_HEADERS }));
}

export async function getAdaptationModelRegistry() {
  return unwrap(fetch("/adaptation/model-registry", { headers: JSON_HEADERS }));
}

export async function getAdaptationModelOptions() {
  return unwrap(fetch("/adaptation/model-options", { headers: JSON_HEADERS }));
}

export async function getAdaptationRouting() {
  return unwrap(fetch("/adaptation/routing", { headers: JSON_HEADERS }));
}

export async function getAdaptationFeedback() {
  return unwrap(fetch("/adaptation/feedback", { headers: JSON_HEADERS }));
}

export async function submitAdaptationFeedback(payload) {
  return unwrap(
    fetch("/adaptation/feedback", {
      method: "POST",
      headers: {
        ...JSON_HEADERS,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    })
  );
}

export async function analyzeAdaptationDataset(payload) {
  return unwrap(
    fetch("/adaptation/analyze-dataset", {
      method: "POST",
      headers: {
        ...JSON_HEADERS,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    })
  );
}

export async function deployAdaptationModel(modelId) {
  return unwrap(
    fetch("/adaptation/deploy-model", {
      method: "POST",
      headers: {
        ...JSON_HEADERS,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ model_id: modelId }),
    })
  );
}

export async function inspectImage({
  file,
  lineId,
  shift,
  modelRoute,
  forceDemo = false,
}) {
  const formData = new FormData();
  formData.append("image", file);
  if (lineId) formData.append("line_id", lineId);
  if (shift) formData.append("shift", shift);
  if (modelRoute) formData.append("model_route", modelRoute);

  const suffix = forceDemo ? "?force_demo=true" : "";
  return unwrap(
    fetch(`/inspect-image${suffix}`, {
      method: "POST",
      body: formData,
    })
  );
}

export async function inspectVideo({
  file,
  lineId,
  shift,
  modelRoute,
  samplingInterval,
  maxFrames,
  forceDemo = false,
}) {
  const formData = new FormData();
  formData.append("video", file);
  if (lineId) formData.append("line_id", lineId);
  if (shift) formData.append("shift", shift);
  if (modelRoute) formData.append("model_route", modelRoute);
  formData.append("sampling_interval", String(samplingInterval));
  formData.append("max_frames", String(maxFrames));

  const suffix = forceDemo ? "?force_demo=true" : "";
  return unwrap(
    fetch(`/inspect-video${suffix}`, {
      method: "POST",
      body: formData,
    })
  );
}

export async function fetchExampleAsFile(path, nameHint = "sample.jpg") {
  const response = await fetch(path);
  if (!response.ok) {
    throw new Error(`Failed to load example image from ${path}`);
  }
  const blob = await response.blob();
  return new File([blob], nameHint, { type: blob.type || "image/jpeg" });
}
