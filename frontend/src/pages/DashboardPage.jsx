import EventLogTable from "../components/EventLogTable";
import MetricCard from "../components/MetricCard";
import OperationsAlertCard from "../components/OperationsAlertCard";
import { InspectionTimeline, SeverityDistribution } from "../components/QualityChart";
import RuntimePanel from "../components/RuntimePanel";
import ShiftReportCard from "../components/ShiftReportCard";
import StatusBadge from "../components/StatusBadge";
import SystemBanner from "../components/SystemBanner";
import { useAppContext } from "../state/AppContext";
import {
  formatConfidence,
  formatDecisionLabel,
  getDataStatus,
  getRuntimeStatus,
} from "../lib/ui";

function formatNumber(value) {
  return new Intl.NumberFormat("en-US").format(Number(value || 0));
}

function riskCopy(latest, metrics) {
  if (!latest && Number(metrics?.total_inspected || 0) === 0) {
    return {
      tone: "neutral",
      label: "Awaiting first inspection",
      headline: "No quality decision has been logged yet.",
      body: "Run the first inspection to establish live line posture, evidence, and shift reporting.",
      action: "Run first inspection",
    };
  }
  if (latest?.action === "STOP_LINE" || String(latest?.severity).toLowerCase() === "critical") {
    return {
      tone: "critical",
      label: "Current plant action",
      headline: "Stop line and contain the affected batch.",
      body: "The latest inspection escalated to a stop-line decision. Hold the item, inspect nearby units, and verify the upstream process before restart.",
      action: "Contain batch",
    };
  }
  if (latest?.action === "ALERT_OPERATOR" || String(latest?.severity).toLowerCase() === "warning") {
    return {
      tone: "warning",
      label: "Current plant action",
      headline: "Manual review is active for the latest item.",
      body: "The latest frame did not qualify for silent release. Keep the line moving, but route this item and similar units to operator review.",
      action: "Review held item",
    };
  }
  return {
    tone: "ok",
    label: "Current line posture",
    headline: "Release decisions are stable.",
    body: "Recent inspections are clearing the release threshold and no intervention is currently recommended.",
    action: "Continue production",
  };
}

function latestEvent(events) {
  return events?.[0] || null;
}

export default function DashboardPage() {
  const {
    metrics,
    events,
    report,
    operationsAlert,
    health,
    frontendDemoMode,
    loading,
    error,
    serviceStatus,
    refreshSystemData,
  } = useAppContext();
  const latest = latestEvent(events);
  const risk = riskCopy(latest, metrics);
  const defectRate = Math.round(Number(metrics?.defect_rate || 0));
  const latestLatency = Math.round(Number(metrics?.latest_latency_ms || 0));
  const avgLatency = Math.round(Number(metrics?.avg_latency_ms || 0));
  const runtimeStatus = getRuntimeStatus({ health, metrics, frontendDemoMode, loading });
  const dataStatus = getDataStatus({ serviceStatus, loading });
  const latestAction = latest ? formatDecisionLabel(latest.action) : "Awaiting first inspection";
  const lineLabel = latest?.line_id || "Configured line";
  const currentDecisionTone = risk.tone === "neutral" ? "info" : risk.tone;

  return (
    <div className="page-shell dashboard-page-shell">
      {(error || runtimeStatus.id !== "live") ? (
        <SystemBanner
          tone={error ? dataStatus.tone : runtimeStatus.tone}
          title={error ? dataStatus.badge : runtimeStatus.badge}
          body={error || runtimeStatus.description}
          actionLabel="Refresh status"
          onAction={() => refreshSystemData()}
        />
      ) : null}
      <section className={`dashboard-hero-v2 dashboard-hero-${risk.tone}`}>
        <div className="dashboard-hero-copy">
          <div className="dashboard-kicker-row">
            <p className="eyebrow">Factory Quality Command Center</p>
            <StatusBadge tone={currentDecisionTone}>
              {risk.label}: {risk.action}
            </StatusBadge>
          </div>
          <h1>{risk.headline}</h1>
          <p>{risk.body}</p>
          <div className="dashboard-hero-actions">
            <a className="button button-primary" href="/inspection">Run inspection</a>
            <a className="button button-secondary button-secondary-dark" href="/reports">View reports</a>
          </div>
        </div>

        <div className="dashboard-hero-console" aria-label="Live quality summary">
          <div className="console-topline">
            <span>{lineLabel}</span>
            <span>Latest decision: {latestAction}</span>
          </div>
          <div className="console-risk-number">
            <strong>{defectRate}%</strong>
            <span>current defect rate window</span>
          </div>
          <div className="console-status-grid">
            <div>
              <span>Total inspected</span>
              <strong>{formatNumber(metrics?.total_inspected)}</strong>
            </div>
            <div>
              <span>Defects found</span>
              <strong>{formatNumber(metrics?.defects_found)}</strong>
            </div>
            <div>
              <span>Review / stop events</span>
              <strong>{formatNumber(Number(metrics?.critical_events || 0) + Number(metrics?.defects_found || 0))}</strong>
            </div>
            <div>
              <span>Inference state</span>
              <strong>{runtimeStatus.label}</strong>
            </div>
          </div>
        </div>
      </section>

      <section className="dashboard-metric-bento">
        <MetricCard label="Current decision" value={latestAction} meta="Most recent logged item outcome" />
        <MetricCard label="Latest Latency" value={`${latestLatency}ms`} meta="Most recent Qwen-VL call" />
        <MetricCard label="Average Latency" value={`${avgLatency}ms`} meta="Current live inference average" />
        <MetricCard label="Throughput" value={`${formatNumber(metrics?.estimated_images_per_min)}/min`} meta="Estimated frames processed per minute" />
      </section>

      <section className="dashboard-main-v2">
        <div className="dashboard-left-stack">
          <OperationsAlertCard alert={operationsAlert} />
          <article className="content-card dashboard-event-card">
            <div className="card-heading-row">
              <div>
                <p className="eyebrow">Recent inspection stream</p>
                <h3>Latest logged quality events</h3>
              </div>
              {latest ? (
                <StatusBadge tone={String(latest.severity).toLowerCase() === "critical" ? "critical" : String(latest.severity).toLowerCase() === "warning" ? "warning" : "ok"}>
                  Latest: {formatDecisionLabel(latest.action)}
                </StatusBadge>
              ) : null}
            </div>
            <EventLogTable events={events.slice(0, 6)} compact />
          </article>
        </div>

        <aside className="dashboard-right-rail-v2">
          <article className="content-card dashboard-latest-card">
            <p className="eyebrow">Latest item outcome</p>
            <h3>{latestAction}</h3>
            <dl>
              <div>
                <dt>Finding</dt>
                <dd>{latest?.defect_category || latest?.defect_type || "No confirmed defect"}</dd>
              </div>
              <div>
                <dt>Severity</dt>
                <dd>{latest ? latest.severity || "ok" : "No event"}</dd>
              </div>
              <div>
                <dt>Decision confidence</dt>
                <dd>{latest ? formatConfidence(latest.confidence) : "N/A"}</dd>
              </div>
              <div>
                <dt>Latency</dt>
                <dd>{latest?.processing_ms || latestLatency}ms</dd>
              </div>
            </dl>
          </article>

          <article className="content-card dashboard-operator-card">
            <p className="eyebrow">Recommended next step</p>
            <h3>{risk.action}</h3>
            <p className="report-text">
              {risk.tone === "critical"
                ? "Contain the affected batch, inspect adjacent items, and verify process settings before restart."
                : risk.tone === "warning"
                  ? "Keep the line moving while routing warning-level images to operator review."
                  : risk.tone === "neutral"
                    ? "Run the first inspection to establish event history and reporting context."
                    : "Maintain line speed and continue monitoring runtime metrics."}
            </p>
          </article>
        </aside>
      </section>

      <section className="dashboard-analytics-v2">
        <SeverityDistribution events={events} />
        <InspectionTimeline events={events} />
        <ShiftReportCard report={report} compact />
      </section>

      <section className="dashboard-runtime-v2">
        <div className="section-copy">
          <p className="eyebrow">AMD runtime visibility</p>
          <h2>Inference performance stays visible beside quality decisions.</h2>
        </div>
        <RuntimePanel
          metrics={metrics}
          health={health}
          frontendDemoMode={frontendDemoMode}
          loading={loading}
        />
      </section>
    </div>
  );
}
