import EventLogTable from "../components/EventLogTable";
import MetricCard from "../components/MetricCard";
import OperationsAlertCard from "../components/OperationsAlertCard";
import { InspectionTimeline, SeverityDistribution } from "../components/QualityChart";
import ShiftReportCard from "../components/ShiftReportCard";
import StatusBadge from "../components/StatusBadge";
import SystemBanner from "../components/SystemBanner";
import { useAppContext } from "../state/AppContext";
import {
  formatDecisionLabel,
  getDataStatus,
  getRuntimeStatus,
} from "../lib/ui";

function deriveTrend(events) {
  const defects = events.filter((event) => event.defect_detected);
  const commonDefect = defects[0]?.defect_category || defects[0]?.defect_type || "No recurring defect yet";
  const commonCause = defects.find((event) => event.possible_causes?.length)?.possible_causes?.[0] || "No recurring likely cause yet";
  const recommendation = defects.find((event) => event.recommended_fix?.length)?.recommended_fix?.[0] || "Continue monitoring inspections";
  return { commonDefect, commonCause, recommendation };
}

export default function ReportsPage() {
  const {
    events,
    metrics,
    report,
    operationsAlert,
    health,
    frontendDemoMode,
    loading,
    error,
    serviceStatus,
    refreshSystemData,
  } = useAppContext();
  const trend = deriveTrend(events);
  const runtimeStatus = getRuntimeStatus({ health, metrics, frontendDemoMode, loading });
  const dataStatus = getDataStatus({ serviceStatus, loading });
  const latest = events?.[0] || null;
  const reportWindow = `${events.length} recent events`;

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
        <p className="eyebrow">Reports and operations review</p>
        <h1 className="page-title">Shift-level reporting, recurring causes, and the next operational move.</h1>
        <div className="page-heading-meta">
          <StatusBadge tone={dataStatus.tone}>{reportWindow}</StatusBadge>
          <StatusBadge tone={runtimeStatus.tone}>{runtimeStatus.badge}</StatusBadge>
          {latest ? <StatusBadge tone="info">Latest decision: {formatDecisionLabel(latest.action)}</StatusBadge> : null}
        </div>
      </div>

      <section className="reports-summary-grid">
        <article className="hero-panel hero-panel-soft reports-intro-panel">
          <p className="eyebrow">Reporting window</p>
          <h2>This is where item decisions become plant-level review.</h2>
          <p className="report-text">
            Use this page to review the current event window, confirm recurring defect signals,
            and brief shift leads on what changed and what to do next.
          </p>
        </article>
        <div className="reports-insight-grid">
          <article className="content-card report-insight-card">
            <p className="eyebrow">Defect trend</p>
            <h3>{trend.commonDefect}</h3>
            <p className="report-text">Most common issue in the current event window</p>
          </article>
          <article className="content-card report-insight-card">
            <p className="eyebrow">Likely process driver</p>
            <h3>{trend.commonCause}</h3>
            <p className="report-text">Most recurring process signal</p>
          </article>
          <article className="content-card report-insight-card report-insight-card-action">
            <p className="eyebrow">Recommended next step</p>
            <h3>{trend.recommendation}</h3>
            <p className="report-text">Action guidance for the next shift decision</p>
          </article>
          <MetricCard label="Average Latency" value={`${Math.round(Number(metrics?.avg_latency_ms || 0))}ms`} meta="Current inference average" />
        </div>
      </section>

      <section className="reports-story-grid">
        <ShiftReportCard report={report} featured />
        <OperationsAlertCard alert={operationsAlert} />
      </section>

      <section className="reports-recommendation-grid reports-recommendation-grid-compact">
        <article className="content-card dashboard-story-card dashboard-story-card-dark">
          <p className="eyebrow">Operator briefing</p>
          <h3>{latest ? formatDecisionLabel(latest.action) : "Awaiting first inspection"}</h3>
          <p className="report-text">
            Use this summary to explain the current shift posture without reading every event row.
          </p>
        </article>
        <article className="content-card">
          <p className="eyebrow">Coverage</p>
          <h3>{reportWindow}</h3>
          <p className="report-text">
            This report is based on the recent event stream available in the local runtime, not a historical warehouse export.
          </p>
        </article>
      </section>

      <section className="reports-story-grid">
        <SeverityDistribution events={events} />
        <InspectionTimeline events={events} />
      </section>

      <article className="content-card">
        <div className="card-heading-row">
          <div>
            <p className="eyebrow">Event log</p>
            <h3>Current reporting window</h3>
          </div>
        </div>
        <EventLogTable events={events} />
      </article>
    </div>
  );
}
