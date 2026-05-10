import { useEffect, useMemo, useState } from "react";
import StatusBadge from "../components/StatusBadge";
import {
  analyzeAdaptationDataset,
  getAdaptationBaselineEvaluation,
  getAdaptationDatasets,
  getAdaptationFeedback,
  getAdaptationModelRegistry,
  getAdaptationOverview,
  getAdaptationRouting,
  getAdaptationTrainingJobs,
  submitAdaptationFeedback,
} from "../lib/api";
import { sanitizeOperatorError } from "../lib/ui";

const demoDraft = {
  dataset_url: "https://github.com/tangsanli5201/DeepPCB",
  existing_model_link: "",
  product_type: "Printed circuit board",
  factory_name: "Precision Circuits Demo Plant",
  line_id: "PCB-A1",
  camera_conditions: "Fixed overhead camera, controlled lighting, aligned board fixture",
  defect_classes: "open circuit, short, mousebite, spur, pin hole, missing copper",
  severity_rules: "Open/short/missing copper defects stop line. Pin holes and spurs alert operator.",
};

const nanoDraft = {
  dataset_url: "data/nano_defects/labels.json",
  existing_model_link: "",
  product_type: "Steel bottle / thermos / food jar",
  factory_name: "NanoDefects Bottle Manufacturing Line",
  line_id: "NANO-A1",
  camera_conditions: "Handheld factory QA images today; fixed camera and controlled lighting recommended next.",
  defect_classes:
    "small_dent, impact_pit, broad_shallow_dent, reflection_deformation, creased_dent, scratch_scuff, coating_damage, internal_dent, base_region_defect, shoulder_deformation, rim_thread_defect, unknown_defect, clean",
  severity_rules:
    "Clean products pass. Visible dents, coating damage, base defects, or uncertain reflections alert operator. Major deformation or leakage/structural risk rejects or stops line.",
};

const workflowSteps = [
  ["Setup factory profile", "complete"],
  ["Attach dataset", "active"],
  ["Define release policy", "active"],
  ["Analyze readiness", "pending"],
  ["Route the model", "pending"],
];

const analysisStages = [
  "Validating dataset source",
  "Checking defect taxonomy",
  "Estimating LoRA adapter path",
  "Calculating deployment route",
];

const creationOptions = [
  { id: "base", label: "Base model" },
  { id: "pcb", label: "PCB / DeepPCB" },
  { id: "nano", label: "NanoDefects Evaluation" },
  { id: "bottle", label: "Bottle line" },
  { id: "custom", label: "Custom product" },
];

function percent(value) {
  if (value === null || value === undefined || value === "") return "-";
  return `${Math.round(Number(value) * 100)}%`;
}

function statusTone(status) {
  const normalized = String(status || "").toLowerCase();
  if (normalized.includes("deploy") || normalized.includes("active") || normalized.includes("complete")) return "ok";
  if (normalized.includes("queue") || normalized.includes("planned")) return "warning";
  return "neutral";
}

function RegistryTable({ models }) {
  return (
    <div className="adaptation-table-wrap">
      <table className="adaptation-table">
        <thead>
          <tr>
            <th>Model</th>
            <th>Factory</th>
            <th>Product line</th>
            <th>Adapter</th>
            <th>Dataset</th>
            <th>Score</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {models.map((model) => (
            <tr key={model.id}>
              <td>
                <strong>{model.model_name}</strong>
                <span>{model.base_model}</span>
              </td>
              <td>{model.factory_id}</td>
              <td>{model.product_line_id}</td>
              <td>{model.adapter_type}</td>
              <td>{model.dataset_version}</td>
              <td>{model.validation_score ? percent(model.validation_score) : "Planned"}</td>
              <td>
                <StatusBadge tone={statusTone(model.deployment_status)} compact>
                  {model.deployment_status}
                </StatusBadge>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function AdaptationPage() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [feedbackStatus, setFeedbackStatus] = useState("");
  const [selectedCreation, setSelectedCreation] = useState("pcb");
  const [datasetFileName, setDatasetFileName] = useState("");
  const [analysis, setAnalysis] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisStageIndex, setAnalysisStageIndex] = useState(0);
  const [technicalOpen, setTechnicalOpen] = useState(false);
  const [draft, setDraft] = useState(demoDraft);

  async function loadAdaptationData() {
    try {
      const [overview, datasets, baseline, jobs, registry, routing, feedback] = await Promise.all([
        getAdaptationOverview(),
        getAdaptationDatasets(),
        getAdaptationBaselineEvaluation(),
        getAdaptationTrainingJobs(),
        getAdaptationModelRegistry(),
        getAdaptationRouting(),
        getAdaptationFeedback(),
      ]);
      setData({
        overview,
        datasets: datasets.datasets || [],
        baseline: baseline.evaluation,
        jobs: jobs.training_jobs || [],
        registry: registry.models || [],
        routing: routing.routing,
        feedback: feedback.feedback,
      });
      setError("");
    } catch (err) {
      setError("Factory adaptation data is unavailable right now. The guided rollout view cannot be loaded.");
    }
  }

  useEffect(() => {
    loadAdaptationData();
  }, []);

  const activeDataset = data?.datasets?.[0];
  const latestJob = data?.jobs?.[0];
  const feedbackItems = data?.feedback?.items || [];
  const classes = activeDataset?.defect_classes || data?.overview?.factory?.target_defects || [];
  const completedSteps = analyzing
    ? workflowSteps.map(([label]) => [
        label,
        label === "Readiness analysis" ? "active" : label === "Deploy adapter" ? "pending" : "complete",
      ])
    : analysis
    ? workflowSteps.map(([label]) => [label, label === "Deploy adapter" ? "active" : "complete"])
    : workflowSteps;

  const metricStory = useMemo(() => {
    if (!data?.baseline || !data?.routing?.active_model) return null;
    return {
      base: percent(data.baseline.metrics.accuracy),
      adapter: percent(data.routing.active_model.validation_score),
      falsePass: data.overview?.kpis?.false_pass_reduction || "14% → 4%",
      classes: classes.length,
    };
  }, [classes.length, data]);
  const analysisRouteLabel = selectedCreation === "nano" ? "NanoDefects Bottle QA — Evaluation Route" : "PCB Adapter v1";
  const analysisRouteHref = selectedCreation === "nano" ? "/inspection?model=nano_defects_eval" : "/inspection?model=pcb_adapter_v1";

  function updateDraft(key, value) {
    setDraft((current) => ({ ...current, [key]: value }));
  }

  function selectCreation(optionId) {
    setSelectedCreation(optionId);
    if (optionId === "nano") {
      setDatasetFileName("");
      setDraft(nanoDraft);
    }
    if (optionId === "pcb") {
      setDatasetFileName("");
      setDraft(demoDraft);
    }
  }

  function useDeepPcbDemo() {
    setSelectedCreation("pcb");
    setDatasetFileName("");
    setDraft(demoDraft);
  }

  async function analyzeDatasetReadiness() {
    setAnalyzing(true);
    setAnalysis(null);
    setAnalysisStageIndex(0);
    setFeedbackStatus("");
    const stageTimer = window.setInterval(() => {
      setAnalysisStageIndex((current) => Math.min(current + 1, analysisStages.length - 1));
    }, 760);
    try {
      const [payload] = await Promise.all([
        analyzeAdaptationDataset({
          ...draft,
          selected_creation_type: selectedCreation,
          dataset_file_name: datasetFileName,
        }),
        new Promise((resolve) => window.setTimeout(resolve, 3200)),
      ]);
      setAnalysis(payload);
    } catch (err) {
      setFeedbackStatus(sanitizeOperatorError(err?.message || err, "Dataset readiness analysis could not be completed."));
    } finally {
      window.clearInterval(stageTimer);
      setAnalyzing(false);
    }
  }

  async function submitSampleFeedback() {
    setFeedbackStatus("Saving operator correction...");
    try {
      await submitAdaptationFeedback({
        factory_id: "pcb_demo_plant",
        product_line_id: "pcb_line_a",
        image_ref: "operator/live_review_case",
        predicted_verdict: "PASS",
        corrected_verdict: "ALERT_OPERATOR",
        predicted_defect_type: "none",
        corrected_defect_type: "mousebite",
        notes: "Demo correction captured for the next DeepPCB adapter dataset version.",
      });
      await loadAdaptationData();
      setFeedbackStatus("Feedback saved to next-training queue.");
    } catch (err) {
      setFeedbackStatus("The correction could not be saved right now. Try again after the adaptation service recovers.");
    }
  }

  if (error) {
    return (
      <div className="page-shell adaptation-page-shell">
        <article className="content-card">
          <p className="eyebrow">Factory Adaptation Studio</p>
          <h2>Adaptation data unavailable</h2>
          <p className="report-text">{error}</p>
          <button className="button button-primary" onClick={loadAdaptationData} type="button">
            Retry
          </button>
        </article>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="page-shell adaptation-page-shell">
        <section className="adaptation-one-screen loading">
          <p className="eyebrow">Factory Adaptation Studio</p>
          <h1>Loading factory adaptation workflow...</h1>
        </section>
      </div>
    );
  }

  return (
    <div className="page-shell adaptation-page-shell adaptation-one-screen-shell">
      <section className="adaptation-command-header">
        <div>
          <p className="eyebrow">Factory Adaptation Studio</p>
          <h1>Guide a factory dataset into a production inspection route.</h1>
          <p>Use the guided rollout path to define the plant profile, analyze dataset readiness, and decide whether the factory should stay on the base route or move to an adapted model.</p>
        </div>
        <div className="adaptation-header-actions">
          <StatusBadge tone="ok">Active route: {data.routing.active_model.name}</StatusBadge>
          <button className="button button-secondary" type="button" onClick={() => setTechnicalOpen(true)}>
            Open advanced details
          </button>
        </div>
      </section>

      <section className="adaptation-one-screen">
        <aside className="adaptation-workflow-rail">
          <p className="eyebrow">Workflow</p>
          {completedSteps.map(([label, status], index) => (
            <div className={`adaptation-workflow-step ${status}`} key={label}>
              <span>{index + 1}</span>
              <div>
                <strong>{label}</strong>
                <small>{status}</small>
              </div>
            </div>
          ))}
        </aside>

        <article className="content-card adaptation-action-panel">
          <div className="adaptation-panel-heading">
            <p className="eyebrow">Guided rollout</p>
            <h2>Create a factory-specific inspection route</h2>
          </div>

          <div className="adaptation-use-case-row">
            {creationOptions.map((option) => (
              <button
                key={option.id}
                className={`adaptation-use-case-chip ${selectedCreation === option.id ? "is-active" : ""}`}
                type="button"
                onClick={() => selectCreation(option.id)}
              >
                {option.label}
              </button>
            ))}
          </div>
          {selectedCreation === "nano" ? (
            <p className="adaptation-route-note">
              NanoDefects raw-image evaluation is challenging because real steel-bottle defects are subtle and reflection-based. Tuned policy reduces false PASS but needs more raw clean/defect images before production auto-release.
            </p>
          ) : null}

          <div className="adaptation-compact-form">
            <label>
              <span>Factory name</span>
              <input value={draft.factory_name} onChange={(event) => updateDraft("factory_name", event.target.value)} />
            </label>
            <label>
              <span>Product type</span>
              <input value={draft.product_type} onChange={(event) => updateDraft("product_type", event.target.value)} />
            </label>
            <label className="wide">
              <span>Dataset source</span>
              <div className="adaptation-source-row">
                <input value={draft.dataset_url} onChange={(event) => updateDraft("dataset_url", event.target.value)} />
                <label className="adaptation-file-pill">
                  Attach
                  <input
                    type="file"
                    accept=".zip,.json,.csv,.txt,image/*"
                    onChange={(event) => setDatasetFileName(event.target.files?.[0]?.name || "")}
                  />
                </label>
              </div>
              <small>{datasetFileName || "DeepPCB demo dataset is loaded."}</small>
            </label>
            <label className="wide">
              <span>Existing model reference</span>
              <input
                placeholder="Optional Hugging Face / registry link"
                value={draft.existing_model_link}
                onChange={(event) => updateDraft("existing_model_link", event.target.value)}
              />
            </label>
            <label className="wide">
              <span>Target defect classes</span>
              <textarea value={draft.defect_classes} onChange={(event) => updateDraft("defect_classes", event.target.value)} />
            </label>
            <label className="wide">
              <span>Release and escalation rules</span>
              <textarea value={draft.severity_rules} onChange={(event) => updateDraft("severity_rules", event.target.value)} />
            </label>
          </div>

          <div className="adaptation-action-row">
            <button className="button button-secondary" type="button" onClick={useDeepPcbDemo} disabled={analyzing}>
              Use DeepPCB Demo
            </button>
            <button
              className="button button-primary adaptation-primary-cta"
              type="button"
              onClick={analyzeDatasetReadiness}
              disabled={analyzing}
            >
              {analyzing ? "Analyzing dataset..." : "Analyze readiness"}
            </button>
          </div>
        </article>

        <aside className={`content-card adaptation-outcome-panel ${analysis ? "has-analysis" : ""} ${analyzing ? "is-analyzing" : ""}`}>
          <p className="eyebrow">Outcome</p>
          <h2>{analyzing ? analysisStages[analysisStageIndex] : analysis ? "Readiness review complete" : "Waiting for readiness analysis"}</h2>
          {analyzing ? (
            <div className="adaptation-analysis-progress" role="status" aria-live="polite">
              <span className="adaptation-spinner" />
              <div>
                <strong>Analyzing dataset...</strong>
                <p>{analysisStages[analysisStageIndex]}</p>
              </div>
            </div>
          ) : null}
          <div className="adaptation-outcome-list">
            <div><span>Recommended rollout</span><strong>{analysis ? "Adapter fine-tuning" : analyzing ? "Analyzing" : "Waiting"}</strong></div>
            <div><span>Training estimate</span><strong>{analysis ? "38–55 minutes on AMD MI300X" : analyzing ? "Calculating" : "Waiting"}</strong></div>
            <div><span>Expected gain</span><strong>{analysis ? "8–13 quality points" : analyzing ? "Estimating" : "Waiting"}</strong></div>
            <div><span>Risk</span><strong>{analysis ? "Low" : analyzing ? "Checking" : "Waiting"}</strong></div>
            <div><span>Inspection route</span><strong>{analysis ? analysisRouteLabel : data.routing.active_model.name}</strong></div>
          </div>
          <div className="adaptation-metric-story">
            <div>
              <span>Accuracy</span>
              <strong>{metricStory.base}{" → "}{metricStory.adapter}</strong>
            </div>
            <div>
              <span>False PASS</span>
              <strong>{metricStory.falsePass}</strong>
            </div>
            <div>
              <span>Classes</span>
              <strong>{metricStory.classes}</strong>
            </div>
          </div>
          {analysis ? (
            <div className="adaptation-outcome-actions">
              <button className="button button-secondary" type="button" onClick={() => setTechnicalOpen(true)}>
                Review advanced details
              </button>
              <a className="button button-primary" href={analysisRouteHref}>
                Open inspection route
              </a>
            </div>
          ) : (
            <p className="report-text">Run readiness analysis to estimate rollout risk, training effort, and the recommended inspection route.</p>
          )}
        </aside>
      </section>

      {technicalOpen ? (
        <div className="adaptation-details-overlay" role="dialog" aria-modal="true">
          <div className="adaptation-details-drawer">
            <div className="card-heading-row">
              <div>
                <p className="eyebrow">Technical details</p>
                <h2>Advanced adaptation details</h2>
              </div>
              <button className="button button-secondary" type="button" onClick={() => setTechnicalOpen(false)}>
                Close
              </button>
            </div>
            <p className="adaptation-truth-note drawer-note">
              This drawer shows the deeper registry and feedback details behind the guided rollout. It is supporting context, not the primary operator workflow.
            </p>
            <div className="adaptation-details-grid">
              <article>
                <p className="eyebrow">Dataset</p>
                <h3>{activeDataset.name} · {activeDataset.version}</h3>
                <p>{activeDataset.sample_count} samples · {activeDataset.train_count} train · {activeDataset.validation_count} validation</p>
                <div className="taxonomy-chip-grid">
                  {classes.map((item) => <span key={item}>{item}</span>)}
                </div>
              </article>
              <article>
                <p className="eyebrow">Training job</p>
                <h3>{latestJob.output_model_version}</h3>
                <p>{latestJob.training_method} · {latestJob.status} · validation {percent(latestJob.metrics.validation_accuracy)}</p>
                <button className="button button-secondary" type="button" onClick={submitSampleFeedback}>
                  Add demo correction
                </button>
                {feedbackStatus ? <p className="adaptation-feedback-status">{feedbackStatus}</p> : null}
              </article>
              <article>
                <p className="eyebrow">Feedback queue</p>
                <h3>{data.feedback.total} corrections</h3>
                <p>{data.feedback.queued} queued · {data.feedback.included_next_training} included in next training</p>
                <div className="feedback-list compact">
                  {feedbackItems.slice(0, 3).map((item) => (
                    <div key={item.id}>
                      <strong>{item.corrected_verdict}</strong>
                      <span>{item.corrected_defect_type} · {item.status}</span>
                    </div>
                  ))}
                </div>
              </article>
            </div>
            <RegistryTable models={data.registry} />
          </div>
        </div>
      ) : null}
    </div>
  );
}
