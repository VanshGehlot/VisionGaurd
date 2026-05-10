import MetricCard from "../components/MetricCard";
import StatusBadge from "../components/StatusBadge";
import SystemBanner from "../components/SystemBanner";
import { useAppContext } from "../state/AppContext";
import { getDataStatus, getRuntimeStatus } from "../lib/ui";

export default function SettingsPage() {
  const {
    frontendDemoMode,
    setFrontendDemoMode,
    health,
    metrics,
    loading,
    error,
    serviceStatus,
    lastUpdated,
    refreshSystemData,
  } = useAppContext();
  const runtimeStatus = getRuntimeStatus({ health, metrics, frontendDemoMode, loading });
  const dataStatus = getDataStatus({ serviceStatus, loading });

  return (
    <div className="page-shell">
      {(error || runtimeStatus.id !== "live") ? (
        <SystemBanner
          tone={error ? dataStatus.tone : runtimeStatus.tone}
          title={error ? dataStatus.badge : runtimeStatus.badge}
          body={error || runtimeStatus.description}
          actionLabel="Refresh status"
          onAction={() => refreshSystemData()}
        />
      ) : null}
      <div className="page-heading">
        <p className="eyebrow">Settings and system truth</p>
        <h1 className="page-title">Configured defaults, live runtime status, and explicit demo controls.</h1>
        <div className="page-heading-meta">
          <StatusBadge tone={runtimeStatus.tone}>{runtimeStatus.badge}</StatusBadge>
          <StatusBadge tone={dataStatus.tone}>{dataStatus.badge}</StatusBadge>
          {lastUpdated ? <StatusBadge tone="info">Last sync available</StatusBadge> : null}
        </div>
      </div>

      <div className="settings-summary-row">
        <MetricCard label="Runtime" value={metrics?.runtime || "AMD MI300X · ROCm · vLLM"} meta="Primary inference substrate" />
        <MetricCard label="Model" value={metrics?.model_name || "Qwen/Qwen2.5-VL-7B-Instruct"} meta="Active multimodal model" />
        <MetricCard label="Inference state" value={runtimeStatus.label} meta="Current runtime reachability" />
      </div>

      <div className="settings-grid">
        <article className="content-card">
          <div className="card-heading-row">
            <div>
              <p className="eyebrow">Configured plant profile</p>
              <h3>Default demo values used by the frontend</h3>
            </div>
          </div>
          <div className="settings-facts-grid">
            <div className="settings-fact-card">
              <span>Factory</span>
              <strong>VisionGuard Demo Plant</strong>
            </div>
            <div className="settings-fact-card">
              <span>Product type</span>
              <strong>Bottle</strong>
            </div>
            <div className="settings-fact-card">
              <span>Default line</span>
              <strong>LINE-A1</strong>
            </div>
            <div className="settings-fact-card">
              <span>Default shift</span>
              <strong>Morning</strong>
            </div>
          </div>
          <p className="report-text">These values are currently configured defaults, not live PLC or MES reads.</p>
        </article>

        <article className="content-card">
          <div className="card-heading-row">
            <div>
              <p className="eyebrow">Runtime truth</p>
              <h3>What the system can confirm right now</h3>
            </div>
          </div>
          <div className="settings-stack">
            <div className="settings-row">
              <span>Inference runtime</span>
              <StatusBadge tone={runtimeStatus.tone}>{runtimeStatus.badge}</StatusBadge>
            </div>
            <div className="settings-row">
              <span>System data</span>
              <StatusBadge tone={dataStatus.tone}>{dataStatus.badge}</StatusBadge>
            </div>
            <div className="settings-row">
              <span>Model route</span>
              <strong>{metrics?.model_name || "Qwen/Qwen2.5-VL-7B-Instruct"}</strong>
            </div>
            <div className="settings-row">
              <span>Runtime</span>
              <strong>{metrics?.runtime || "AMD MI300X · ROCm · vLLM"}</strong>
            </div>
          </div>
        </article>

        <article className="content-card">
          <div className="card-heading-row">
            <div>
              <p className="eyebrow">Demo controls</p>
              <h3>Frontend behavior when live inference is unavailable</h3>
            </div>
          </div>
          <div className="settings-stack">
            <div className="settings-row">
              <span>Frontend demo override</span>
              <StatusBadge tone={frontendDemoMode ? "warning" : "neutral"}>
                {frontendDemoMode ? "Forced demo enabled" : "Forced demo disabled"}
              </StatusBadge>
            </div>
            <div className="settings-row">
              <span>Action</span>
              <button
                className="button button-secondary"
                onClick={() => setFrontendDemoMode((value) => !value)}
              >
                {frontendDemoMode ? "Disable Demo Mode" : "Enable Demo Mode"}
              </button>
            </div>
            <p className="report-text">
              Demo mode should stay visibly distinct from live inference so operators do not mistake simulated outcomes for plant truth.
            </p>
          </div>
        </article>

        <article className="content-card">
          <p className="eyebrow">Operational governance</p>
          <h3>What this build is optimized for today</h3>
          <p className="report-text">
            VisionGuard is currently optimized for a reliable inspection demo loop with
            explicit status visibility, local event logging, and shift-level review surfaces.
          </p>
          <ul className="clean-list clean-list-tight settings-bullet-list">
            <li>Primary workflow is single-frame inspection with optional batch review.</li>
            <li>SQLite remains the local event source so the product does not depend on analytics middleware to function.</li>
            <li>Demo mode stays explicit and visible so simulated results are never shown as live AMD inference.</li>
          </ul>
        </article>

        <article className="content-card">
          <p className="eyebrow">Connection status</p>
          <h3>System components that the UI can currently verify</h3>
          <p className="report-text">
            These are the runtime states the frontend can verify from current API responses. Anything not confirmed here should not be treated as live plant truth.
          </p>
          <div className="settings-status-grid">
            <div className="settings-status-card">
              <span>Inspection API</span>
              <strong>{serviceStatus.health === "ok" ? "Reachable" : "Unavailable"}</strong>
            </div>
            <div className="settings-status-card">
              <span>Event stream</span>
              <strong>{serviceStatus.events === "ok" ? "Reachable" : "Unavailable"}</strong>
            </div>
            <div className="settings-status-card">
              <span>Live AMD runtime</span>
              <strong>{runtimeStatus.label}</strong>
            </div>
          </div>
        </article>
      </div>

      <article className="content-card settings-architecture-card">
        <div className="card-heading-row">
          <div>
            <p className="eyebrow">Architecture / system status</p>
            <h3>How VisionGuard is wired today</h3>
          </div>
        </div>
        <div className="settings-architecture-grid">
          <div className="architecture-flow">
            <div>Frontend</div>
            <div>FastAPI API Layer</div>
            <div>Scanner Agent</div>
            <div>AMD MI300X + ROCm + vLLM</div>
            <div>Qwen2.5-VL</div>
            <div>Structured Defect JSON</div>
            <div>SQLite + MindsDB</div>
            <div>Reporter Agent</div>
            <div>Factory Operations Report</div>
          </div>
          <div className="system-status-stack">
            <div className="system-status-card">
              <span>API</span>
              <strong>{serviceStatus.health === "ok" ? "Reachable" : "Unavailable"}</strong>
            </div>
            <div className="system-status-card">
              <span>Inference</span>
              <strong>{runtimeStatus.label}</strong>
            </div>
            <div className="system-status-card">
              <span>System data</span>
              <strong>{dataStatus.label}</strong>
            </div>
            <div className="system-status-card">
              <span>MindsDB</span>
              <strong>Optional</strong>
            </div>
          </div>
        </div>
        <div className="sponsor-grid">
          <MetricCard label="AMD" value="GPU compute + ROCm runtime" />
          <MetricCard label="Qwen" value="Multimodal defect reasoning" />
          <MetricCard label="HuggingFace" value="Model hub + demo distribution" />
          <MetricCard label="MindsDB" value="Operations analytics + reporting" />
          <MetricCard label="MVTec AD" value="Industrial defect benchmark dataset" />
        </div>
      </article>
    </div>
  );
}
